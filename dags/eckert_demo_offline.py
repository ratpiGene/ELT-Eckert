"""
C4.2.2 / C4.3.1 — DAG de DÉMONSTRATION, hors-ligne.

Objectif : donner une exécution Airflow verte, rapide et reproductible, sans
dépendre du téléchargement du fichier réel INSEE. Il rejoue le traitement au fil
de l'eau sur le fichier décès de démonstration déjà présent
(data/bronze/demo/deces-demo.txt), l'enchaînement bronze → silver, et journalise
chaque étape dans ops.journal_execution.

Le DAG de production reste `eckert_ingestion_deces` (ingestion réelle depuis
data.gouv). Celui-ci est explicitement étiqueté « demo ».
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from airflow.decorators import dag, task
from airflow.exceptions import AirflowFailException

from eckert.supervision.alerte import alerter_echec, journaliser

FICHIER_DEMO = Path("/opt/airflow/data/bronze/demo/deces-demo.txt")

ARGUMENTS_DEFAUT = {
    "owner": "data-eckert",
    "retries": 1,
    "retry_delay": timedelta(seconds=30),
    "on_failure_callback": alerter_echec,
}


@dag(
    dag_id="eckert_demo_offline",
    description="Démonstration hors-ligne : fichier décès de démo → bronze → silver",
    schedule=None,  # déclenchement manuel
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=ARGUMENTS_DEFAUT,
    tags=["eckert", "bloc4", "demo"],
)
def eckert_demo_offline():
    @task
    def archiver_minio(**contexte) -> str:
        """Dépose le fichier brut reçu dans MinIO (couche bronze objet) + manifeste."""
        from eckert.ingestion.stockage_objet import deposer

        if not FICHIER_DEMO.exists():
            raise AirflowFailException(f"Fichier de démonstration absent : {FICHIER_DEMO}.")
        uri = deposer(
            FICHIER_DEMO,
            cle=f"brut/demo/{contexte['run_id']}/{FICHIER_DEMO.name}",
            run_id=contexte["run_id"],
        )
        journaliser(run_id=contexte["run_id"], etape="archiver_minio", statut="SUCCES", message=uri)
        return uri

    @task
    def charger_bronze(**contexte) -> int:
        from eckert.transform.charge_bronze import charger

        if not FICHIER_DEMO.exists():
            raise AirflowFailException(
                f"Fichier de démonstration absent : {FICHIER_DEMO}. "
                "Générer avec eckert.referentiel.scenario_deces."
            )
        total = charger(FICHIER_DEMO, run_id=contexte["run_id"])
        journaliser(
            run_id=contexte["run_id"],
            etape="charger_bronze",
            statut="SUCCES",
            lignes_lues=total,
            message=f"démonstration hors-ligne : {FICHIER_DEMO.name}",
        )
        return total

    @task
    def promouvoir_silver(lignes_bronze: int, **contexte) -> int:
        from eckert.transform.bronze_vers_silver import promouvoir

        total = promouvoir(run_id=contexte["run_id"])
        journaliser(
            run_id=contexte["run_id"],
            etape="promouvoir_silver",
            statut="SUCCES",
            lignes_lues=total,
            message=f"{lignes_bronze} lignes bronze traitées",
        )
        return total

    archive = archiver_minio()
    bronze = charger_bronze()
    archive >> bronze
    promouvoir_silver(bronze)


eckert_demo_offline()
