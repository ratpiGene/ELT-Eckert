# ELT Eckert — plateforme de détection des contrats en déshérence

Projet support du **Bloc 4** du titre RNCP 39586 *Ingénieur en science des
données spécialisé en infrastructure data* — spécialité Data Engineer.

## Le problème

Une mutuelle santé et prévoyance doit identifier ses adhérents décédés pour
traiter les contrats en déshérence. C'est une obligation légale (loi Eckert),
avec un risque de sanction et un enjeu de restitution des capitaux aux ayants
droit. La source de vérité externe est le **fichier des personnes décédées**
publié par l'INSEE sur data.gouv.fr.

Cette plateforme ingère ce fichier, le rapproche d'un référentiel adhérents et
produit la liste des contrats potentiellement concernés, avec un niveau de
confiance.

## Périmètre et honnêteté des données

Ce dépôt est une **reconstruction** menée sur un contexte métier réel, pas le
système d'information d'un assureur. Concrètement :

- le fichier des décès est la **vraie** donnée publique de l'INSEE ;
- le référentiel adhérents et contrats est **entièrement synthétique**, généré
  avec Faker ;
- aucune donnée d'entreprise ni donnée personnelle réelle d'assuré n'entre dans
  ce dépôt.

## Architecture

```
data.gouv.fr ──► Ingestion ──► MinIO (bronze) ──► Validation de contrat
   INSEE                                                │
                          ┌─────────────────────────────┤
                          ▼                             ▼
                  Spark (distribué)             Python/SQL (fil de l'eau)
                  rapprochement                 typage, dédoublonnage
                          └─────────────┬───────────────┘
                                        ▼
                        PostgreSQL — bronze / silver / gold / ops
                                        │
                                        ▼
                                Restitution métier

Orchestration : Airflow  ·  CI/CD : GitHub Actions  ·  Supervision : callbacks,
SLA, journal ops + alertes
```

| Couche | Contenu | Accès |
|---|---|---|
| `bronze` | ligne source telle que reçue, horodatée et tracée | pipeline seul |
| `silver` | données typées, nettoyées, dédoublonnées | pipeline seul |
| `gold` | contrats en déshérence, avec niveau de confiance | restitution métier |
| `ops` | journal d'exécution et contrôles qualité | supervision |

## Démarrage

```bash
cp infra/.env.example infra/.env       # puis renseigner les mots de passe
cd infra && docker compose --env-file .env up -d
```

| Service | URL | Rôle |
|---|---|---|
| Airflow | http://localhost:8080 | orchestration |
| MinIO | http://localhost:9001 | stockage objet (bronze) |
| Spark | http://localhost:8081 | calculs distribués |
| PostgreSQL | `localhost:5432/eckert` | entrepôt |

Générer le référentiel synthétique :

```bash
PYTHONPATH=src python -m eckert.referentiel.generate --adherents 50000
```

Lancer le cahier de recette automatisé :

```bash
PYTHONPATH=src pytest tests -v
```

## Structure

```
infra/          docker compose, Dockerfile, init PostgreSQL
dags/           DAG Airflow
src/eckert/     ingestion · validation · transform · referentiel · supervision
src/sql/        DDL des schémas, rôles et tables
tests/          tests unitaires, structurels et de sécurité
livrables/      les dix livrables du Bloc 4 (C4.1.1 → C4.4.2)
docs/           récits techniques, dont l'incident traité en C4.4.2
soutenance/     support projetable et préparation orale
```

## Documents clés

- [`CLAUDE.md`](CLAUDE.md) — cadrage du dossier, critères de la grille, rétroplanning
- [`docs/incident_metadonnees.md`](docs/incident_metadonnees.md) — l'incident de production traité en C4.4.2
- [`LIMITES.md`](LIMITES.md) — ce qui n'a pas été fait, et pourquoi
