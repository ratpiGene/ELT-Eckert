"""
Contrat de données du fichier des personnes décédées (INSEE).

C4.4.1 (tests structurels) et C4.4.2 (correctif de l'incident).

--- Contexte ---------------------------------------------------------------
La V1 du traitement validait la conformité du fichier reçu à partir des
MÉTADONNÉES DÉCLARÉES sur data.gouv (taille, empreinte). Quand le producteur a
cessé de publier ces métadonnées, la validation a rejeté tous les fichiers et le
traitement est tombé en erreur pendant plusieurs jours, alors que les fichiers
eux-mêmes étaient parfaitement exploitables.

La V2, implémentée ici, inverse la logique : la vérité est le CONTENU du
fichier. Les métadonnées déclarées ne servent plus qu'à lever une alerte
d'écart, jamais à bloquer. Voir docs/incident_metadonnees.md.
---------------------------------------------------------------------------
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

# Format à largeur fixe, 176 caractères. Positions 1-indexées de la spécification
# INSEE, converties ici en tranches Python (début, longueur).
# À revérifier à chaque évolution de la spécification publiée par le producteur.
CHAMPS: dict[str, tuple[int, int]] = {
    "nom_prenoms": (0, 80),
    "sexe": (80, 1),
    "date_naissance": (81, 8),
    "code_lieu_naissance": (89, 5),
    "commune_naissance": (94, 30),
    "pays_naissance": (124, 30),
    "date_deces": (154, 8),
    "code_lieu_deces": (162, 5),
    "numero_acte_deces": (167, 9),
}
LONGUEUR_LIGNE = 176

# Seuils de tolérance : un fichier réel n'est jamais parfait.
TAUX_REJET_MAX = 0.02  # au-delà, le fichier est refusé
LIGNES_MINIMUM = 1_000  # un fichier annuel plus petit est suspect


@dataclass
class RapportValidation:
    fichier: str
    lignes_lues: int = 0
    lignes_conformes: int = 0
    lignes_rejetees: int = 0
    erreurs: dict[str, int] = field(default_factory=dict)
    exemples_rejets: list[str] = field(default_factory=list)
    bloquant: list[str] = field(default_factory=list)
    alertes: list[str] = field(default_factory=list)

    @property
    def taux_rejet(self) -> float:
        return self.lignes_rejetees / self.lignes_lues if self.lignes_lues else 0.0

    @property
    def conforme(self) -> bool:
        return not self.bloquant

    def _compter(self, motif: str, ligne: str) -> None:
        self.erreurs[motif] = self.erreurs.get(motif, 0) + 1
        if len(self.exemples_rejets) < 5:
            self.exemples_rejets.append(f"[{motif}] {ligne[:60]}")

    def resume(self) -> str:
        etat = "CONFORME" if self.conforme else "NON CONFORME"
        return (
            f"{etat} — {self.fichier} : {self.lignes_lues} lignes lues, "
            f"{self.lignes_rejetees} rejetées ({self.taux_rejet:.2%})"
        )


def _date_valide(valeur: str) -> date | None:
    """Les dates INSEE sont en AAAAMMJJ, avec des mois ou jours à 00 quand ils
    sont inconnus. Un jour inconnu n'est pas une erreur : il est ramené au 1er."""
    valeur = valeur.strip()
    if len(valeur) != 8 or not valeur.isdigit():
        return None
    annee, mois, jour = int(valeur[:4]), int(valeur[4:6]), int(valeur[6:8])
    if not 1850 <= annee <= date.today().year:
        return None
    # Seul « 00 » signifie « inconnu » dans la spécification et se ramène au 1er.
    # Toute autre valeur hors bornes est une vraie anomalie et doit être rejetée.
    if mois == 0:
        mois = 1
    if jour == 0:
        jour = 1
    if not (1 <= mois <= 12) or not (1 <= jour <= 31):
        return None
    try:
        return date(annee, mois, jour)
    except ValueError:
        return None


def valider_fichier(chemin: Path, encodage: str = "utf-8") -> RapportValidation:
    """Valide la structure réelle du fichier, indépendamment de toute métadonnée."""
    rapport = RapportValidation(fichier=chemin.name)

    if not chemin.exists():
        rapport.bloquant.append("fichier absent")
        return rapport
    if chemin.stat().st_size == 0:
        rapport.bloquant.append("fichier vide")
        return rapport

    with chemin.open("r", encoding=encodage, errors="replace") as flux:
        for ligne in flux:
            ligne = ligne.rstrip("\n").rstrip("\r")
            if not ligne.strip():
                continue
            rapport.lignes_lues += 1

            if len(ligne) < LONGUEUR_LIGNE:
                rapport.lignes_rejetees += 1
                rapport._compter("longueur_insuffisante", ligne)
                continue

            debut, longueur = CHAMPS["date_deces"]
            if _date_valide(ligne[debut : debut + longueur]) is None:
                rapport.lignes_rejetees += 1
                rapport._compter("date_deces_invalide", ligne)
                continue

            debut, longueur = CHAMPS["sexe"]
            if ligne[debut : debut + longueur] not in ("1", "2"):
                rapport.lignes_rejetees += 1
                rapport._compter("sexe_invalide", ligne)
                continue

            rapport.lignes_conformes += 1

    # --- Règles bloquantes : elles portent toutes sur le CONTENU -----------
    if rapport.lignes_lues == 0:
        rapport.bloquant.append("aucune ligne exploitable")
    elif rapport.lignes_lues < LIGNES_MINIMUM:
        rapport.bloquant.append(
            f"volumétrie anormalement basse : {rapport.lignes_lues} lignes "
            f"(minimum attendu {LIGNES_MINIMUM})"
        )
    if rapport.taux_rejet > TAUX_REJET_MAX:
        rapport.bloquant.append(
            f"taux de rejet {rapport.taux_rejet:.2%} au-dessus du seuil {TAUX_REJET_MAX:.0%}"
        )

    logger.info(rapport.resume())
    return rapport


def controler_metadonnees(ecarts: list[str], metadonnees_absentes: list[str]) -> list[str]:
    """
    Traduit les écarts de métadonnées en ALERTES, jamais en blocages.

    C'est la ligne de code qui résume le correctif de l'incident : avant, ces
    mêmes constats levaient une exception et arrêtaient le traitement.
    """
    alertes = []
    if metadonnees_absentes:
        alertes.append(
            "Le producteur ne publie plus les métadonnées suivantes : "
            + ", ".join(metadonnees_absentes)
            + ". Validation assurée par le contenu du fichier."
        )
    alertes.extend(f"Écart déclaré/réel : {ecart}" for ecart in ecarts)
    return alertes
