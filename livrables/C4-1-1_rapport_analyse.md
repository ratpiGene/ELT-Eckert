# C4.1.1 — Rapport d'analyse de l'environnement du projet

> **Compétence visée.** Analyser l'environnement du projet en identifiant les besoins,
> les enjeux, l'environnement technique et les contraintes (coût, délais, complexité),
> ainsi que l'état de l'existant, afin de cadrer la conception de l'infrastructure de données.

> **Périmètre et honnêteté.** Ce dossier présente une **plateforme reconstruite** sur un
> **contexte métier réel** — l'obligation loi Eckert vécue en alternance chez Prévifrance
> (site d'Agen, poste de chargé d'étude Data / AMOA). Ce n'est pas le système d'information
> de l'entreprise. Aucune donnée d'entreprise ni donnée personnelle réelle d'adhérent
> n'entre dans le dépôt : le fichier des décès est la vraie donnée publique de l'INSEE, le
> référentiel adhérents est **synthétique** (Faker). Cette distinction est rappelée à l'oral
> dès la deuxième diapositive.

---

## 1. Le besoin métier

### 1.1 L'obligation légale

Une mutuelle santé et prévoyance doit identifier ses adhérents décédés pour traiter les
**contrats en déshérence** — des contrats dont le souscripteur est décédé sans que les
capitaux aient été versés aux ayants droit. C'est une **obligation légale** issue de la
**loi Eckert (loi n° 2014-617 du 13 juin 2014)**, entrée en vigueur au 1er janvier 2016,
qui impose aux organismes assureurs :

- de **rechercher activement** les assurés décédés et les bénéficiaires des contrats ;
- de **recenser annuellement** les contrats non réglés et d'en publier le nombre et l'encours ;
- de **reverser à la Caisse des dépôts** les capitaux non réclamés au terme d'un délai.

Le manquement expose à un **contrôle et à des sanctions de l'ACPR** (Autorité de contrôle
prudentiel et de résolution) et, au-delà du risque juridique, à un **enjeu de confiance** :
un capital non versé à un ayant droit est une promesse d'assurance non tenue.

### 1.2 Le besoin fonctionnel dérivé

Traduit en besoin de données, l'obligation se décompose ainsi :

| # | Besoin | Traduction technique |
|---|---|---|
| B1 | Disposer d'une source de vérité des décès | Ingérer le **fichier des personnes décédées de l'INSEE** (data.gouv.fr) |
| B2 | Rapprocher les décès du portefeuille d'adhérents | **Rapprochement** décès × référentiel sur des clés d'identité |
| B3 | Produire une liste de contrats à instruire, priorisée | Table `gold` avec **niveau de confiance** et ancienneté du décès |
| B4 | Garantir la fiabilité de la donnée entrante | **Validation de contrat de données** sur le fichier reçu |
| B5 | Tracer et superviser un traitement à valeur réglementaire | **Journal d'exécution**, alertes, indicateurs qualité |
| B6 | Rejouer et auditer le traitement | Exécutions **horodatées**, données **versionnées** (bronze immuable) |

Le besoin n'est pas décisionnel (produire un rapport) mais **opérationnel** : produire une
donnée actionnable, fiable et traçable, sur un rythme mensuel aligné sur la publication INSEE.

---

## 2. Les enjeux du projet

| Enjeu | Nature | Conséquence sur la conception |
|---|---|---|
| **Conformité réglementaire** | Juridique / réputationnel | Traçabilité, reproductibilité, preuve d'exécution non négociables |
| **Fiabilité de la détection** | Métier | Un faux négatif = un ayant droit lésé ; un faux positif = une instruction inutile → **niveaux de confiance** plutôt qu'un booléen |
| **Résilience aux sources externes** | Technique | La source INSEE n'est pas maîtrisée → validation par le **contenu**, pas par les métadonnées déclarées (cf. incident C4.4.2) |
| **Protection des données** | RGPD | Données de santé et d'identité → cloisonnement des couches, moindre privilège, aucune donnée réelle hors périmètre |
| **Soutenabilité d'exploitation** | Organisationnel | Un traitement réglementaire mensuel doit tenir sans expert dédié → supervision et runbook |

L'enjeu structurant est le **troisième** : c'est lui qui a provoqué l'incident réel rejoué en
C4.4.2 et qui justifie l'architecture de validation retenue.

---

## 3. L'environnement du projet

### 3.1 Environnement organisationnel (vécu Prévifrance)

- **Poste** : chargé d'étude Data / AMOA, au sein d'une équipe décisionnelle.
- **Gouvernance contraignante** : un **DBA en position de *gatekeeper*** sur les accès et les
  objets de base ; les arbitrages de charge et de priorité passaient par **Jira**.
- **Cycle avant production** : contrôles de cohérence manuels (volumétries, totaux,
  recoupement avec l'existant) puis **revue SQL par le DBA**. **Aucun cahier de recette
  formalisé** — précisément ce que le Bloc 4 demande de produire.
- **Supervision réelle** : jobs SQL Server Agent et logs SSRS **consultés à la main**, sans
  alerting outillé.

### 3.2 Environnement technique d'origine (vécu Prévifrance)

| Composant | Existant réel |
|---|---|
| Entrepôt | **SQL Server** (bases `DWH_AI`, `DWH_DSN_PREVI`, `FRUP00`) |
| Traitements | **T-SQL**, procédures stockées |
| Restitution | Rapports **SSRS** |
| Orchestration | **Airflow** (un traitement de collecte Eckert mis en production) |
| Ordonnancement historique | **SQL Server Agent** |
| Absents de l'environnement d'origine | **Aucun Spark, aucun CI/CD, aucun alerting outillé** |

### 3.3 Environnement de la plateforme reconstruite

Environnement **100 % local, conteneurisé sous Docker Compose**, sans aucun service managé
ni facturé (justification en §4.1) : Airflow (orchestration), PostgreSQL (entrepôt), MinIO
(stockage objet), Apache Spark (calcul distribué), GitHub Actions (CI/CD). Le détail des
choix et de leur justification fait l'objet du livrable **C4.1.2**.

---

## 4. Les contraintes

### 4.1 Contrainte de coût

- **Contrainte imposée** : aucun budget d'infrastructure, pas de compte cloud à provisionner,
  pas de carte bancaire, pas de quota à négocier.
- **Conséquence** : tout tourne en local sous Docker Compose ; coût logiciel **nul** (briques
  open source), coût d'infrastructure = un poste existant. Le seul coût réel est le **temps
  humain** de construction et d'exploitation.
- Une **estimation de coût à trois scénarios** (local / cloud managé Azure / SaaS type
  Snowflake-Fabric), avec hypothèses de volumétrie explicites, est produite en **C4.1.2** —
  c'est un critère écrit de la compétence de sélection des composants.

### 4.2 Contrainte de délai

- **Moins d'un mois** de bout en bout, découpé en deux temps : **construction** puis
  **rédaction et répétition**.
- **Règle de coupe assumée** : toute brique qui ne tourne pas en fin de phase de construction
  bascule dans `LIMITES.md` comme évolution consciente, plutôt que d'être bâclée. Le jury
  valorise une limite lucide, pas une brique survendue.
- **Conséquence de conception** : chaque brique doit pouvoir **produire une capture d'écran en
  moins de cinq minutes**. Un composant non démontrable ne sert pas la démonstration.

### 4.3 Contrainte de complexité

- **Volumétrie** : le fichier des décès cumulé se compte en **dizaines de millions de lignes**
  (fichiers annuels historiques + mise à jour mensuelle). C'est cette volumétrie qui **justifie
  le recours au calcul distribué** (Spark) — par la donnée, pas par la grille d'évaluation.
- **Source non maîtrisée** : le contrat de données du fichier INSEE peut changer **sans
  préavis** (format à largeur fixe, métadonnées déclaratives). La complexité est reportée sur
  la **robustesse de la validation**, pas sur le format.
- **Rapprochement sans identifiant pivot** : aucun identifiant national (NIR) dans le
  périmètre → rapprochement **probabiliste** sur nom + prénom + date de naissance, d'où la
  nécessité de **niveaux de confiance** gradués.

---

## 5. État de l'existant et écart à combler

### 5.1 Ce qui existait (vécu Prévifrance)

- Un traitement de **collecte Eckert orchestré sous Airflow, en production**.
- Une chaîne décisionnelle SQL Server mûre (T-SQL, SSRS).
- Une **étude d'architecture cible Snowflake / Airflow** menée en année 2 : **maquettée,
  testée, non retenue** — matériau direct pour l'arbitrage de C4.1.2.
- Des contrôles de cohérence **manuels** et une revue DBA, mais **non consignés**.

### 5.2 Ce qui manquait — les quatre trous

Ce sont les compétences **sans matériau d'origine**, ciblées en priorité par la
reconstruction :

| Trou | Existant d'origine | À construire |
|---|---|---|
| **Calcul distribué (C4.2.2)** | Aucun Spark | Job PySpark de rapprochement décès × référentiel |
| **CI/CD (C4.2.3)** | Déploiement 100 % manuel | Workflow GitHub Actions (lint, tests, sécurité, build) |
| **Alerting (C4.3.1)** | Logs consultés à la main | Callbacks d'échec, SLA, notification, indicateurs |
| **Tests de sécurité (C4.4.1)** | Contrôles + revue DBA non consignés | Cahier de recette écrit, test de droits, non-exposition de secrets, scan de dépendances |

### 5.3 Distinction étudié / maquetté / en production

| Statut | Vécu Prévifrance | Plateforme reconstruite |
|---|---|---|
| **En production** | Collecte Eckert sous Airflow ; chaîne SQL Server / SSRS | — |
| **Maquetté puis abandonné** | Architecture Snowflake / Airflow (année 2) | — |
| **Reconstruit et démontré** | — | Ingestion, validation par contenu, entrepôt multi-couches, orchestration, distribué, CI/CD, supervision, tests |

---

## 6. Synthèse : de l'analyse à la conception

L'analyse cadre trois décisions de conception, reprises et justifiées dans les livrables suivants :

1. **Une plateforme locale conteneurisée** (contrainte de coût et de délai) → C4.1.2.
2. **Une validation par le contenu et une architecture multi-couches** (enjeu de résilience et
   de conformité) → C4.2.1 et C4.4.2.
3. **Un calcul distribué justifié par la volumétrie réelle** (contrainte de complexité) → C4.2.2.

---

## 7. Couverture des critères de la compétence C4.1.1

| Critère de la grille | Section qui le couvre | Preuve associée |
|---|---|---|
| Identifier les **besoins** | §1 (B1→B6) | `livrables/C4-1-1` §1.2 |
| Identifier les **enjeux du projet** | §2 | `livrables/C4-1-1` §2 |
| Décrire l'**environnement** | §3 (organisationnel, technique, reconstruit) | `docs/`, `infra/docker-compose.yml` |
| Identifier les **contraintes de coût** | §4.1 | Chiffrage détaillé en `C4-1-2` §5 |
| Identifier les **contraintes de délai** | §4.2 | Rétroplanning `CLAUDE.md` §9 |
| Identifier les **contraintes de complexité** | §4.3 | Volumétrie citée à l'ingestion (`preuves/`) |
| Établir l'**état de l'existant** | §5 | `docs/incident_metadonnees.md`, `LIMITES.md` |
| Cadrer la **conception** à partir de l'analyse | §6 | Renvois vers `C4-1-2`, `C4-2-1`, `C4-2-2` |
