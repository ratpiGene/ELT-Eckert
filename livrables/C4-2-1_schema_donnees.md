# C4.2.1 — Conception de l'entrepôt de données

> **Compétence visée.** Concevoir la structure de l'entrepôt de données (type de données,
> modalités d'accès, organisation) en justifiant les choix au regard de la **rapidité**, de la
> **sécurité** et de l'**accessibilité**.

---

## 1. Type de données à héberger

| Donnée | Nature | Volumétrie (démonstration) | Origine |
|---|---|---|---|
| Décès bruts | Texte largeur fixe (176 car.) | dizaines de M de lignes (cumulé réel) | INSEE / data.gouv |
| Décès typés | Relationnel typé (dates, codes) | idem après nettoyage | dérivé |
| Adhérents | Relationnel | 20 000 (paramétrable) | **synthétique (Faker)** |
| Contrats | Relationnel | ~ 27 000 | **synthétique (Faker)** |
| Contrats en déshérence | Relationnel + indicateurs | ~ 4 000 (démo) | produit par le rapprochement |
| Journal / qualité | Relationnel horodaté | 1 ligne / étape / exécution | supervision |

L'entrepôt est **relationnel** (PostgreSQL) : la donnée est structurée, les jointures sont au
cœur du besoin (rapprochement), et les contrôles d'intégrité (clés, types, contraintes) portent
une part de la qualité. Le brut est conservé **tel quel** en texte pour la traçabilité et la
rejouabilité.

---

## 2. Organisation : quatre couches

L'entrepôt est organisé en **schémas par couche**, du plus brut au plus exposé. C'est la
colonne vertébrale de la sécurité (§4) et de la qualité.

```
bronze  ── image fidèle de la source, aucune transformation, tracée
   │        (bronze.deces_brut : ligne_source, fichier_source, ligne_numero, run_id, ingere_le)
   ▼
silver  ── données typées, nettoyées, dédoublonnées, conformes au contrat
   │        (silver.deces, silver.adherent, silver.contrat)
   ▼
gold    ── données exposées au métier : rapprochements et indicateurs
   │        (gold.contrat_desherence, vue gold.v_contrats_a_instruire)
   │
ops     ── journal d'exécution et contrôles qualité (transverse, supervision)
            (ops.journal_execution, ops.controle_qualite)
```

**Justification de l'organisation.** Séparer les couches, c'est séparer les responsabilités et
les droits : le brut n'est jamais exposé au métier, le nettoyage est isolé et rejouable, et la
restitution ne voit que le résultat validé. Chaque couche a un rôle unique et un niveau d'accès
unique.

---

## 3. Schéma détaillé et choix de conception

### 3.1 Bronze — fidélité et traçabilité

```sql
CREATE TABLE bronze.deces_brut (
    id             BIGSERIAL PRIMARY KEY,
    ligne_source   TEXT        NOT NULL,   -- la ligne INSEE telle que reçue
    fichier_source TEXT        NOT NULL,   -- provenance
    ligne_numero   INTEGER     NOT NULL,   -- position dans le fichier
    ingere_le      TIMESTAMPTZ NOT NULL DEFAULT now(),
    run_id         TEXT        NOT NULL    -- rattachement à une exécution
);
CREATE INDEX ix_deces_brut_run ON bronze.deces_brut (run_id);
```

Choix : **aucune interprétation** en bronze. On stocke la ligne brute + sa provenance. En cas
de doute sur une donnée gold, on remonte jusqu'à la ligne source exacte (`run_id`,
`ligne_numero`). L'index sur `run_id` sert la promotion incrémentale (une exécution à la fois).

### 3.2 Silver — typage, nettoyage, déduplication

`silver.deces` porte les champs typés (dates en `DATE`, sexe en `SMALLINT`) et une
**clé de rapprochement** normalisée. Le découpage largeur fixe, le typage et la déduplication
sont réalisés **en SQL, au plus près de la donnée** (cf. C4.2.2, méthode « fil de l'eau »).

La **clé de rapprochement** est le point de conception sensible : `nom | premier prénom | date
de naissance`, **normalisée à l'identique** côté SQL (`regexp_replace(upper(unaccent(...)),
'[^A-Z]','')`) et côté Python (`unicodedata` + filtrage alphabétique). Cette cohérence est ce
qui permet au rapprochement de fonctionner sur des noms accentués ou composés.

`silver.adherent` et `silver.contrat` (référentiel **synthétique**) sont reliés par une clé
étrangère `contrat.adherent_id → adherent.adherent_id`, qui garantit qu'aucun contrat n'est
orphelin.

### 3.3 Gold — le résultat métier

```sql
CREATE TABLE gold.contrat_desherence (
    contrat_id         BIGINT      NOT NULL,
    adherent_id        BIGINT      NOT NULL,
    nom, prenoms, date_naissance, date_deces …,
    jours_depuis_deces INTEGER     NOT NULL,
    niveau_confiance   TEXT        NOT NULL,   -- CERTAIN | PROBABLE | A_VERIFIER
    capital_garanti    NUMERIC(12,2),
    detecte_le         TIMESTAMPTZ NOT NULL DEFAULT now(),
    run_id             TEXT        NOT NULL,
    PRIMARY KEY (contrat_id, run_id)           -- une détection par contrat et par exécution
);
```

Choix : la clé primaire `(contrat_id, run_id)` autorise le **rejeu** d'une exécution sans écraser
l'historique des détections précédentes — essentiel pour un traitement à valeur réglementaire.
Le `niveau_confiance` matérialise le caractère **probabiliste** du rapprochement (pas
d'identifiant national) et évite le piège du booléen « décédé / pas décédé ».

### 3.4 Ops — supervision et qualité

`ops.journal_execution` (statut, lignes lues/rejetées, durée, message par étape) et
`ops.controle_qualite` (contrôle, résultat, valeur, seuil) alimentent le tableau de bord de
supervision (C4.3.1).

---

## 4. Modalités d'accès et sécurité

### 4.1 Deux rôles, principe du moindre privilège

| Rôle | Droit | Périmètre | Usage |
|---|---|---|---|
| `elt_writer` | SELECT/INSERT/UPDATE/DELETE + USAGE séquences | bronze, silver, gold, ops | le **pipeline** |
| `elt_reader` | SELECT **uniquement** | **gold seulement** | la **restitution métier** |

```sql
-- Lecture métier : gold seulement
GRANT USAGE ON SCHEMA gold TO elt_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA gold GRANT SELECT ON TABLES TO elt_reader;
-- Refus explicite des couches techniques
REVOKE ALL ON SCHEMA bronze, silver, ops FROM elt_reader;
```

**Ce cloisonnement est testé, pas seulement déclaré** (C4.4.1) :

- `elt_reader` qui tente un `INSERT` en gold → `InsufficientPrivilege` (test `SEC-02`) ;
- `elt_reader` qui tente un `SELECT` en bronze → `InsufficientPrivilege` (test `SEC-03`).

Les deux tests **passent contre la base réelle** (`tests/test_securite.py`, preuve
`preuves/C4-4-1_tests_securite.txt`).

### 4.2 Accessibilité métier : la vue de restitution

Le métier n'écrit jamais de SQL sur les tables techniques. Il consomme une **vue priorisée** :

```sql
CREATE VIEW gold.v_contrats_a_instruire AS
SELECT row_number() OVER (ORDER BY <CERTAIN d'abord>, jours_depuis_deces DESC,
                          capital_garanti DESC) AS priorite, …
FROM gold.contrat_desherence;
GRANT SELECT ON gold.v_contrats_a_instruire TO elt_reader;
```

La colonne `priorite` donne un **ordre d'instruction directement exploitable** : d'abord les
correspondances certaines, puis les décès les plus anciens (le délai Eckert court), puis les
plus gros capitaux. Une bascule vers un outil de restitution (Metabase) se brancherait sur
cette même vue, avec le rôle lecture seule.

### 4.3 Rapidité

- **Index** ciblés : `run_id` (bronze, promotion incrémentale), `cle_rapprochement`
  (silver.deces et silver.adherent, cœur de la jointure), `date_deces`, `niveau_confiance`.
- **Chargement par `COPY`** (et non `INSERT` ligne à ligne) pour l'entrée en bronze.
- **Transformations poussées dans le moteur** (SQL ensembliste) plutôt que dans l'application.
- Le rapprochement massif est déporté sur **Spark** quand la volumétrie le justifie (C4.2.2).

---

## 5. Preuves

| Élément | Preuve |
|---|---|
| Schémas, tables, rôles créés | `preuves/C4-2-1_schema_postgres.txt` (`\dn`, `\du`, `\dt`) |
| Cloisonnement testé | `preuves/C4-4-1_tests_securite.txt` (SEC-02, SEC-03 verts) |
| Vue de restitution lisible par le lecteur | `preuves/C4-2-1_vue_restitution.txt` |
| Résultats gold aux 3 niveaux | `preuves/C4-2-2_gold_par_confiance.txt` |

---

## 6. Couverture des critères de la compétence C4.2.1

| Critère de la grille | Section | Preuve |
|---|---|---|
| **Type de données** identifié et justifié | §1 | `src/sql/20_tables.sql` |
| **Organisation** de l'entrepôt | §2, §3 | `preuves/C4-2-1_schema_postgres.txt` |
| **Modalités d'accès** | §4.1, §4.2 | `src/sql/10_schemas.sql`, `30_vues_gold.sql` |
| Justification **rapidité** | §4.3 | index en `20_tables.sql` |
| Justification **sécurité** | §4.1 | tests `SEC-02/03` verts |
| Justification **accessibilité** | §4.2 | `preuves/C4-2-1_vue_restitution.txt` |
