"""
C4.3.1 — DÉMONSTRATION du système d'alertes.

Ce DAG contient une tâche qui échoue volontairement, sans retry, afin de
déclencher le `on_failure_callback` (alerter_echec). Celui-ci journalise
l'échec dans ops.journal_execution ET envoie une notification au webhook
configuré (ALERT_WEBHOOK_URL). Il sert uniquement à prouver que l'alerte est
réellement *délivrée* à son destinataire, pas seulement codée.

À déclencher manuellement, avec un récepteur de webhook à l'écoute
(cf. tools/webhook_receiver.py).
"""

from __future__ import annotations

from datetime import datetime

from airflow.decorators import dag, task
from airflow.exceptions import AirflowFailException

from eckert.supervision.alerte import alerter_echec

ARGUMENTS_DEFAUT = {
    "owner": "data-eckert",
    "retries": 0,  # échec immédiat : on veut déclencher l'alerte sans attendre
    "on_failure_callback": alerter_echec,
}


@dag(
    dag_id="eckert_demo_alerte",
    description="Démonstration d'alerte : échec provoqué -> notification au webhook",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=ARGUMENTS_DEFAUT,
    tags=["eckert", "bloc4", "demo", "supervision"],
)
def eckert_demo_alerte():
    @task
    def echec_provoque() -> None:
        # Simule une panne de traitement (ex. entrepôt injoignable à 3 h du matin).
        raise AirflowFailException(
            "Échec provoqué pour démonstration du système d'alertes (C4.3.1)."
        )

    echec_provoque()


eckert_demo_alerte()
