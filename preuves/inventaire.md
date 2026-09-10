# Inventaire des preuves

Une preuve par critère, rattachée à sa compétence. Deux natures :

- **[texte]** — export/log déjà capturé et versionné dans ce dossier (reproductible) ;
- **[capture]** — capture d'écran à prendre dans l'interface (Airflow, Spark UI, MinIO,
  GitHub Actions). La plateforme tourne : chaque capture se prend en moins de 5 minutes.

> Convention de nommage : `C4-x-y_sujet.ext`.

## État des preuves

| Compétence | Preuve | Fichier | État |
|---|---|---|---|
| C4.1.1 | Analyse (besoins, contraintes, existant) | `livrables/C4-1-1_rapport_analyse.md` | ✅ rédigé |
| C4.1.2 | Composants + estimation des coûts | `livrables/C4-1-2_composants_architecture.md` | ✅ rédigé |
| C4.2.1 | Schémas, rôles, tables de l'entrepôt | `preuves/C4-2-1_schema_postgres.txt` | ✅ [texte] |
| C4.2.1 | Restitution métier lue par `elt_reader` | `preuves/C4-2-1_vue_restitution.txt` | ✅ [texte] |
| C4.2.2 | Résultats gold par niveau de confiance | `preuves/C4-2-2_gold_par_confiance.txt` | ✅ [texte] |
| C4.2.2 | Exécution du job Spark (cluster) | `preuves/C4-2-2_spark_execution.txt` | ✅ [texte] |
| C4.2.2 | Spark UI (application `eckert-rapprochement` FINISHED) | `preuves/C4-2-2_spark_ui.png` | ✅ [capture] |
| C4.2.2 | DAG Airflow démo (exécution verte) | `preuves/C4-2-2_airflow_demo_vert.png` | ⏳ [capture] Grid de `eckert_demo_offline` |
| C4.2.2 | Fil de l'eau bronze → silver (compteurs) | `preuves/C4-2-2_bronze_silver.txt` | ✅ [texte] |
| C4.2.3 | CI/CD verte (jobs) | `preuves/C4-2-3_ci_jobs.txt` | ✅ [texte] |
| C4.2.3 | CI/CD verte (capture, run #4 Success) | `preuves/C4-2-3_ci_run_vert.png` | ✅ [capture] |
| C4.2.3 | Scan de dépendances | `preuves/C4-2-3_pip_audit.txt` | ✅ [texte] |
| C4.3.1 | Airflow Grid view | `preuves/C4-3-1_airflow_grid.png` | ⏳ [capture] |
| C4.3.1 | Journal d'exécution `ops` | `preuves/C4-3-1_journal_ops.txt` | ✅ [texte] |
| C4.3.1 | Alerte sur échec provoqué | `preuves/C4-3-1_alerte_echec.png` | ⏳ [capture] |
| C4.4.1 | Cahier de recette exécuté (19 tests) | `preuves/C4-4-1_recette_complete.txt` | ✅ [texte] |
| C4.4.1 | Tests de sécurité (base réelle) | `preuves/C4-4-1_tests_securite.txt` | ✅ [texte] |
| C4.4.2 | Rejeu de l'incident (avant/après) | `preuves/C4-4-2_incident_rejeu.txt` | ✅ [texte] |

## Captures restantes à prendre (checklist)

La plateforme est démarrée (`docker compose ps` → tous `Up`). Ordre suggéré :

1. **Airflow** http://localhost:8080 → DAG `eckert_ingestion_deces` : vue *Graph* puis *Grid*
   après un déclenchement manuel (`C4-2-2_airflow_dag.png`, `C4-2-2_airflow_run.png`,
   `C4-3-1_airflow_grid.png`).
2. **Spark UI** http://localhost:8081 → onglet *Completed Applications* : l'app
   `eckert-rapprochement-*` (`C4-2-2_spark_ui.png`).
3. **MinIO** http://localhost:9001 → bucket `eckert-bronze` versionné (`C4-2-1_minio_bronze.png`,
   optionnel).
4. **GitHub Actions** → dernier run vert des 5 jobs (`C4-2-3_ci_run_vert.png`).

## Preuves texte encore à générer (commandes)

```bash
# C4-2-2_bronze_silver.txt : compteurs de la promotion fil de l'eau
docker exec eckert-postgres psql -U postgres -d eckert \
  -c "SELECT etape, statut, lignes_lues FROM ops.journal_execution ORDER BY horodatage;"

# C4-3-1_journal_ops.txt : journal de supervision
docker exec eckert-postgres psql -U postgres -d eckert \
  -c "SELECT run_id, etape, statut, lignes_lues, lignes_rejetees FROM ops.journal_execution;"
```
