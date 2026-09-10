# C4.3.3 — Documentation technique

> **Compétence visée.** Rédiger une documentation technique en énonçant son **public visé** et
> son **objectif**, puis en fournissant une documentation **réellement utilisable** (procédure
> de configuration, runbook d'exploitation).

---

## 1. Public visé et objectif

| | |
|---|---|
| **Public** | Ingénieur data / exploitant reprenant la plateforme (successeur, astreinte, pair). Suppose une aisance Docker, SQL et Python, **sans connaissance préalable** du projet. |
| **Objectif** | Permettre à cette personne de **démarrer la plateforme, exécuter la chaîne, diagnostiquer un incident et reprendre le service** sans recourir à l'auteur. |
| **Non-objectifs** | N'est pas un cours sur Airflow/Spark ; ne documente pas le contexte réglementaire (voir `C4-1-1`). |

Documents connexes : [`README.md`](../README.md) (vue d'ensemble),
[`docs/incident_metadonnees.md`](../docs/incident_metadonnees.md) (récit d'incident),
[`C4-3-2`](C4-3-2_feuille_route_exploitation.md) (calendrier d'exploitation).

---

## 2. Procédure de configuration (installation depuis zéro)

**Pré-requis** : Docker + Docker Compose, Python 3.11, ~4 Go de RAM libres.

```bash
# 1. Récupérer le dépôt
git clone https://github.com/ratpiGene/ELT-Eckert.git && cd ELT-Eckert

# 2. Configurer les secrets (jamais versionnés)
cp infra/.env.example infra/.env
#    puis renseigner les mots de passe et générer une clé Fernet :
python -c "import base64,os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
#    -> coller dans AIRFLOW__CORE__FERNET_KEY

# 3. Démarrer la plateforme
cd infra && docker compose --env-file .env up -d
```

| Service | URL | Identifiants |
|---|---|---|
| Airflow | http://localhost:8080 | `AIRFLOW_ADMIN_USER` / `AIRFLOW_ADMIN_PASSWORD` (.env) |
| MinIO | http://localhost:9001 | `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` |
| Spark | http://localhost:8081 | — |
| PostgreSQL | `localhost:5432/eckert` | `elt_writer` / `elt_reader` |

**Vérification** : `docker compose ps` — tous les services `Up` ; Airflow web `healthy`.

---

## 3. Exécuter la chaîne de bout en bout (démonstration)

```bash
export ELT_PG_DSN="postgresql://elt_writer:<mdp>@localhost:5432/eckert"

# 1. Générer le référentiel synthétique et le charger en silver
PYTHONPATH=src python -m eckert.referentiel.generate --adherents 20000
PYTHONPATH=src python -m eckert.referentiel.charger

# 2. Générer un fichier décès de démonstration (recouvrement contrôlé)
PYTHONPATH=src python -m eckert.referentiel.scenario_deces

# 3. Charger en bronze puis promouvoir en silver (fil de l'eau)
PYTHONPATH=src python -c "from pathlib import Path; \
from eckert.transform.charge_bronze import charger; \
from eckert.transform.bronze_vers_silver import promouvoir; \
charger(Path('data/bronze/demo/deces-demo.txt'), run_id='run1'); promouvoir(run_id='run1')"

# 4. Rapprochement distribué (Spark) -> gold
MSYS_NO_PATHCONV=1 docker exec -e PG_HOST=postgres -e PG_USER=elt_writer \
  -e PG_PASSWORD=<mdp> eckert-spark-master \
  spark-submit --master spark://spark-master:7077 \
  --packages org.postgresql:postgresql:42.7.4 \
  /opt/app/src/eckert/spark/rapprochement.py --run-id run1

# 5. Consulter le résultat métier
docker exec eckert-postgres psql -U postgres -d eckert \
  -c "SELECT * FROM gold.v_contrats_a_instruire ORDER BY priorite LIMIT 10;"
```

*(Note Windows/Git Bash : `MSYS_NO_PATHCONV=1` évite la conversion des chemins Unix.)*

---

## 4. Runbook d'exploitation (incidents courants)

### 4.1 Le DAG est en échec

1. **Airflow → Grid view** : repérer la tâche rouge, ouvrir ses logs.
2. Consulter le journal : `SELECT * FROM ops.journal_execution WHERE statut='ECHEC' ORDER BY horodatage DESC;`
3. Selon l'étape :
   - `telecharger_et_valider` **bloquant sur le contenu** → fichier réellement non conforme
     (taux de rejet, volumétrie). Vérifier le fichier source. **Ne pas** contourner la validation.
   - `charger_bronze` / `promouvoir_silver` → vérifier la connexion Postgres et l'espace disque.
4. Relancer la tâche (bouton *Clear*) une fois la cause traitée ; les `retries` gèrent le transitoire.

### 4.2 Tous les fichiers sont rejetés alors qu'ils semblent bons

C'est le **scénario de l'incident C4.4.2**. Vérifier qu'il ne s'agit **pas** d'une dépendance à
une métadonnée disparue. Rappel : la validation doit porter sur le **contenu**, jamais sur les
métadonnées déclarées (déjà corrigé, cf. `contract.py`). Voir `docs/incident_metadonnees.md`.

### 4.3 Le job Spark ne démarre pas

- Master joignable ? `docker logs eckert-spark-master`.
- Driver JDBC : le `--packages org.postgresql:postgresql:42.7.4` nécessite un accès réseau au
  premier lancement (mise en cache Ivy ensuite).
- Connexion Postgres depuis le conteneur : hôte `postgres` (réseau Compose), pas `localhost`.

### 4.4 Rotation d'un secret compromis

Procédure détaillée en [`C4-3-2` §3](C4-3-2_feuille_route_exploitation.md).

### 4.5 Repartir d'un état propre

```bash
cd infra && docker compose down -v   # ATTENTION : -v supprime les volumes (données perdues)
docker compose --env-file .env up -d # ré-initialise schémas, rôles, vues (scripts init)
```

---

## 5. Architecture des fichiers (pour s'orienter)

```
infra/          docker-compose, Dockerfile, init PostgreSQL (rôles, schémas, vues)
dags/           DAG Airflow (eckert_ingestion_deces)
src/eckert/     ingestion · validation · transform · referentiel · spark · supervision
src/sql/        DDL : 10 schémas+rôles, 20 tables, 30 vues gold
tests/          recette automatisée : test_contract (structurel), test_securite (sécurité)
.github/        workflow CI/CD
livrables/      les dix livrables du Bloc 4
preuves/        captures, logs, exports (inventaire.md)
```

---

## 6. Couverture des critères de la compétence C4.3.3

| Critère de la grille | Section | Preuve |
|---|---|---|
| **Public visé** énoncé | §1 | — |
| **Objectif** énoncé | §1 | — |
| **Procédure de configuration** utilisable | §2, §3 | reproductible depuis zéro |
| **Runbook** d'exploitation | §4 | incidents courants + reprise |
| Documentation **réellement utilisable** | §2-§5 | commandes exactes, `README.md` |
