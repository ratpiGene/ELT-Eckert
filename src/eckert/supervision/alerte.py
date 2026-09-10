"""
C4.3.1 — Supervision et système d'alertes.

Trois canaux, par ordre de gravité :
  - journal en base (ops.journal_execution) : trace systématique, exploitable
    par le tableau de bord de supervision ;
  - webhook : notification immédiate de l'équipe data en cas d'échec ;
  - courriel : escalade sur dépassement de SLA.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from eckert.config import CONFIG

logger = logging.getLogger(__name__)


def journaliser(
    run_id: str,
    etape: str,
    statut: str,
    lignes_lues: int | None = None,
    lignes_rejetees: int | None = None,
    duree_secondes: float | None = None,
    message: str | None = None,
) -> None:
    """Écrit une ligne dans ops.journal_execution."""
    import psycopg

    requete = """
        INSERT INTO ops.journal_execution
            (run_id, etape, statut, lignes_lues, lignes_rejetees, duree_secondes, message)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    try:
        with psycopg.connect(CONFIG.pg_dsn) as connexion:
            connexion.execute(
                requete,
                (run_id, etape, statut, lignes_lues, lignes_rejetees, duree_secondes, message),
            )
    except Exception:  # la supervision ne doit jamais faire tomber le traitement
        logger.exception("Journalisation impossible pour %s / %s", run_id, etape)


def _notifier(titre: str, corps: str) -> None:
    if not CONFIG.alert_webhook_url:
        logger.warning("ALERTE (webhook non configuré) — %s : %s", titre, corps)
        return
    try:
        requests.post(
            CONFIG.alert_webhook_url,
            json={"titre": titre, "corps": corps, "destinataire": CONFIG.alert_email_to},
            timeout=10,
        )
    except Exception:
        logger.exception("Envoi de l'alerte impossible")


def alerter_echec(contexte: dict[str, Any]) -> None:
    """Callback Airflow sur échec de tâche."""
    instance = contexte.get("task_instance")
    dag_id = getattr(instance, "dag_id", "?")
    tache = getattr(instance, "task_id", "?")
    essai = getattr(instance, "try_number", "?")
    run_id = contexte.get("run_id", "?")

    corps = (
        f"DAG {dag_id} — tâche {tache} en échec (tentative {essai}).\n"
        f"Exécution : {run_id}\n"
        f"Erreur : {contexte.get('exception')}\n"
        f"Journal : {getattr(instance, 'log_url', 'indisponible')}"
    )
    logger.error(corps)
    journaliser(run_id=str(run_id), etape=str(tache), statut="ECHEC", message=corps)
    _notifier(f"[ECKERT] Échec {dag_id}.{tache}", corps)


def alerter_sla(dag, task_list, blocking_tis, slas, blocking_tis_list) -> None:  # noqa: ANN001
    """Callback Airflow sur dépassement de SLA."""
    corps = f"Dépassement de SLA sur {getattr(dag, 'dag_id', '?')} : {task_list}"
    logger.warning(corps)
    _notifier("[ECKERT] Dépassement de SLA", corps)
