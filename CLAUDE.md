# CLAUDE.md — Bloc 4 (Spé Data Engineer) — RNCP 39586

## 1. Ce que ce dépôt produit

Trois choses, dans cet ordre :

1. **Une plateforme data qui tourne** — reconstruite proprement, sur le contexte métier de l'alternance Prévifrance (obligation loi Eckert), avec des données publiques.
2. **Le dossier du Bloc 4** — dix livrables, un par compétence C4.1.1 → C4.4.2.
3. **Le support projetable** de la soutenance (≈ 45 min + 15 min de questions).

La plateforme n'est pas un prétexte : c'est elle qui fournit les captures, les logs, les métriques et l'incident rejoué. Sans elle, six compétences sur dix restent déclaratives.

## 2. Contrainte majeure : moins d'un mois

Conséquences non négociables sur les choix techniques :

- **Rien de managé, rien de facturé.** Pas de compte cloud à provisionner, pas de quota à négocier, pas de carte bancaire. Tout tourne en local sous Docker Compose.
- **Chaque brique doit produire une capture d'écran en moins de 5 minutes.** Un composant qu'on ne peut pas montrer ne sert pas le jury.
- **Deux semaines de construction, deux semaines de rédaction et de répétition.** Voir le rétroplanning §9.
- Toute idée qui allonge le chemin critique est écartée et notée dans `LIMITES.md` comme évolution assumée — le jury valorise une limite consciente, pas une brique bâclée.

Claude doit refuser d'ajouter des outils au périmètre sans qu'une compétence de la grille l'exige.

## 3. Contexte métier (le fond du dossier)

**Le problème.** Une mutuelle santé et prévoyance doit identifier ses adhérents décédés pour traiter les contrats en déshérence — c'est une obligation légale (loi Eckert), avec un risque de sanction ACPR et un enjeu de confiance pour les ayants droit. La source de vérité externe est le **fichier des personnes décédées publié par l'INSEE sur data.gouv.fr**.

**Le vécu qui alimente le dossier** (Prévifrance, site d'Agen, poste de chargé d'étude Data / AMOA) :

- Existant décisionnel SQL Server (DWH_AI, DWH_DSN_PREVI, FRUP00), rapports SSRS, traitements T-SQL.
- Un traitement de collecte Eckert orchestré sous Airflow, mis en production.
- Une étude d'architecture cible Snowflake / Airflow menée en année 2 : maquettée, testée, **non retenue** — matériau direct pour C4.1.2.
- Gouvernance contraignante : un DBA en position de gatekeeper sur les accès et les objets de base ; arbitrages de charge via Jira.
- Avant production : contrôles de cohérence (volumétries, totaux, recoupement avec l'existant) et revue SQL par le DBA. **Aucun cahier de recette formalisé** — c'est précisément ce que le Bloc 4 demande de produire.
- Supervision réelle : jobs SQL Server Agent et logs SSRS consultés manuellement. Pas d'alerting outillé.
- **Aucun Spark, aucun CI/CD** dans l'environnement d'origine.

**L'incident réel à rejouer (C4.4.2).** Le traitement ELT Eckert validait la conformité du fichier reçu en s'appuyant sur les métadonnées annoncées sur data.gouv. Au bout d'environ deux mois, les fichiers récupérés ne contenaient plus les métadonnées décrites sur la plateforme : le contrôle d'entrée rejetait systématiquement le fichier et le traitement tombait en erreur. La résolution a consisté à revoir les règles de validation — passer d'une confiance dans les métadonnées déclarées à une validation du contenu réel.

Cet incident est le meilleur atout du dossier : il est vrai, il est technique, il a une cause non triviale (le contrat de données change sans préavis côté producteur), et il débouche sur une correction d'architecture. Il doit être **rejoué dans la plateforme reconstruite** — un fichier de test amputé de ses métadonnées, le pipeline qui échoue, l'alerte qui part, le diagnostic, le correctif, le rejeu vert.

**Règle d'honnêteté.** Le dossier présente une plateforme reconstruite sur un contexte métier réel, pas le SI de Prévifrance. Cette distinction est écrite noir sur blanc en introduction du dossier et dite à l'oral dès la deuxième diapositive. Aucune donnée d'entreprise, aucune donnée personnelle d'adhérent n'entre dans le dépôt. Le référentiel adhérents est **synthétique** (généré avec Faker, volumétrie et distributions plausibles).

## 4. Architecture cible

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
            Spark (batch distribué)              Python/SQL (flux)           │
            rapprochement décès × contrats       traitement au fil de l'eau  │
                    │                                    │                   │
                    └─────────────────┬──────────────────┘                   │
                                      ▼                                      │
                          PostgreSQL — entrepôt                              │
                          schémas : bronze / silver / gold                   │
                                      │                                      │
                                      ▼                                      │
                          Restitution : vues gold + Metabase                 │
                                                                             │
     Supervision : callbacks Airflow, SLA, alerting, dashboard qualité ──────┘
     CI/CD : GitHub Actions (lint, tests, build image, déploiement)
```

**Stack retenue et justification** (à reprendre telle quelle dans C4.1.2) :

| Composant | Choix | Pourquoi | Point de vigilance |
|---|---|---|---|
| Orchestration | Apache Airflow | Déjà pratiqué sur le traitement Eckert réel ; DAG lisible en soutenance ; callbacks et SLA natifs | Empreinte mémoire du Compose ; scheduler à surveiller |
| Stockage brut | MinIO (S3-compatible) | Sépare le brut du modélisé, versionne les fichiers reçus, prépare une bascule cloud sans réécriture | Pas de cycle de vie automatique en local |
| Entrepôt | PostgreSQL | Rôles et droits démontrables (sécurité), index et plans d'exécution (rapidité), schémas par couche (organisation) | Ne scale pas horizontalement — assumé et argumenté |
| Distribué | Apache Spark (PySpark) | Le fichier décès cumulé se compte en dizaines de millions de lignes : le distribué est justifié par la donnée, pas par la grille | Coût de démarrage du cluster local ; ne pas sur-dimensionner |
| Temps réel / flux | Python + SQL déclenché à l'arrivée d'un fichier | Répond au « pipeline temps réel (ex : SQL, Python) » de la grille sans monter un Kafka | Bien nommer : traitement au fil de l'eau, pas streaming |
| CI/CD | GitHub Actions | Gratuit, exécutions horodatées et exportables en preuve | Runners publics : pas de secret réel dans le dépôt |
| Supervision | Airflow (callbacks, SLA, alerting) + dashboard qualité | Choix assumé de légèreté sur le délai disponible | Pas de métrique d'infra — noté dans LIMITES.md |
| Restitution | Vues `gold` + Metabase | Montre l'accessibilité pour le métier | Optionnel si le temps manque |

**Estimation des coûts (critère explicite de C4.1.2 — à ne pas oublier).** Produire dans le livrable un tableau à trois scénarios, avec les hypothèses de volumétrie écrites :

1. **Local / on-premise conteneurisé** (la solution retenue) : coût logiciel nul, coût d'infrastructure = un serveur existant, coût principal = temps d'exploitation humain.
2. **Cloud managé Azure** (Data Factory, Storage, Azure SQL ou Databricks) : chiffrer en ordre de grandeur mensuel, hypothèses de volume et de fréquence assumées.
3. **Plateforme SaaS type Snowflake / Microsoft Fabric** : reprendre l'étude réelle menée en année 2, ses coûts estimés, et **la raison documentée du non-retenu**.

Le jury n'attend pas un devis exact : il attend une méthode de chiffrage, des hypothèses explicites et un arbitrage argumenté. Le vendor lock-in se traite ici.

## 5. Les dix livrables

Un fichier par compétence dans `livrables/`. Chaque livrable se termine par un tableau `critère de la grille → section qui le couvre → preuve associée`.

| Compétence | Livrable | Ce qu'il faut absolument y trouver |
|---|---|---|
| **C4.1.1** Analyser l'environnement | `C4-1-1_rapport_analyse.md` | Besoins, enjeux du projet, environnement, **contraintes (coût, délais, complexité)**, état de l'existant. Doit cadrer la conception. |
| **C4.1.2** Sélectionner les composants | `C4-1-2_composants_architecture.md` | Liste des composants et technologies, avantages attendus, points de vigilance dont le **vendor lock-in**, **estimation des coûts** (§4). |
| **C4.2.1** Concevoir l'entrepôt | `C4-2-1_schema_donnees.md` | Type de données, **modalités d'accès**, organisation. Justifier rapidité / sécurité / accessibilité. |
| **C4.2.2** Pipelines | `C4-2-2_pipelines.md` | ⚠️ **Trois** méthodes : temps réel (Python/SQL), orchestrateur (Airflow), **calculs distribués (Spark)**. Chacune produit une donnée demandée. |
| **C4.2.3** CI/CD | `C4-2-3_cicd.md` | Un pipeline qui automatise **intégration et déploiement**. Fichier de workflow + capture d'une exécution réelle. |
| **C4.3.1** Supervision | `C4-3-1_supervision.md` | Éléments et indicateurs surveillés, choix et **configuration** des outils, visualisation, **système d'alertes** (seuils, canaux, destinataires, escalade). |
| **C4.3.2** Exploitation / MCO | `C4-3-2_feuille_route_exploitation.md` | Tâches (dont renouvellement de certificats et de secrets), échéances, **planification de la maintenance**, points de vigilance. Format calendaire. |
| **C4.3.3** Documentation | `C4-3-3_documentation_technique.md` | Public visé + objectif énoncés, puis une doc réellement utilisable (procédure de configuration, runbook). |
| **C4.4.1** Cahier de recette | `C4-4-1_cahier_recette.md` | **Toutes** les fonctionnalités attendues, tests **fonctionnels, structurels ET de sécurité**, exécutés, avec résultats obtenus. |
| **C4.4.2** Incident | `C4-4-2_methodologie_incident.md` | L'incident métadonnées (§3) : nature du problème, actions selon scénarios, **communication aux parties prenantes**, résultats attendus, résolution effective. |

### Les quatre trous à combler en priorité

Ce sont les compétences sans matériau d'origine. Elles passent en premier dans le rétroplanning.

1. **C4.2.2 — le distribué.** Zéro Spark dans le vécu. Le job PySpark de rapprochement décès × référentiel est **la** brique à sécuriser en premier : sans elle, la compétence tombe en Non Acquis, quelle que soit la qualité du reste.
2. **C4.2.3 — le CI/CD.** Déploiement 100 % manuel à l'origine. Le workflow GitHub Actions est à monter de zéro : lint, tests unitaires, validation des DAG, build de l'image, déploiement.
3. **C4.3.1 — l'alerting.** L'existant se limitait à des logs consultés à la main. À construire : callbacks d'échec, SLA, notification, et une visualisation d'indicateurs.
4. **C4.4.1 — les tests de sécurité.** Les contrôles de cohérence et la revue DBA existaient, mais rien n'était consigné et la sécurité n'était pas testée. À produire : matrice de tests écrite, avec au minimum un test de droits (un rôle en lecture seule ne peut pas écrire), un test de non-exposition de secrets et un scan de dépendances dans la CI.

## 6. Données

- **Source principale** : fichier des personnes décédées de l'INSEE, sur data.gouv.fr. Format texte à largeur fixe, publication mensuelle et fichiers annuels historiques. Vérifier la volumétrie réelle au téléchargement et la citer dans le dossier — c'est elle qui justifie le recours au distribué.
- **Référentiel adhérents / contrats** : **synthétique**, généré avec Faker (adhérents, contrats, bénéficiaires, dates d'effet, statuts). Volumétrie paramétrable, distributions rendues plausibles pour une mutuelle régionale. Un taux de correspondance volontairement réaliste avec le fichier décès pour que le rapprochement produise des résultats exploitables.
- **Jeux de test dégradés** — indispensables pour C4.4.1 et C4.4.2 : fichier sans métadonnées (l'incident réel), fichier tronqué, colonne décalée, doublons, date impossible, encodage inattendu.
- Aucune donnée d'entreprise, aucune donnée personnelle réelle. Le `.gitignore` exclut `data/` ; seuls des échantillons anonymisés de quelques lignes sont versionnés.

## 7. Structure du dépôt

```
/infra/               docker-compose.yml, Dockerfiles, .env.example
/dags/                DAG Airflow
/src/
  ingestion/          téléchargement, dépôt bronze, manifeste
  validation/         contrat de données, règles de conformité
  spark/              job de rapprochement distribué
  streaming/          traitement au fil de l'eau (Python/SQL)
  sql/                DDL des schémas bronze / silver / gold, vues, rôles
/tests/               unitaires, intégration, sécurité
/.github/workflows/   pipeline CI/CD
/livrables/           un fichier par compétence C4.x.y
/preuves/             captures, exports, logs, inventaire.md
/soutenance/          support projetable, notes, questions_jury.md
/dossier/             dossier assemblé (PDF final)
LIMITES.md            ce qui n'a pas été fait, et pourquoi
```

Conventions : nommage des preuves en `C4-2-2_spark_execution.png` ; secrets uniquement dans `.env` (jamais versionné) et dans les secrets GitHub ; schémas en source (mermaid ou draw.io) puis exportés en PNG.

## 8. Comment Claude travaille sur ce dépôt

- Rattacher **chaque section produite à une compétence C4.x.y**, nommément.
- Ne jamais écrire qu'une brique fonctionne sans preuve dans `preuves/`. Si la preuve manque, l'écrire dans `LIMITES.md` et le dire.
- Distinguer systématiquement **étudié / maquetté / en production**, aussi bien pour la plateforme reconstruite que pour le vécu Prévifrance.
- Français professionnel. « Je » pour les actions portées personnellement, « nous » pour les décisions collectives de l'alternance.
- Pas de superlatif, pas de vocabulaire d'agence. Un fait, un chiffre, une limite.
- Avant chaque rédaction de livrable : relire les critères correspondants au §5 et vérifier point par point.
- **Audit avant correction** : quand Claude relit un livrable, il rend d'abord un verdict Acquis / Non Acquis par critère avec la citation qui le justifie, puis seulement ensuite propose les corrections. Jamais les deux dans le même passage.

## 9. Rétroplanning (4 semaines)

**Semaine 1 — la plateforme tourne.**
Compose (Airflow, Postgres, MinIO, Spark) ; ingestion du fichier INSEE ; DDL bronze/silver/gold + rôles ; générateur de référentiel synthétique ; premier DAG bout en bout, même minimal. Livrable de la semaine : une exécution verte capturée.

**Semaine 2 — les quatre trous.**
Job Spark de rapprochement (priorité absolue) ; traitement au fil de l'eau ; workflow GitHub Actions complet ; callbacks et alerting Airflow ; matrice de tests dont sécurité ; **rejeu de l'incident métadonnées** avec captures avant/après. Livrable : `preuves/inventaire.md` complet, une preuve par compétence.

**Semaine 3 — le dossier.**
Les dix livrables, dans l'ordre C4.1.1 → C4.4.2. Un livrable, un tableau de couverture des critères. En fin de semaine : audit contradictoire complet de Claude, verdict par compétence, corrections priorisées par gravité.

**Semaine 4 — la soutenance.**
Support projetable, notes de commentaire, `questions_jury.md`, deux répétitions chronométrées minimum, coupes, assemblage du PDF.

Règle de coupe : à la fin de la semaine 2, ce qui ne tourne pas ne sera pas dans le dossier. On bascule dans `LIMITES.md` et on avance.

## 10. Soutenance : 45 minutes + 15 minutes de questions

Un support projetable est à fournir **en complément** du dossier. Cible : **32 à 38 diapositives**, une idée par diapositive, titres assertifs (le titre énonce la conclusion, pas le thème).

**Règles de conception.** Cinq lignes maximum par diapositive, le reste se dit et vit dans les notes de commentaire. Un bandeau discret rappelle la compétence traitée (`C4.2.2`) sur chaque diapositive de démonstration — le jury note par compétence, il doit se repérer sans effort. Captures réelles plutôt que schémas génériques. Texte projeté ≥ 18 pt, 12 blocs maximum par schéma, extraits de code de 15 lignes maximum avec la ligne qui compte surlignée. Annexes numérotées A1, A2… après la conclusion, pour les questions.

| Temps | Séquence | Diapos | Compétences |
|---|---|---|---|
| 0-4 min | Contexte : obligation Eckert, enjeu, mon rôle, **périmètre honnête du projet reconstruit** | 1-4 | — |
| 4-10 min | Analyse : besoins, enjeux, environnement, contraintes, existant | 5-8 | C4.1.1 |
| 10-16 min | Choix des composants : alternatives, arbitrage, **coûts**, vigilance et lock-in | 9-13 | C4.1.2 |
| 16-21 min | Entrepôt : schéma, couches, accès, sécurité | 14-17 | C4.2.1 |
| 21-28 min | Les trois traitements : fil de l'eau, orchestration, **distribué** | 18-23 | C4.2.2 |
| 28-31 min | Industrialisation : pipeline CI/CD, exécution réelle | 24-26 | C4.2.3 |
| 31-36 min | Exploitation : supervision et alertes, feuille de route, documentation | 27-31 | C4.3.1/2/3 |
| 36-42 min | Qualité et résilience : cahier de recette, **incident métadonnées rejoué** | 32-35 | C4.4.1/2 |
| 42-45 min | Bilan : résultats, limites assumées, ce que je referais autrement | 36-37 | — |
| +15 min | Questions du jury, appui sur les annexes | A1-A… | toutes |

Dix compétences en 45 minutes, c'est **4 minutes chacune**. Toute séquence qui dépasse son créneau de plus d'une minute est coupée, pas accélérée.

**Moment fort à soigner** : la séquence 36-42 min. Un incident vrai, raconté avec sa cause non évidente (le producteur de données change son contrat sans préavis) et sa correction structurelle, vaut plus que dix diapositives d'architecture. C'est là que se joue la différence entre un candidat qui a suivi un tutoriel et un ingénieur.

## 11. Préparation des 15 minutes de questions

`soutenance/questions_jury.md` : pour chaque compétence, deux questions probables et leur réponse en 60 secondes. À préparer en priorité, parce qu'elles tombent presque toujours :

- Pourquoi Spark ici, alors qu'un Postgres bien indexé traiterait ce volume ? *(Question piège assumée : répondre par la volumétrie cumulée, la trajectoire de croissance et le coût de la fenêtre de traitement — et reconnaître que sur le volume mensuel seul, Postgres suffirait.)*
- Pourquoi Snowflake / Fabric n'a-t-il pas été retenu dans le contexte réel ? Qui a tranché, sur quels critères, pour quel coût comparé ?
- Comment l'architecture se comporte-t-elle si le volume est multiplié par dix ?
- Où sont les données personnelles, qui y accède, comment la traçabilité et les durées de conservation sont-elles assurées (RGPD) ?
- Que se passe-t-il si le traitement échoue à 3 h du matin ? Qui est alerté, sous quel délai, avec quelle procédure de reprise ?
- Comment une modification est-elle testée avant production ? Qui valide, comment revient-on en arrière ?
- Quelle est la part réellement construite par vous, et quelle est la part reprise de l'entreprise ?
- Qu'est-ce qui n'a pas fonctionné, et qu'en avez-vous tiré ?

Règle de réponse : une phrase de réponse directe, puis un fait, puis une limite honnête. Ne jamais surjouer la maîtrise d'un outil peu pratiqué — le jury creuse ce qui sonne appris par cœur.

## 12. Points de vigilance du bloc

1. **C4.2.2 est le point de rupture.** Trois méthodes exigées, dont le distribué. C'est le premier livrable à sécuriser, en semaine 2 au plus tard.
2. **L'estimation des coûts de C4.1.2** est un critère écrit, presque toujours absent des dossiers. Chiffrer, avec hypothèses assumées.
3. **Les tests de sécurité de C4.4.1** sont explicitement listés. Ne pas se limiter au fonctionnel.
4. **Ce n'est pas un dossier de reporting.** L'attendu est une infrastructure conçue et opérée. Le vécu Prévifrance sert à ancrer le besoin et l'incident, pas à raconter des rapports SSRS.
5. **Assumer les limites** plutôt que les masquer. Un `LIMITES.md` lucide, cité à l'oral, démontre plus de maturité d'ingénieur qu'une brique survendue.
