# C4.2.2 — Conception et réalisation des pipelines de données

> **Compétence visée.** Concevoir et réaliser des pipelines de données selon **trois méthodes**
> distinctes — traitement **au fil de l'eau** (Python/SQL), **orchestration** (Airflow) et
> **calculs distribués** (Spark) — chacune produisant une donnée attendue.

> **Point de rupture de la grille.** Les trois méthodes doivent être présentes et démontrées, la
> distribuée en particulier. Ce livrable les décrit et renvoie à leur preuve d'exécution.

---

## 1. Vue d'ensemble de la chaîne

```
data.gouv / fichier de démonstration
        │
        ▼
[Ingestion + validation de contenu]  ──►  bronze.deces_brut
        │  (Python, COPY)
        ▼
[Promotion fil de l'eau — SQL]  ──►  silver.deces        ┐
                                                          │  jointure sur clé
référentiel synthétique ──► silver.adherent/contrat ─────┘  de rapprochement
        │
        ▼
[Rapprochement distribué — Spark]  ──►  gold.contrat_desherence
        │
        ▼
[Restitution]  ──►  gold.v_contrats_a_instruire
```

Les trois méthodes couvrent trois régimes différents : le **SQL au fil de l'eau** transforme la
donnée à l'arrivée, l'**orchestrateur** enchaîne et fiabilise les étapes, le **distribué**
absorbe le volume du rapprochement.

---

## 2. Méthode 1 — Traitement au fil de l'eau (Python + SQL)

**Donnée produite : `silver.deces`** (décès typés, nettoyés, dédoublonnés).

À l'arrivée d'un fichier, deux traitements légers s'enchaînent sans faire transiter la donnée
par une couche applicative lourde :

- **Chargement bronze** (`src/eckert/transform/charge_bronze.py`) : la ligne brute est insérée
  par `COPY … FROM STDIN`, avec sa provenance (fichier, numéro de ligne, `run_id`). Le `COPY`
  est choisi pour le débit (chargement en masse plutôt qu'`INSERT` ligne à ligne).
- **Promotion silver** (`src/eckert/transform/bronze_vers_silver.py`) : le découpage largeur
  fixe, le typage des dates, le calcul de la clé de rapprochement et la **déduplication**
  (`DISTINCT ON` sur une clé naturelle) sont **poussés dans PostgreSQL**. La transformation
  s'exécute au plus près de la donnée, en une requête ensembliste.

> Extrait — la logique de nettoyage vit dans le moteur, pas dans l'application :
> ```sql
> INSERT INTO silver.deces (...)
> SELECT DISTINCT ON (cle_naturelle) ...,
>   regexp_replace(upper(unaccent(nom)), '[^A-Z]', '', 'g') || '|' || ... AS cle_rapprochement
> FROM bronze.deces_brut
> WHERE run_id = %(run_id)s AND length(ligne_source) >= 176
> ORDER BY cle_naturelle ON CONFLICT DO NOTHING;
> ```

**Nommage assumé** : c'est un traitement *au fil de l'eau* déclenché à l'arrivée d'un fichier,
**pas du streaming permanent** (Kafka). La source est publiée mensuellement : un flux continu
n'aurait aucun sens métier (choix argumenté, `LIMITES.md`).

**Preuve** : `preuves/C4-2-2_bronze_silver.txt` (compteurs bronze → silver).

---

## 3. Méthode 2 — Orchestration (Apache Airflow)

**Donnée produite : le fichier validé en bronze/silver, avec traçabilité et alertes.**

Le DAG `eckert_ingestion_deces` (`dags/eckert_ingestion.py`) enchaîne quatre tâches :

```
recuperer_catalogue ─► telecharger_et_valider ─► charger_bronze ─► promouvoir_silver
```

Ce que l'orchestrateur apporte, et qu'un script isolé n'a pas :

| Apport | Mise en œuvre |
|---|---|
| **Planification** | `schedule="0 4 5 * *"` — le 5 de chaque mois à 4 h (rythme INSEE) |
| **Reprise sur erreur** | `retries=3`, `retry_exponential_backoff=True` |
| **Garde-fou de durée** | `execution_timeout=2 h`, `sla=30 min` sur l'étape sensible |
| **Supervision** | `on_failure_callback` (alerte) et `sla_miss_callback` (escalade) — cf. C4.3.1 |
| **Idempotence** | `max_active_runs=1`, `catchup=False` |

C'est aussi **la brique héritée du vécu Prévifrance** (le traitement Eckert réel était orchestré
sous Airflow), reconstruite ici proprement.

**Preuve** : `preuves/C4-2-2_airflow_dag.png` (graphe du DAG), `preuves/C4-2-2_airflow_run.png`
(exécution verte).

---

## 4. Méthode 3 — Calculs distribués (Apache Spark / PySpark)

**Donnée produite : `gold.contrat_desherence`** (contrats en déshérence, à trois niveaux de
confiance).

Le job `src/eckert/spark/rapprochement.py` s'exécute sur le **cluster Spark standalone**
(`spark://spark-master:7077`, un master + un worker), lit `silver` par JDBC, réalise le
rapprochement, et écrit le résultat en `gold` par JDBC.

### 4.1 Pourquoi le distribué ici

Le fichier des décès **cumulé** se compte en **dizaines de millions de lignes**. Le
rapprochement croise ce volume avec le portefeuille d'adhérents. Le distribué est justifié
**par la donnée** : partitionnement de la jointure, montée en charge horizontale, maîtrise de
la **fenêtre de traitement**. Sur le seul volume mensuel, un PostgreSQL indexé suffirait — c'est
assumé et argumenté à l'oral (question de jury).

### 4.2 La logique de rapprochement — trois niveaux de confiance

Faute d'identifiant national dans le périmètre, le rapprochement est **probabiliste**, d'où la
graduation :

| Niveau | Règle | Interprétation métier |
|---|---|---|
| **CERTAIN** | clé exacte (nom + prénom + naissance) **+ sexe + lieu de naissance concordants** | instruction directe |
| **PROBABLE** | clé exacte seule | à confirmer |
| **A_VERIFIER** | même nom + même date de naissance, **prénom différent** (homonymie) | levée humaine nécessaire |

> Extrait — la ligne qui gradue la confiance :
> ```python
> F.when(
>     (F.col("d.sexe") == F.col("a.sexe"))
>     & (F.col("d.code_lieu_naissance") == F.col("a.code_insee_naiss")),
>     F.lit("CERTAIN"),
> ).otherwise(F.lit("PROBABLE"))
> ```

### 4.3 Résultat d'exécution (démonstration)

Exécution sur le cluster, `run_id=demo_local_001`, référentiel de 20 000 adhérents :

```
Rapprochement demo_local_001 — 4162 contrats potentiellement en déshérence
  CERTAIN     : 2846   (88,1 M€ de capital)
  PROBABLE    : 1259   (38,4 M€)
  A_VERIFIER  :   57   ( 2,0 M€)
```

**Preuve** : `preuves/C4-2-2_spark_execution.txt` (sortie du job),
`preuves/C4-2-2_spark_ui.png` (Spark UI, application enregistrée sur le master),
`preuves/C4-2-2_gold_par_confiance.txt` (agrégat en base).

---

## 5. Note d'honnêteté sur les données de démonstration

Le **vrai** fichier INSEE sert à démontrer l'ingestion, la validation par le contenu et la
volumétrie. Ses identités ne recoupent cependant pas le référentiel **synthétique** : pour que
le rapprochement produise un résultat exploitable en soutenance, un fichier décès de
démonstration au format INSEE est généré avec un **recouvrement contrôlé** du référentiel
(`src/eckert/referentiel/scenario_deces.py`). Ce jeu est **clairement identifié comme
synthétique** ; aucune donnée réelle n'y figure.

---

## 6. Couverture des critères de la compétence C4.2.2

| Critère de la grille | Méthode / section | Preuve |
|---|---|---|
| Pipeline **temps réel (Python/SQL)** produisant une donnée | §2 → `silver.deces` | `preuves/C4-2-2_bronze_silver.txt` |
| Pipeline **orchestré** produisant une donnée | §3 → DAG Airflow | `preuves/C4-2-2_airflow_run.png` |
| Pipeline **distribué** produisant une donnée | §4 → `gold.contrat_desherence` | `preuves/C4-2-2_spark_execution.txt` |
| Justification du recours au **distribué** | §4.1 | volumétrie réelle citée |
| Chaque méthode produit une **donnée demandée** | §2/§3/§4 | tables bronze/silver/gold |
