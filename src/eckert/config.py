"""Configuration centralisée, lue depuis l'environnement."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


@dataclass(frozen=True)
class Config:
    pg_dsn: str = _env("ELT_PG_DSN", "postgresql://elt_writer:changeme@localhost:5432/eckert")
    minio_endpoint: str = _env("MINIO_ENDPOINT", "http://localhost:9000")
    minio_bucket: str = _env("MINIO_BUCKET", "eckert-bronze")
    minio_user: str = _env("MINIO_ROOT_USER", "minioadmin")
    minio_password: str = _env("MINIO_ROOT_PASSWORD", "minioadmin")
    datagouv_api: str = _env("DATAGOUV_API", "https://www.data.gouv.fr/api/1/datasets")
    datagouv_dataset: str = _env("DATAGOUV_DATASET", "fichier-des-personnes-decedees")
    alert_webhook_url: str = _env("ALERT_WEBHOOK_URL", "")
    alert_email_to: str = _env("ALERT_EMAIL_TO", "")

    @property
    def dataset_url(self) -> str:
        return f"{self.datagouv_api}/{self.datagouv_dataset}/"


CONFIG = Config()
