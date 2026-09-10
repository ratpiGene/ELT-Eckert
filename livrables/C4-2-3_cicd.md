# C4.2.3 — Pipeline d'intégration et de déploiement continus

> **Compétence visée.** Mettre en place un pipeline **CI/CD** automatisant l'**intégration**
> (qualité, tests, sécurité) et le **déploiement**, avec un fichier de workflow et la **preuve
> d'une exécution réelle**.

> **Trou comblé.** Dans le vécu Prévifrance, le déploiement était **100 % manuel** et aucun
> contrôle automatisé n'existait. Ce pipeline est construit de zéro.

---

## 1. Choix de l'outil

**GitHub Actions**, pour trois raisons alignées sur les contraintes du projet :

- **Gratuit** sur dépôt public, sans infrastructure à maintenir (contrainte de coût) ;
- **Exécutions horodatées et exportables** — chaque run est une preuve datée réutilisable ;
- **Déclenchement natif** sur `push` et `pull_request`, au plus près du geste de développement.

Point de vigilance assumé : les runners publics ne doivent contenir **aucun secret réel** —
d'où le job de vérification de non-exposition (§2, `securite`).

Fichier : [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

---

## 2. Le pipeline — cinq étages

```
push / pull_request sur main
        │
   ┌────┴─────┬──────────────┐
   ▼          ▼              ▼
qualite     tests        securite          (intégration, en parallèle)
   └────┬─────┘              │
        ▼                    │
      dags  ◄────────────────┘              (validation Airflow)
        │
        ▼
   deploiement                              (si push sur main)
```

| Job | Rôle | Outils | Critère couvert |
|---|---|---|---|
| **qualite** | Analyse statique + format | `ruff check`, `ruff format --check` | Intégration |
| **tests** | Cahier de recette automatisé | `pytest` + couverture, rapport JUnit archivé | Intégration |
| **securite** | Vulnérabilités + secrets | `pip-audit --strict`, contrôle qu'aucun `.env` n'est versionné | Intégration / **sécurité** |
| **dags** | Import des DAG sans erreur | Airflow (contraintes officielles) + `dags list-import-errors` | Intégration |
| **deploiement** | Construction et vérification de l'image | `docker build`, run de vérification, résumé de version | **Déploiement** |

### 2.1 Intégration

- **Qualité** : `ruff` échoue le build sur toute entorse de lint ou de format — la base de code
  reste homogène.
- **Tests** : exécute `tests/` (structurels + sécurité), publie couverture et rapport JUnit en
  artefact téléchargeable.
- **Sécurité** : `pip-audit --strict` échoue s'il existe **une seule** vulnérabilité connue dans
  les dépendances (c'est ce qui a imposé de monter `requests`, `python-dotenv` et `pytest` vers
  des versions corrigées). Un contrôle refuse tout `.env` versionné.
- **DAG** : Airflow est installé avec son **fichier de contraintes officiel** (évite les
  conflits de résolution) et vérifie que les DAG s'importent sans `Traceback`.

### 2.2 Déploiement

Le job `deploiement` ne s'exécute que sur `push` vers `main`, après succès de `dags` et
`securite`. Il **construit l'image applicative** (`infra/Dockerfile`), **vérifie qu'elle
démarre** (`python -c "import eckert"`), et journalise la version (SHA) dans le résumé du run.

**Limite assumée** (`LIMITES.md`) : le déploiement s'arrête à la construction et à la
vérification de l'image. Il n'y a pas d'environnement cible exposé depuis un runner public, ni
de secret de déploiement dans le dépôt public — le déploiement effectif vers un environnement
joignable est décrit comme évolution.

---

## 3. Sécurité par conception dans la CI

Le pipeline **est lui-même un contrôle de sécurité** (contribue à C4.4.1) :

- scan de dépendances (`pip-audit --strict`) — au moins une vulnérabilité connue = build rouge ;
- refus de tout secret versionné (`.env`) ;
- image applicative exécutée **sans privilèges** (`USER eckert`, cf. `infra/Dockerfile`).

---

## 4. Preuve d'exécution réelle

Le pipeline s'exécute à chaque `push` sur le dépôt `ratpiGene/ELT-Eckert`. Historique complet
et logs : **onglet Actions du dépôt**.

| Preuve | Contenu |
|---|---|
| `preuves/C4-2-3_ci_run_vert.png` | Capture d'un run vert (les cinq jobs) |
| `preuves/C4-2-3_ci_jobs.txt` | Conclusion par job (API Actions) |
| `preuves/C4-2-3_pip_audit.txt` | Sortie « No known vulnerabilities found » |

> Note de méthode : le premier run a échoué (format ruff, puis conflit d'installation Airflow).
> Ces échecs **font partie de la preuve** : ils montrent que les garde-fous mordent réellement.
> La correction (format appliqué, Airflow installé via contraintes) a ramené le pipeline au vert.

---

## 5. Couverture des critères de la compétence C4.2.3

| Critère de la grille | Section | Preuve |
|---|---|---|
| Pipeline automatisant l'**intégration** | §2.1 | `.github/workflows/ci.yml`, run vert |
| Pipeline automatisant le **déploiement** | §2.2 | job `deploiement` (build image) |
| **Fichier de workflow** fourni | §1 | `.github/workflows/ci.yml` |
| **Capture d'une exécution réelle** | §4 | `preuves/C4-2-3_ci_run_vert.png` |
| Contrôles de **sécurité** intégrés | §3 | `preuves/C4-2-3_pip_audit.txt` |
