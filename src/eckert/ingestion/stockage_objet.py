"""
C4.2.1 / C4.2.2 — Couche bronze « stockage objet » (MinIO, S3-compatible).

Rôle de MinIO dans le flux : archiver le **fichier brut reçu**, tel quel, avec un
**manifeste** (taille et empreinte réelles, provenance). C'est l'archive
immuable et versionnée des fichiers d'entrée — distincte du bronze PostgreSQL,
qui, lui, contient les *lignes* parsées.

Pourquoi les deux ? Le fichier objet garantit la rejouabilité (on peut recharger
depuis la source exacte reçue) ; la table relationnelle sert le traitement SQL.
MinIO expose une API S3 : la bascule vers un stockage objet cloud se ferait sans
réécriture.
"""

from __future__ import annotations

import io
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from eckert.config import CONFIG

logger = logging.getLogger(__name__)


def _client():
    import boto3
    from botocore.client import Config

    return boto3.client(
        "s3",
        endpoint_url=CONFIG.minio_endpoint,
        aws_access_key_id=CONFIG.minio_user,
        aws_secret_access_key=CONFIG.minio_password,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def _assurer_bucket(client) -> None:
    from botocore.exceptions import ClientError

    try:
        client.head_bucket(Bucket=CONFIG.minio_bucket)
    except ClientError:
        client.create_bucket(Bucket=CONFIG.minio_bucket)


def deposer(chemin: Path, cle: str | None = None, run_id: str | None = None) -> str:
    """Dépose le fichier brut dans MinIO et écrit son manifeste. Retourne l'URI s3."""
    chemin = Path(chemin)
    cle = cle or f"brut/{chemin.name}"
    taille = chemin.stat().st_size

    client = _client()
    _assurer_bucket(client)
    client.upload_file(
        str(chemin),
        CONFIG.minio_bucket,
        cle,
        ExtraArgs={"Metadata": {"run_id": run_id or "", "depose_le": _horodatage()}},
    )

    manifeste = {
        "cle": cle,
        "fichier": chemin.name,
        "taille_octets": taille,
        "run_id": run_id,
        "depose_le": _horodatage(),
    }
    client.put_object(
        Bucket=CONFIG.minio_bucket,
        Key=f"{cle}.manifest.json",
        Body=io.BytesIO(json.dumps(manifeste, ensure_ascii=False, indent=2).encode("utf-8")),
        ContentType="application/json",
    )

    uri = f"s3://{CONFIG.minio_bucket}/{cle}"
    logger.info("Fichier brut archivé dans MinIO : %s (%d octets)", uri, taille)
    return uri


def _horodatage() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")
