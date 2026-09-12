"""
Génère le support projetable de la soutenance (soutenance/support_eckert.pptx).

Format 30 minutes : 17 diapositives projetées + 3 annexes masquées. Titres
assertifs, bandeau de compétence, ≤ 5 lignes projetées, captures réelles
intégrées, et notes de commentaire (le texte À LIRE) resserrées pour tenir
dans ~1,7 min par diapo. Voir soutenance/support_plan.md.

    PYTHONPATH=. python -m tools.build_pptx
"""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Emu, Pt

RACINE = Path(__file__).resolve().parents[1]
PREUVES = RACINE / "preuves"
SORTIE = RACINE / "soutenance" / "support_eckert.pptx"

LARGEUR = Emu(12192000)  # 16:9
HAUTEUR = Emu(6858000)

BLEU = RGBColor(0x0B, 0x3D, 0x66)
GRIS = RGBColor(0x40, 0x40, 0x40)
GRIS_CLAIR = RGBColor(0xE8, 0xEC, 0xF0)
BLANC = RGBColor(0xFF, 0xFF, 0xFF)
ACCENT = RGBColor(0xC0, 0x39, 0x2B)


def _txt(cadre, texte, taille, gras=False, couleur=BLEU, align=PP_ALIGN.LEFT):
    cadre.text = texte
    p = cadre.paragraphs[0]
    p.alignment = align
    r = p.runs[0]
    r.font.size = Pt(taille)
    r.font.bold = gras
    r.font.color.rgb = couleur
    r.font.name = "Calibri"


def _bandeau(slide, comp):
    if not comp:
        return
    box = slide.shapes.add_textbox(Emu(10000000), Emu(180000), Emu(1950000), Emu(520000))
    box.fill.solid()
    box.fill.fore_color.rgb = ACCENT
    box.line.fill.background()
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    _txt(tf, comp, 16, gras=True, couleur=BLANC, align=PP_ALIGN.CENTER)


def _titre(slide, titre):
    box = slide.shapes.add_textbox(Emu(500000), Emu(300000), Emu(9200000), Emu(1150000))
    tf = box.text_frame
    tf.word_wrap = True
    _txt(tf, titre, 29, gras=True, couleur=BLEU)


def _puces(slide, lignes, largeur, gauche=Emu(600000), haut=Emu(1650000),
           hauteur=Emu(4600000), taille=20):
    box = slide.shapes.add_textbox(gauche, haut, largeur, hauteur)
    tf = box.text_frame
    tf.word_wrap = True
    for i, ligne in enumerate(lignes):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = "•  " + ligne
        p.space_after = Pt(10)
        for r in p.runs:
            r.font.size = Pt(taille)
            r.font.color.rgb = GRIS
            r.font.name = "Calibri"


def _image(slide, chemin, gauche, haut, largeur):
    if chemin and Path(chemin).exists():
        slide.shapes.add_picture(str(chemin), gauche, haut, width=largeur)


def _notes(slide, texte):
    slide.notes_slide.notes_text_frame.text = texte


def _cacher(slide):
    slide._element.set("show", "0")  # masquée en diaporama, dispo pour les questions


def titre_slide(prs, titre, sous_titre, notes):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    fond = s.shapes.add_textbox(0, 0, LARGEUR, HAUTEUR)
    fond.fill.solid(); fond.fill.fore_color.rgb = BLEU; fond.line.fill.background()
    t = s.shapes.add_textbox(Emu(700000), Emu(2300000), Emu(10800000), Emu(1500000))
    _txt(t.text_frame, titre, 34, gras=True, couleur=BLANC); t.text_frame.word_wrap = True
    st = s.shapes.add_textbox(Emu(700000), Emu(3900000), Emu(10800000), Emu(1000000))
    _txt(st.text_frame, sous_titre, 22, couleur=GRIS_CLAIR); st.text_frame.word_wrap = True
    _notes(s, notes)
    return s


def contenu(prs, titre, comp, puces, notes, image=None, cache=False):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _titre(s, titre)
    _bandeau(s, comp)
    if image and Path(image).exists():
        _puces(s, puces, largeur=Emu(11000000), haut=Emu(1500000), hauteur=Emu(1250000), taille=17)
        _image(s, image, Emu(1400000), Emu(2850000), Emu(9400000))
    else:
        _puces(s, puces, largeur=Emu(11000000), taille=21)
    _notes(s, notes)
    if cache:
        _cacher(s)
    return s


def construire() -> Path:
    prs = Presentation()
    prs.slide_width = LARGEUR
    prs.slide_height = HAUTEUR

    # 1 — Titre
    titre_slide(
        prs,
        "Plateforme ELT Eckert — détecter les contrats en déshérence",
        "Bloc 4 · Spécialité Data Engineer · RNCP 39586",
        "Bonjour. En 30 minutes, je vous présente une plateforme data que j'ai conçue et opérée "
        "pour répondre à l'obligation loi Eckert, puis je réponds à vos questions.",
    )

    # 2 — Contexte
    contenu(
        prs, "Une obligation légale : identifier les adhérents décédés", "Contexte",
        ["Loi Eckert : traiter les contrats non réglés au décès",
         "Risque de sanction ACPR + restitution aux ayants droit",
         "Source de vérité : fichier des décès de l'INSEE (data.gouv.fr)"],
        "Une mutuelle doit repérer ses adhérents décédés pour verser les capitaux des contrats "
        "en déshérence. C'est une obligation légale — la loi Eckert — sous risque de sanction. "
        "La source de vérité, c'est le fichier des décès de l'INSEE.",
    )

    # 3 — Périmètre honnête
    contenu(
        prs, "Une plateforme reconstruite sur un contexte réel — et mon rôle", "Contexte",
        ["Contexte métier réel vécu en alternance (Prévifrance)",
         "Plateforme entièrement RECONSTRUITE pour ce dossier",
         "Fichier INSEE réel · référentiel adhérents synthétique (Faker)",
         "J'ai vécu en production l'ingestion Eckert et l'incident"],
        "Point d'honnêteté important : j'ai reconstruit entièrement cette plateforme, sur un "
        "contexte réel. Ce n'est pas le SI de l'entreprise. Le fichier décès est la vraie donnée "
        "publique, mais le référentiel adhérents est synthétique, généré avec Faker : aucune "
        "donnée personnelle réelle. J'ai vécu l'ingestion Eckert en production, et l'incident que "
        "je rejouerai à la fin.",
    )

    # 4 — C4.1.1
    contenu(
        prs, "Analyse : besoins, contraintes, et les quatre trous à combler", "C4.1.1",
        ["Besoin : une donnée actionnable, fiable, tracée, au rythme mensuel",
         "Contraintes : coût nul · délai < 1 mois · forte volumétrie",
         "Existant : SQL Server, SSRS, un traitement Eckert sous Airflow",
         "Trous sans matériau : Spark, CI/CD, alerting, tests de sécurité"],
        "Trois contraintes cadrent tout : coût nul, donc tout en local ; délai court, donc chaque "
        "brique démontrable en cinq minutes ; et une forte volumétrie. L'existant couvrait SQL "
        "Server et un Airflow. Mais quatre compétences n'avaient aucun matériau : le distribué, "
        "la CI/CD, l'alerting et les tests de sécurité. Ce sont mes priorités.",
    )

    # 5 — C4.1.2 composants
    contenu(
        prs, "Des composants open source, locaux, portables vers le cloud", "C4.1.2",
        ["Airflow · PostgreSQL · MinIO (S3) · Spark · GitHub Actions",
         "Interfaces standard : S3, SQL, PySpark",
         "Vendor lock-in traité par conception (bascule cloud sans réécriture)"],
        "J'ai retenu cinq briques open source. Toutes exposent des interfaces standard — S3, SQL, "
        "PySpark — ce qui traite le vendor lock-in par conception : je peux basculer vers le cloud "
        "sans réécriture majeure.",
    )

    # 6 — C4.1.2 coûts
    contenu(
        prs, "Trois scénarios de coût, avec des hypothèses explicites", "C4.1.2",
        ["Local (retenu) : ~ coût du temps humain seul",
         "Cloud Azure : ~ 50 à 145 € / mois",
         "SaaS Snowflake/Fabric : ~ 80 à 250 € / mois",
         "SaaS écarté (réel) : coût récurrent + souveraineté des données"],
        "Sur le coût, j'ai chiffré trois scénarios avec des hypothèses assumées. Le local coûte "
        "surtout du temps humain ; Azure, 50 à 145 € par mois ; le SaaS, 80 à 250. Dans le "
        "contexte réel, le SaaS a été écarté pour son coût récurrent et la souveraineté des "
        "données de santé. Le jury attend une méthode de chiffrage, pas un devis exact.",
    )

    # 7 — C4.2.1
    contenu(
        prs, "Un entrepôt en quatre couches, avec des droits testés", "C4.2.1",
        ["bronze (brut) · silver (typé) · gold (métier) · ops (journal)",
         "Deux rôles : le pipeline écrit, le métier lit gold seulement",
         "Le rôle lecture ne peut ni écrire ni lire le brut — TESTÉ",
         "Le métier consomme une vue déjà priorisée"],
        "L'entrepôt est en quatre couches : le brut, le nettoyé, le métier, le journal. Deux rôles "
        "appliquent le moindre privilège. Et je le prouve par des tests : le rôle lecture ne peut "
        "ni écrire, ni lire le brut. Le métier consomme une vue déjà priorisée par niveau de "
        "confiance.",
    )

    # 8 — C4.2.2 les 3 méthodes
    contenu(
        prs, "Trois méthodes de pipeline, dont le distribué", "C4.2.2",
        ["Fil de l'eau (SQL) : typage, nettoyage, déduplication dans le moteur",
         "Orchestration (Airflow) : enchaîne et fiabilise",
         "Distribué (Spark) : absorbe le volume du rapprochement",
         "Chaque méthode produit une donnée demandée"],
        "La compétence pipelines exige trois méthodes. Le fil de l'eau, en SQL, nettoie et "
        "dédoublonne au plus près de la donnée. L'orchestration Airflow enchaîne et fiabilise. Et "
        "le distribué, avec Spark, absorbe le volume du rapprochement. Les trois tournent.",
    )

    # 9 — C4.2.2 orchestration (capture)
    contenu(
        prs, "Orchestration : le DAG réel tourne vert sur le fichier INSEE", "C4.2.2",
        ["4 tâches · retries · SLA · callbacks d'alerte · exécution réelle data.gouv"],
        "Voici le DAG réel : quatre tâches, de la récupération du catalogue à la promotion silver, "
        "avec retries, SLA et callbacks. Il tourne au vert sur le vrai fichier INSEE téléchargé "
        "depuis data.gouv.",
        image=PREUVES / "C4-2-2_airflow_run.png",
    )

    # 10 — C4.2.2 distribué (capture)
    contenu(
        prs, "Distribué : Spark détecte 4 162 contrats, 88 M€ en CERTAIN", "C4.2.2",
        ["Rapprochement sur cluster · 3 niveaux CERTAIN / PROBABLE / A_VERIFIER · app FINISHED"],
        "Le rapprochement tourne sur un cluster Spark et gradue la confiance en trois niveaux, "
        "faute d'identifiant national. Résultat : 4 162 contrats potentiellement en déshérence, "
        "dont 88 millions d'euros en niveau certain. Sur le seul volume mensuel, un Postgres "
        "indexé suffirait — je l'assume ; Spark se justifie par la volumétrie cumulée et la "
        "trajectoire de croissance.",
        image=PREUVES / "C4-2-2_spark_ui.png",
    )

    # 11 — C4.2.3 (capture)
    contenu(
        prs, "CI/CD : cinq jobs verts et un déploiement réel sur registre", "C4.2.3",
        ["Qualité · tests · sécurité · validation DAG · déploiement (image sur GHCR)"],
        "La CI/CD, construite de zéro, enchaîne cinq contrôles à chaque push : qualité, tests, "
        "scan de sécurité, validation des DAG, et déploiement. Le déploiement est réel : l'image "
        "est publiée sur le registre GitHub, puis re-téléchargée et testée. Détail assumé : mon "
        "premier run était rouge — la preuve que les garde-fous mordent.",
        image=PREUVES / "C4-2-3_ci_run_vert.png",
    )

    # 12 — C4.3.1 (capture)
    contenu(
        prs, "Supervision : indicateurs, seuils, et une alerte réellement délivrée", "C4.3.1",
        ["Statut · SLA · taux de rejet · journal ops · webhook reçu · escalade courriel"],
        "La supervision surveille le statut, les SLA et surtout le taux de rejet. Chaque étape est "
        "journalisée. Sur échec, une alerte part vraiment : j'ai capturé la notification reçue par "
        "le destinataire, avec le lien vers le journal. Un dépassement de délai escalade par "
        "courriel.",
        image=PREUVES / "C4-3-1_airflow_eventlog.png",
    )

    # 13 — C4.3.2 / 3.3
    contenu(
        prs, "Exploitation : un calendrier de MCO et une doc réutilisable", "C4.3.2 · C4.3.3",
        ["Cycles mensuel → annuel · rotation des secrets et des certificats",
         "Runbook des incidents courants (DAG, Spark, reset)",
         "Un successeur reprend sans moi"],
        "Une feuille de route calendaire cadre la maintenance : rotation des secrets au trimestre, "
        "certificats au semestre. Et une documentation avec runbook permet à un successeur de "
        "reprendre sans moi — d'ailleurs c'est cette procédure qui a servi à monter la plateforme.",
    )

    # 14 — C4.4.1
    contenu(
        prs, "Une recette automatisée : 19 tests, dont la sécurité", "C4.4.1",
        ["Tests fonctionnels, structurels ET de sécurité",
         "Droits · non-exposition des secrets · scan de dépendances",
         "Rejouée à chaque push : un filet permanent, pas un instantané"],
        "La recette est automatisée : dix-neuf tests fonctionnels, structurels et de sécurité — "
        "les droits, les secrets, les dépendances. Elle est rejouée à chaque push. Ce n'est pas un "
        "instantané, c'est un filet permanent. Je peux la lancer en direct : elle passe en moins "
        "d'une seconde.",
    )

    # 15 — C4.4.2 incident (moment fort)
    contenu(
        prs, "L'incident : la confiance aveugle dans les métadonnées déclarées", "C4.4.2",
        ["La V1 validait le fichier sur la taille et l'empreinte ANNONCÉES",
         "Le producteur cesse de les publier → rejet systématique",
         "Fichiers pourtant parfaitement exploitables · échec quotidien"],
        "Voici l'incident, vécu en production. Le contrôle d'entrée validait le fichier sur ses "
        "métadonnées déclarées : taille et empreinte annoncées. Après deux mois nominaux, le "
        "producteur a cessé de les publier. Résultat : rejet systématique, traitement en erreur "
        "chaque jour — alors que les fichiers étaient parfaitement exploitables. La cause n'est "
        "pas triviale : le contrat de données change sans préavis, côté producteur.",
    )

    # 16 — C4.4.2 correctif
    contenu(
        prs, "Le correctif : valider le contenu, pas la promesse — rejeu vert", "C4.4.2",
        ["Métadonnées → simple alerte ; le CONTENU devient la seule vérité",
         "Fichier sain sans métadonnées : CONFORME · corrompu : bloqué",
         "Test de non-régression : l'incident ne peut plus revenir en silence"],
        "Le correctif inverse la logique : les métadonnées ne font qu'alerter, la vérité c'est le "
        "contenu — structure, volumétrie, taux de rejet. Un fichier sain sans métadonnées passe "
        "désormais ; un fichier corrompu reste bloqué. Un test de non-régression verrouille le "
        "cas. Je peux rejouer l'avant/après en direct, en moins d'une seconde. La leçon : une "
        "source externe n'est jamais un contrat.",
    )

    # 17 — Bilan
    contenu(
        prs, "Bilan : ce qui tourne, les limites assumées", "Bilan",
        ["Chaîne complète prouvée : ingestion → Spark → gold → restitution",
         "Sécurité testée · CI verte · incident rejoué",
         "Limites : Postgres unique · Spark lancé manuellement · pas de supervision infra",
         "À poursuivre : déclenchement Spark par Airflow, supervision d'infra"],
        "En bilan : la chaîne complète tourne et est prouvée, la sécurité est testée, la CI est "
        "verte, l'incident est rejoué. J'assume mes limites : une seule instance Postgres, le job "
        "Spark lancé manuellement, pas de supervision d'infrastructure. Si je continuais, "
        "j'outillerais le déclenchement Spark par Airflow et une supervision infra. Merci — je "
        "suis prêt pour vos questions.",
    )

    # Annexes masquées
    contenu(prs, "A1 — Schéma de l'entrepôt : couches, tables, rôles", "Annexe",
            ["4 schémas · 6 tables · 2 rôles · 1 vue", "Preuve : C4-2-1_schema_postgres.txt"],
            "Annexe ouverte si le jury creuse l'entrepôt.", cache=True)
    contenu(prs, "A2 — Estimation des coûts détaillée (3 scénarios)", "Annexe",
            ["Hypothèses de volumétrie explicites", "Comparatif local / Azure / SaaS"],
            "Annexe ouverte sur une question de coût ou de lock-in.", cache=True)
    contenu(prs, "A3 — Workflow CI/CD complet (5 jobs)", "Annexe",
            [".github/workflows/ci.yml", "Qualité, tests, sécurité, DAG, déploiement GHCR"],
            "Annexe ouverte sur une question CI/CD ou déploiement.", cache=True)

    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(SORTIE))
    return SORTIE


if __name__ == "__main__":
    chemin = construire()
    prs = Presentation(str(chemin))
    total = len(prs.slides._sldIdLst)
    caches = sum(1 for s in prs.slides if s._element.get("show") == "0")
    print(f"Support généré : {chemin}")
    print(f"  {total} diapositives ({total - caches} projetées + {caches} annexes masquées)")
