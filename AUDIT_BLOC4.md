# Audit contradictoire — Bloc 4 (RNCP 39586)

> Passage **verdict seulement** (Acquis / Non Acquis / Acquis avec réserve), avec la citation ou
> la preuve qui le justifie. Les corrections ne figurent **pas** ici (règle `CLAUDE.md` §8).
> Position d'auditeur : chercher ce qui pècherait devant un jury, pas valider par principe.

Échelle : **A** = Acquis (preuve tangible) · **A/r** = Acquis avec réserve (preuve présente
mais un angle reste déclaratif) · **NA** = Non Acquis.

---

## C4.1.1 — Analyser l'environnement

| Critère | Verdict | Justification |
|---|---|---|
| Besoins | **A** | `C4-1-1` §1 (B1→B6), traçant loi → besoin technique |
| Enjeux du projet | **A** | `C4-1-1` §2 (conformité, fiabilité, résilience) |
| Environnement | **A** | §3 (organisationnel, technique d'origine, reconstruit) |
| Contraintes coût / délai / complexité | **A** | §4, les trois traitées explicitement |
| État de l'existant | **A** | §5 + distinction étudié/maquetté/prod |

**Verdict compétence : A.** Rien à redire : l'analyse cadre la conception et distingue vécu / reconstruit.

---

## C4.1.2 — Sélectionner les composants

| Critère | Verdict | Justification |
|---|---|---|
| Liste composants / technologies | **A** | `C4-1-2` §2-§3 + `docker-compose.yml` réel |
| Avantages attendus | **A** | §3 (colonne dédiée) |
| Points de vigilance (dont lock-in) | **A** | §3 + §4 (tableau de substituabilité S3/SQL/PySpark) |
| Estimation des coûts | **A/r** | §5, trois scénarios avec hypothèses. **Réserve** : chiffres en ordre de grandeur (assumé) — le jury peut demander la source d'un poste précis (ex. Databricks) |

**Verdict compétence : A.** L'estimation de coût — souvent absente des dossiers — est présente et méthodique. La réserve est mineure et anticipée dans `questions_jury.md`.

---

## C4.2.1 — Concevoir l'entrepôt

| Critère | Verdict | Justification |
|---|---|---|
| Type de données | **A** | `C4-2-1` §1 + `20_tables.sql` |
| Organisation | **A** | §2-§3 (bronze/silver/gold/ops), preuve `C4-2-1_schema_postgres.txt` |
| Modalités d'accès | **A** | §4 + `10_schemas.sql`, `30_vues_gold.sql` |
| Justif. rapidité | **A** | §4.3 (index, COPY, ensembliste) |
| Justif. sécurité | **A** | §4.1 + tests SEC-02/03 **verts contre la base réelle** |
| Justif. accessibilité | **A** | vue `v_contrats_a_instruire` lue par `elt_reader` (preuve) |

**Verdict compétence : A.** La sécurité est *prouvée*, pas déclarée (c'est un point fort réel).

---

## C4.2.2 — Pipelines (le point de rupture de la grille)

| Critère | Verdict | Justification |
|---|---|---|
| Pipeline temps réel (Python/SQL) → donnée | **A** | `bronze_vers_silver.py` → `silver.deces`, preuve `C4-2-2_bronze_silver.txt` |
| Pipeline orchestré (Airflow) → donnée | **A** | DAG `eckert_ingestion_deces` **4 tâches SUCCESS** sur le vrai fichier INSEE (`C4-2-2_airflow_run.png`) |
| Pipeline distribué (Spark) → donnée | **A** | job sur cluster → `gold.contrat_desherence`, Spark UI FINISHED (`C4-2-2_spark_ui.png`), 4162 contrats |
| Recours au distribué justifié | **A** | §4.1 (volumétrie cumulée) + reconnaissance honnête que Postgres suffirait au mois |

**Verdict compétence : A.** Les trois méthodes existent, tournent et produisent chacune une donnée. **Réserve mineure (non bloquante)** : le job Spark est soumis manuellement, non déclenché par Airflow (documenté `LIMITES.md`). La grille exige trois méthodes, pas leur chaînage — donc non pénalisant.

---

## C4.2.3 — CI/CD

| Critère | Verdict | Justification |
|---|---|---|
| Automatise l'intégration | **A** | 3 jobs (qualité, tests, sécurité) verts, `C4-2-3_ci_jobs.txt` |
| Automatise le déploiement | **A** | job `deploiement` : build → **push sur GHCR** (`ghcr.io/ratpigene/eckert-elt:<sha>` + `latest`) → **pull depuis le registre** + smoke test. Déploiement d'artefact réel, tous les steps verts (run #6) |
| Fichier de workflow | **A** | `.github/workflows/ci.yml` |
| Capture d'exécution réelle | **A** | `C4-2-3_ci_run_vert.png` (5 jobs Success) + `C4-2-3_deploiement_ghcr.png` (image publiée) |

**Verdict compétence : A.** Réserve levée : l'image est **publiée sur un registre et revérifiée par pull**, récupérable par tout consommateur. Reste une limite honnête (pas de mise en service auto sur un cluster cible), assumée `LIMITES.md`.

---

## C4.3.1 — Supervision et alertes

| Critère | Verdict | Justification |
|---|---|---|
| Éléments / indicateurs surveillés | **A** | `C4-3-1` §1-§2 + `ops.journal_execution` (preuve `C4-3-1_journal_ops.txt`) |
| Choix / configuration des outils | **A** | §3 (callbacks, SLA, retries) dans le DAG |
| Visualisation | **A** | Airflow Grid/Event Log (`C4-3-1_airflow_eventlog.png`, retry visible) |
| Système d'alertes : seuils | **A** | seuils centralisés (`TAUX_REJET_MAX`, `LIGNES_MINIMUM`) |
| Alertes : canaux / destinataires / escalade | **A** | §4 : journal→webhook→courriel. **Alerte réellement délivrée** capturée (`C4-3-1_alerte_webhook.txt`) : titre + corps + destinataire, sur échec provoqué du DAG `eckert_demo_alerte` |

**Verdict compétence : A.** Réserve levée : la notification est **délivrée et capturée** (webhook reçu), en plus de la trace `ECHEC` en base. Les deux canaux sont prouvés bout en bout.

---

## C4.3.2 — Exploitation / MCO

| Critère | Verdict | Justification |
|---|---|---|
| Tâches (dont certificats et secrets) | **A** | `C4-3-2` §2-§3, procédure de rotation détaillée |
| Échéances | **A** | colonnes échéance par périodicité |
| Planification de la maintenance | **A** | §2.3-§2.5 (trim./sem./annuel) |
| Points de vigilance | **A** | §4 + colonnes vigilance |
| Format calendaire | **A** | tableaux par périodicité |

**Verdict compétence : A.**

---

## C4.3.3 — Documentation technique

| Critère | Verdict | Justification |
|---|---|---|
| Public visé énoncé | **A** | `C4-3-3` §1 |
| Objectif énoncé | **A** | §1 |
| Procédure de configuration utilisable | **A** | §2-§3 (repro depuis zéro, commandes exactes) |
| Runbook | **A** | §4 (DAG en échec, Spark, rotation, reset) |

**Verdict compétence : A.** La procédure a été validée dans les faits (c'est ainsi que la plateforme a été montée).

---

## C4.4.1 — Cahier de recette

| Critère | Verdict | Justification |
|---|---|---|
| Toutes les fonctionnalités attendues | **A** | `C4-4-1` §1 (F1→F8) mappées aux tests |
| Tests fonctionnels | **A** | §3 |
| Tests structurels | **A** | §4 (10 cas) |
| Tests de sécurité | **A** | §5 (droits, secrets, dépendances) — souvent le trou des dossiers |
| Exécutés avec résultats | **A** | `C4-4-1_recette_complete.txt` (19 tests, 19 réussis) + CI |

**Verdict compétence : A.** Point fort : sécurité *testée* et recette *rejouée en CI*.

---

## C4.4.2 — Incident

| Critère | Verdict | Justification |
|---|---|---|
| Nature du problème | **A** | `C4-4-2` §1 + `docs/incident_metadonnees.md` |
| Actions selon scénarios | **A** | §4 (3 scénarios : absent / divergent / contenu KO) |
| Communication aux parties prenantes | **A** | §5 (équipe, métier, producteur, CR écrit) |
| Résultats attendus | **A** | §6 |
| Résolution effective | **A** | `C4-4-2_incident_rejeu.txt` + test de non-régression |

**Verdict compétence : A.** Incident réel, cause non triviale, correctif structurel, rejeu prouvé. **C'est la pièce maîtresse du dossier.**

---

## Synthèse

| Compétence | Verdict |
|---|---|
| C4.1.1 Analyse | **A** |
| C4.1.2 Composants / coûts | **A** |
| C4.2.1 Entrepôt | **A** |
| C4.2.2 Pipelines (×3) | **A** |
| C4.2.3 CI/CD | **A** |
| C4.3.1 Supervision | **A** |
| C4.3.2 Exploitation | **A** |
| C4.3.3 Documentation | **A** |
| C4.4.1 Recette | **A** |
| C4.4.2 Incident | **A** |

### Verdict global : **le bloc se valide — 10 compétences Acquises, sans réserve.**

Les dix compétences sont couvertes par un livrable **et** une preuve tangible. La plateforme
tourne réellement (DAG réel vert, Spark FINISHED, CI verte, sécurité testée), ce qui fait passer
six compétences du déclaratif au démontré.

### Les deux réserves de la première passe ont été levées

1. **C4.2.3 « déploiement »** — **levée** : le job publie désormais l'image sur GHCR
   (`ghcr.io/ratpigene/eckert-elt`) et la revérifie par `docker pull` + smoke test. Reste une
   limite honnête (pas de mise en service auto sur cluster cible), assumée `LIMITES.md`.
2. **C4.3.1 « destinataires d'alerte »** — **levée** : une alerte réellement délivrée est
   capturée (`preuves/C4-3-1_alerte_webhook.txt`), avec titre, corps et destinataire, en plus de
   la trace `ECHEC` en base.

### Risque résiduel principal

Ce n'est pas un critère manquant, c'est un **risque de crédibilité à l'oral** : ne pas surjouer
la maîtrise de Spark (peu pratiqué). La parade est déjà écrite (`questions_jury.md`) : assumer
que Postgres suffirait au volume mensuel et justifier Spark par la trajectoire.
