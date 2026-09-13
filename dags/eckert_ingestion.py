"""
C4.2.2 — Pipeline orchestré : ingestion mensuelle du fichier des décès.
C4.3.1 — Supervision : callbacks d'échec, SLA, journal d'exécution.

Chaîne : catalogue data.gouv → bronze (MinIO + Postgres) → validation de
contrat → silver. Le rapprochement distribué (Spark) fait l'objet d'un DAG
séparé, déclenché à la fin de celui-ci.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path

from airflow.decorators import dag, task
from airflow.exceptions import AirflowFailException

from eckert.ingestion.datagouv import lister_ressources, telecharger
from eckert.supervision.alerte import alerter_echec, alerter_sla, journaliser
from eckert.validation.contract import controler_metadonnees, valider_fichier

logger = logging.getLogger(__name__)

REPERTOIRE_TRAVAIL = Path("/opt/airflow/data/bronze")

ARGUMENTS_DEFAUT = {
    "owner": "data-eckert",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "on_failure_callback": alerter_echec,
    "execution_timeout": timedelta(hours=2),
}


@dag(
    dag_id="eckert_ingestion_deces",
    description="Ingestion et validation du fichier des personnes décédées (INSEE)",
    schedule="0 4 5 * *",  # le 5 de chaque mois à 4 h
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args=ARGUMENTS_DEFAUT,
    sla_miss_callback=alerter_sla,
    tags=["eckert", "bloc4", "ingestion"],
)
def eckert_ingestion_deces():
    @task(sla=timedelta(minutes=30))
    def recuperer_catalogue(**contexte) -> list[dict]:
        """Interroge data.gouv. Les métadonnées absentes alertent, ne bloquent pas."""
        annee_courante = datetime.now().year
        ressources = lister_ressources(annees=[annee_courante, annee_courante - 1])
        if not ressources:
            raise AirflowFailException(
                "Aucune ressource annuelle trouvée dans le catalogue data.gouv"
            )

        for ressource in ressources:
            absentes = ressource.anomalies_metadonnees()
            if absentes:
                for alerte in controler_metadonnees([], absentes):
                    logger.warning(alerte)
                    journaliser(
                        run_id=contexte["run_id"],
                        etape="recuperer_catalogue",
                        statut="ALERTE",
                        message=alerte,
                    )
        return [
            {
                "titre": r.titre,
                "url": r.url,
                "annee": r.annee,
                "taille_declaree": r.taille_declaree,
                "empreinte_declaree": r.empreinte_declaree,
                "type_empreinte": r.type_empreinte,
            }
            for r in ressources
        ]

    @task
    def telecharger_et_valider(ressources: list[dict], **contexte) -> list[str]:
        """Télécharge puis valide le CONTENU. Un fichier non conforme échoue ici."""
        from eckert.ingestion.datagouv import RessourceDeces
        from eckert.ingestion.stockage_objet import deposer

        fichiers_valides: list[str] = []
        for brut in ressources:
            ressource = RessourceDeces(**brut)
            destination = REPERTOIRE_TRAVAIL / f"{ressource.annee}" / ressource.titre
            resultat = telecharger(ressource, destination)

            # Couche bronze objet : on archive le fichier brut reçu (+ manifeste)
            # dans MinIO avant tout traitement — l'archive versionnée de la source.
            uri = deposer(
                resultat.chemin,
                cle=f"brut/{ressource.annee}/{ressource.titre}",
                run_id=contexte["run_id"],
            )
            journaliser(
                run_id=contexte["run_id"],
                etape=f"archive_minio_{ressource.annee}",
                statut="SUCCES",
                message=uri,
            )

            for alerte in controler_metadonnees(resultat.ecarts, ressource.anomalies_metadonnees()):
                journaliser(
                    run_id=contexte["run_id"],
                    etape="telecharger_et_valider",
                    statut="ALERTE",
                    message=alerte,
                )

            rapport = valider_fichier(resultat.chemin)
            journaliser(
                run_id=contexte["run_id"],
                etape=f"validation_{ressource.annee}",
                statut="SUCCES" if rapport.conforme else "ECHEC",
                lignes_lues=rapport.lignes_lues,
                lignes_rejetees=rapport.lignes_rejetees,
                message=rapport.resume(),
            )

            if not rapport.conforme:
                raise AirflowFailException(
                    f"Contrat de données non respecté sur {ressource.titre} : "
                    + " ; ".join(rapport.bloquant)
                )
            fichiers_valides.append(str(resultat.chemin))

        return fichiers_valides

    @task
    def charger_bronze(fichiers: list[str], **contexte) -> int:
        from eckert.transform.charge_bronze import charger

        total = sum(charger(Path(f), run_id=contexte["run_id"]) for f in fichiers)
        journaliser(
            run_id=contexte["run_id"],
            etape="charger_bronze",
            statut="SUCCES",
            lignes_lues=total,
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

    catalogue = recuperer_catalogue()
    fichiers = telecharger_et_valider(catalogue)
    bronze = charger_bronze(fichiers)
    promouvoir_silver(bronze)


eckert_ingestion_deces()
