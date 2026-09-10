"""
Ingestion du fichier des personnes décédées (INSEE) publié sur data.gouv.fr.

C4.2.2 — brique d'ingestion du pipeline.

Le catalogue data.gouv expose, pour chaque ressource, des métadonnées
déclarées : taille, empreinte, date de dernière modification. Ces métadonnées
sont récupérées et journalisées, mais elles ne sont PAS la seule source de
vérité pour valider le fichier : voir `eckert.validation.contract` et
docs/incident_metadonnees.md — c'est précisément la confiance aveugle dans ces
métadonnées qui a provoqué l'incident de production traité en C4.4.2.
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

import requests

from eckert.config import CONFIG

logger = logging.getLogger(__name__)

# Ressources annuelles : deces-2024.txt, deces-2023.txt, ...
RE_RESSOURCE_ANNUELLE = re.compile(r"deces[-_](?P<annee>(19|20)\d{2})\.txt", re.IGNORECASE)


@dataclass
class RessourceDeces:
    """Une ressource du catalogue, avec les métadonnées telles que déclarées."""

    titre: str
    url: str
    annee: int
    # Métadonnées DÉCLARÉES par le producteur. Peuvent être absentes ou fausses.
    taille_declaree: int | None = None
    empreinte_declaree: str | None = None
    type_empreinte: str | None = None
    derniere_modification: str | None = None

    @property
    def metadonnees_completes(self) -> bool:
        return self.taille_declaree is not None and self.empreinte_declaree is not None

    def anomalies_metadonnees(self) -> list[str]:
        manquant = []
        if self.taille_declaree is None:
            manquant.append("filesize")
        if self.empreinte_declaree is None:
            manquant.append("checksum")
        return manquant


@dataclass
class ResultatTelechargement:
    chemin: Path
    taille_reelle: int
    empreinte_reelle: str
    ressource: RessourceDeces
    ecarts: list[str] = field(default_factory=list)


def lister_ressources(annees: list[int] | None = None, timeout: int = 60) -> list[RessourceDeces]:
    """Interroge l'API data.gouv et retourne les ressources annuelles demandées."""
    reponse = requests.get(CONFIG.dataset_url, timeout=timeout)
    reponse.raise_for_status()
    donnees = reponse.json()

    ressources: list[RessourceDeces] = []
    for brut in donnees.get("resources", []):
        titre = (brut.get("title") or "").strip()
        correspondance = RE_RESSOURCE_ANNUELLE.search(titre) or RE_RESSOURCE_ANNUELLE.search(
            brut.get("url") or ""
        )
        if not correspondance:
            continue
        annee = int(correspondance.group("annee"))
        if annees and annee not in annees:
            continue

        empreinte = brut.get("checksum") or {}
        ressource = RessourceDeces(
            titre=titre or f"deces-{annee}.txt",
            url=brut["url"],
            annee=annee,
            taille_declaree=brut.get("filesize"),
            empreinte_declaree=empreinte.get("value") if isinstance(empreinte, dict) else None,
            type_empreinte=empreinte.get("type") if isinstance(empreinte, dict) else None,
            derniere_modification=brut.get("last_modified"),
        )
        if not ressource.metadonnees_completes:
            # Journalisé, mais NON bloquant : c'est le correctif de l'incident.
            logger.warning(
                "Métadonnées incomplètes pour %s (absentes : %s). "
                "La validation reposera sur le contenu du fichier.",
                ressource.titre,
                ", ".join(ressource.anomalies_metadonnees()),
            )
        ressources.append(ressource)

    ressources.sort(key=lambda r: r.annee, reverse=True)
    logger.info("%d ressource(s) annuelle(s) retenue(s)", len(ressources))
    return ressources


def telecharger(
    ressource: RessourceDeces, destination: Path, timeout: int = 300
) -> ResultatTelechargement:
    """Télécharge la ressource et calcule ses caractéristiques RÉELLES."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    sha256 = hashlib.sha256()
    taille = 0

    with requests.get(ressource.url, stream=True, timeout=timeout) as flux:
        flux.raise_for_status()
        with destination.open("wb") as sortie:
            for bloc in flux.iter_content(chunk_size=1024 * 1024):
                if not bloc:
                    continue
                sortie.write(bloc)
                sha256.update(bloc)
                taille += len(bloc)

    resultat = ResultatTelechargement(
        chemin=destination,
        taille_reelle=taille,
        empreinte_reelle=sha256.hexdigest(),
        ressource=ressource,
    )

    # Comparaison déclaré / réel : un écart est une ALERTE, pas un rejet.
    if ressource.taille_declaree is not None and ressource.taille_declaree != taille:
        resultat.ecarts.append(
            f"taille déclarée {ressource.taille_declaree} != taille réelle {taille}"
        )
    if (
        ressource.empreinte_declaree
        and (ressource.type_empreinte or "").lower() == "sha256"
        and ressource.empreinte_declaree.lower() != resultat.empreinte_reelle
    ):
        resultat.ecarts.append("empreinte sha256 déclarée différente de l'empreinte calculée")

    for ecart in resultat.ecarts:
        logger.warning("Écart métadonnées sur %s : %s", ressource.titre, ecart)

    logger.info("Téléchargé %s (%.1f Mo) vers %s", ressource.titre, taille / 1_048_576, destination)
    return resultat
