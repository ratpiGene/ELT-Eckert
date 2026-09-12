# C4.1.2 — Sélection des composants et technologies de l'architecture

> **Compétence visée.** Sélectionner les composants et technologies de l'infrastructure de
> données en explicitant les avantages attendus, les points de vigilance (dont le
> **vendor lock-in**) et une **estimation des coûts**, afin de concevoir une architecture
> adaptée aux besoins et aux contraintes établis en C4.1.1.

---

## 1. Méthode de sélection

Chaque composant est retenu contre un besoin (B1→B6 de C4.1.1) et une contrainte (coût, délai,
complexité). Le fil directeur est **le principe de moindre dépendance** : ne rien ajouter au
périmètre qu'une compétence de la grille n'exige, et préférer une brique **open source,
locale, démontrable en moins de cinq minutes** à un service managé.

Une règle de conception a guidé les arbitrages : **rester portable**. Chaque choix local a été
retenu pour préparer une éventuelle bascule cloud **sans réécriture majeure** (S3-compatibilité,
SQL standard, orchestrateur portable).

---

## 2. Architecture cible

```
                    ┌─────────────── Airflow (orchestrateur) ───────────────┐
                    │                                                        │
data.gouv.fr        ▼                                                        │
fichier décès  ──►  Ingestion ──► MinIO (bronze, fichiers bruts + manifeste) │
   INSEE            (Python)          │                                      │
                                      ▼                                      │
                            Validation de contrat de données                 │
                            (schéma, largeurs, volumétrie, doublons)         │
                                      │                                      │
                    ┌─────────────────┴──────────────────┐                   │
                    ▼                                    ▼                   │
            Spark (batch distribué)              Python/SQL (fil de l'eau)    │
            rapprochement décès × contrats       typage, dédoublonnage        │
                    │                                    │                   │
                    └─────────────────┬──────────────────┘                   │
                                      ▼                                      │
                          PostgreSQL — entrepôt                              │
                          schémas : bronze / silver / gold / ops             │
                                      │                                      │
                                      ▼                                      │
                          Restitution : vues gold (+ Metabase, option)       │
                                                                             │
     Supervision : callbacks Airflow, SLA, alerting, journal qualité ────────┘
     CI/CD : GitHub Actions (lint, tests, sécurité, build image)
```

---

## 3. Composants retenus, avantages et points de vigilance

| Composant | Choix | Avantage attendu | Point de vigilance |
|---|---|---|---|
| **Orchestration** | Apache Airflow | Déjà pratiqué sur le traitement Eckert réel ; DAG lisible en soutenance ; **callbacks et SLA natifs** | Empreinte mémoire du Compose ; scheduler à surveiller |
| **Stockage brut** | MinIO (S3-compatible) | Sépare le brut du modélisé, **versionne** les fichiers reçus, prépare une bascule cloud sans réécriture | Pas de cycle de vie automatique en local |
| **Entrepôt** | PostgreSQL | **Rôles et droits** démontrables (sécurité), index et plans (rapidité), **schémas par couche** (organisation) | Ne scale pas horizontalement — assumé |
| **Distribué** | Apache Spark (PySpark) | Le fichier décès cumulé = dizaines de M de lignes : **le distribué est justifié par la donnée** | Coût de démarrage du cluster local ; ne pas sur-dimensionner |
| **Fil de l'eau** | Python + SQL déclenché à l'arrivée d'un fichier | Répond au « pipeline temps réel (SQL, Python) » **sans monter un Kafka** | Bien nommer : traitement au fil de l'eau, pas streaming |
| **CI/CD** | GitHub Actions | Gratuit, exécutions **horodatées et exportables** en preuve | Runners publics : aucun secret réel dans le dépôt |
| **Supervision** | Airflow (callbacks, SLA) + journal qualité `ops` | Légèreté assumée sur le délai disponible | Pas de métrique d'infra — noté en `LIMITES.md` |
| **Restitution** | Vues `gold` (+ Metabase optionnel) | Montre l'**accessibilité** pour le métier | Optionnel si le temps manque |

### 3.1 Justification des choix structurants

- **PostgreSQL plutôt qu'un moteur analytique dédié** : le besoin est opérationnel et
  transactionnel (charger, rapprocher, tracer), pas OLAP massif. Postgres couvre les trois
  qualités attendues d'un entrepôt — **rapidité** (index, plans), **sécurité** (rôles,
  schémas), **organisation** (couches) — avec un coût d'exploitation nul et une portabilité SQL.
- **Spark justifié par la donnée, pas par la grille** : sur le **seul volume mensuel**, un
  Postgres bien indexé suffirait — et nous l'assumons à l'oral. C'est la **volumétrie cumulée**
  (historique + fenêtre de traitement) et la **trajectoire de croissance** qui rendent le
  distribué pertinent. Point de vigilance honnête traité en question de jury.
- **MinIO comme couche bronze** : découple l'ingestion du modèle, **versionne** chaque fichier
  reçu (rejouabilité de l'incident), et expose une API S3 identique à un stockage objet cloud.

---

## 4. Vendor lock-in

Le lock-in est traité **par construction** : chaque brique est soit open source, soit
substituable par une interface standard.

| Brique | Dépendance | Substituabilité | Risque de lock-in |
|---|---|---|---|
| MinIO | API **S3** | → AWS S3, Azure Blob (via passerelle), GCS | **Faible** — API standard |
| PostgreSQL | **SQL standard** | → Azure SQL, Aurora, Cloud SQL | **Faible** — SQL portable |
| Airflow | DAG Python | → Cloud Composer, MWAA, Astronomer | **Faible** — même moteur managé ailleurs |
| Spark | PySpark | → Databricks, EMR, Dataproc, Fabric | **Faible** — API identique |
| GitHub Actions | Workflow YAML | → GitLab CI, Azure DevOps (réécriture) | **Modéré** — syntaxe propriétaire |

**Conclusion** : aucun composant n'enferme la plateforme. Le point le plus propriétaire est le
format de workflow CI/CD, dont la réécriture reste marginale au regard du reste. Ce résultat
est **le fruit d'un choix délibéré** : préférer des interfaces standard (S3, SQL, PySpark) aux
services managés propriétaires, précisément pour préserver la réversibilité.

---

## 5. Estimation des coûts — trois scénarios

> Le jury n'attend pas un devis exact, mais **une méthode de chiffrage, des hypothèses
> explicites et un arbitrage argumenté**.

### 5.1 Hypothèses de volumétrie et de fréquence (communes aux trois scénarios)

| Hypothèse | Valeur retenue |
|---|---|
| Fichier décès mensuel | ~ 60 000 lignes / mois |
| Historique cumulé traité | ~ 25 M de lignes (fichiers annuels 2010→courant) |
| Volume de stockage brut (bronze versionné) | ~ 5 à 10 Go |
| Référentiel adhérents synthétique | 50 000 adhérents, ~ 80 000 contrats |
| Fréquence de traitement | 1 exécution complète / mois + rejeux ponctuels |
| Fenêtre de traitement distribué | quelques minutes / exécution |
| Rétention | historique complet (obligation de traçabilité) |

### 5.2 Scénario 1 — Local / on-premise conteneurisé *(solution retenue)*

Le logiciel est gratuit et le serveur existe déjà : le coût réel est le **temps humain**. Il faut
donc le chiffrer, et non le déclarer « nul ».

*Hypothèse de coût humain* : coût chargé d'un **alternant Master 2** ≈ **1 600 €/mois**, soit
≈ **90 €/jour** ouvré (les charges d'un contrat d'apprentissage sont largement exonérées, le coût
employeur reste proche du brut).

| Poste | Hypothèse | Coût |
|---|---|---|
| Logiciel (Airflow, Postgres, MinIO, Spark, GitHub Actions publics) | open source | **0 €** |
| Infrastructure | serveur interne existant (électricité négligeable) | **~ 0 €** |
| **Construction** (une fois) | ~ 15 j-homme × 90 € | **≈ 1 350 €** (amorti : ~ 37 €/mois sur 3 ans) |
| **Exploitation** (récurrent) | ~ 0,5 j-homme/mois (surveillance, rejeux, MCO) | **≈ 45 €/mois** |
| **Total mensuel récurrent** | exploitation seule → tout amorti | **≈ 45 à 82 €/mois** |

**Avantage** : pas de coût d'infrastructure, maîtrise totale, aucune donnée hors périmètre.
**Limite** : pas de scalabilité horizontale ni de haute disponibilité native (assumé, `LIMITES.md`).

### 5.3 Scénario 2 — Cloud managé Azure

Implémentation équivalente : Azure Data Factory (orchestration), Blob Storage (bronze), Azure
Database for PostgreSQL Flexible Server (entrepôt), un cluster Databricks éphémère pour le
distribué. Prix publics pay-as-you-go, région Europe (arrondis, hors remises).

| Poste | Ressource / SKU | Hypothèse | €/mois |
|---|---|---|---|
| Entrepôt | PostgreSQL Flexible **Burstable B1ms** (1 vCore, 2 Gio) | arrêt possible hors traitement | **~ 13** |
| Stockage entrepôt | 32 Go + sauvegardes | | **~ 4** |
| Orchestration | Data Factory | ~ 1 exécution/mois, quelques activités | **1 – 5** |
| Stockage brut | Blob Storage 10 Go (chaud) | + opérations | **1 – 2** |
| Calcul distribué | Databricks **job cluster** éphémère | quelques min/mois | **10 – 30** |
| Réseau | sortie de données | faible | **~ 3** |
| **Total** | | | **≈ 30 – 55 €/mois** |

> Une instance **B2s** (2 vCore/4 Gio, ~ **46 €/mois** de compute) porterait le total à
> **≈ 65 – 90 €/mois** si l'entrepôt doit rester allumé en permanence.

**Avantage** : haute disponibilité, scalabilité, exploitation déléguée.
**Limite** : coût récurrent, exposition d'un budget, gouvernance des accès cloud à outiller.

### 5.4 Scénario 3 — Plateforme SaaS (Snowflake / Microsoft Fabric)

Ce scénario **reprend l'étude réelle menée en année 2 chez Prévifrance** (architecture cible
Snowflake / Airflow, **maquettée, testée, non retenue**). Deux modèles de facturation opposés :

**Snowflake — facturation à l'usage (crédits) :**

| Poste | Hypothèse | €/mois |
|---|---|---|
| Calcul | édition Standard ≈ **2,50 €/crédit** (Europe) · warehouse **XS** = 1 crédit/h · auto-suspend · ~ 15–30 crédits/mois | **≈ 40 – 75** |
| Stockage | ~ 10 Go compressés (~ 23 €/To/mois) | **< 1** |
| **Total** | très sensible à l'usage | **≈ 40 – 80 €/mois** |

**Microsoft Fabric — facturation à la capacité :**

| Poste | Hypothèse | €/mois |
|---|---|---|
| Capacité | **F2** pay-as-you-go = **0,423 €/h** (2 CU) | allumée en continu → **~ 305** ; réservée → **~ 183** |
| | pausée agressivement (quelques h/mois) | fortement réduit, mais peu réaliste pour un entrepôt |
| **Total** | | **≈ 180 – 305 €/mois** (capacité maintenue) |

Lecture : un modèle **à l'usage** (Snowflake) reste bon marché sur un besoin intermittent ; un
modèle **à la capacité** (Fabric) devient cher dès qu'on maintient l'instance allumée.

**Raison documentée du non-retenu (contexte réel, année 2)** : arbitrage rendu **contre** la
bascule SaaS pour un faisceau de raisons — **coût récurrent** au regard d'un besoin mensuel à
faible intensité, **gouvernance des données** (santé et identité, sensibilité à la localisation et
à la sortie du SI maîtrisé), **maturité des équipes** sur l'existant SQL Server, et **absence de
gain décisif** sur une volumétrie que l'existant absorbait déjà. Décision collégiale (équipe data
+ DBA *gatekeeper*), sur critères coût / valeur / souveraineté. C'est le **matériau direct** de la
question de jury sur le vendor lock-in.

*Sources de prix (consultées pour le chiffrage)* : [Azure PostgreSQL Flexible Server —
prix](https://azure.microsoft.com/en-us/pricing/details/postgresql/flexible-server/) et
[comparatif Bytebase](https://www.bytebase.com/dbcost/azure-flexible-server-pricing/) ;
[Snowflake pricing — Revefi 2026](https://www.revefi.com/blog/snowflake-pricing-guide) ;
[Microsoft Fabric — prix Azure](https://azure.microsoft.com/en-us/pricing/details/microsoft-fabric/)
et [analyse Agilytic](https://www.agilytic.com/blog/microsoft-fabric-pricing). Ordres de grandeur,
région Europe, hors remises négociées.

### 5.5 Synthèse comparative

| Critère | Local (retenu) | Cloud Azure | SaaS Snowflake / Fabric |
|---|---|---|---|
| Coût mensuel | **~ 45 – 82 €** (temps humain) | ~ 30 – 90 € | Snowflake ~ 40 – 80 € · Fabric ~ 180 – 305 € |
| Scalabilité | Faible | Élevée | Très élevée |
| Haute disponibilité | Non | Oui | Oui |
| Souveraineté / contrôle | **Total** | Partagé | Délégué |
| Réversibilité (lock-in) | **Totale** | Bonne | Modérée |
| Adapté au besoin (mensuel, faible intensité) | **Oui** | Surdimensionné | Surdimensionné |

**Arbitrage.** Pour un traitement **mensuel, à faible intensité, à forte exigence de
souveraineté et à budget nul**, le scénario local conteneurisé est le mieux aligné. Les
scénarios cloud/SaaS restent la **trajectoire de montée en charge documentée** si la volumétrie
ou la fréquence changeaient d'ordre de grandeur (cf. question de jury « ×10 »).

---

## 6. Couverture des critères de la compétence C4.1.2

| Critère de la grille | Section qui le couvre | Preuve associée |
|---|---|---|
| **Liste des composants et technologies** | §2, §3 | `infra/docker-compose.yml` |
| **Avantages attendus** de chaque composant | §3, §3.1 | Architecture en fonctionnement (`preuves/`) |
| **Points de vigilance** | §3 (colonne dédiée) | `LIMITES.md` |
| **Vendor lock-in** | §4 | Tableau de substituabilité §4 |
| **Estimation des coûts** (méthode + hypothèses) | §5 (3 scénarios) | §5.1 hypothèses explicites |
| **Arbitrage argumenté** du non-retenu | §5.4, §5.5 | Étude année 2 (vécu Prévifrance) |
