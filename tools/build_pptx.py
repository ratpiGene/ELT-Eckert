"""
Génère le support projetable de la soutenance (soutenance/support_eckert.pptx)
à partir du plan (soutenance/support_plan.md).

37 diapositives : titres assertifs, bandeau de compétence, ≤ 5 lignes projetées,
captures réelles intégrées sur les diapos de démonstration, et notes de
commentaire (ce qui se dit) dans chaque diapo.

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

# 16:9
LARGEUR = Emu(12192000)
HAUTEUR = Emu(6858000)

BLEU = RGBColor(0x0B, 0x3D, 0x66)
GRIS = RGBColor(0x5A, 0x5A, 0x5A)
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
    box = slide.shapes.add_textbox(Emu(10000000), Emu(180000), Emu(1900000), Emu(500000))
    tf = box.text_frame
    tf.word_wrap = True
    _txt(tf, comp, 16, gras=True, couleur=BLANC, align=PP_ALIGN.CENTER)
    box.fill.solid()
    box.fill.fore_color.rgb = ACCENT
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE


def _titre(slide, titre):
    box = slide.shapes.add_textbox(Emu(500000), Emu(300000), Emu(9200000), Emu(1100000))
    tf = box.text_frame
    tf.word_wrap = True
    _txt(tf, titre, 30, gras=True, couleur=BLEU)


def _puces(slide, lignes, largeur=Emu(11000000), gauche=Emu(600000), haut=Emu(1600000),
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


def diviseur(prs, titre, sous_titre):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    fond = slide.shapes.add_textbox(0, 0, LARGEUR, HAUTEUR)
    fond.fill.solid()
    fond.fill.fore_color.rgb = BLEU
    fond.line.fill.background()
    b1 = slide.shapes.add_textbox(Emu(700000), Emu(2600000), Emu(10800000), Emu(1200000))
    _txt(b1.text_frame, titre, 40, gras=True, couleur=BLANC)
    b1.text_frame.word_wrap = True
    b2 = slide.shapes.add_textbox(Emu(700000), Emu(3900000), Emu(10800000), Emu(800000))
    _txt(b2.text_frame, sous_titre, 22, couleur=GRIS_CLAIR)
    b2.text_frame.word_wrap = True
    return slide


def contenu(prs, titre, comp, puces, notes, image=None, image_pleine=False):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _titre(slide, titre)
    _bandeau(slide, comp)
    if image and Path(image).exists():
        if image_pleine:
            _puces(slide, puces, largeur=Emu(11000000), haut=Emu(1500000), hauteur=Emu(1300000),
                   taille=18)
            _image(slide, image, Emu(1200000), Emu(2900000), Emu(9800000))
        else:
            _puces(slide, puces, largeur=Emu(5400000), haut=Emu(1600000), taille=18)
            _image(slide, image, Emu(6300000), Emu(1700000), Emu(5500000))
    else:
        _puces(slide, puces, taille=20)
    _notes(slide, notes)
    return slide


def construire() -> Path:
    prs = Presentation()
    prs.slide_width = LARGEUR
    prs.slide_height = HAUTEUR

    # ---- Titre --------------------------------------------------------------
    s = prs.slides.add_slide(prs.slide_layouts[6])
    fond = s.shapes.add_textbox(0, 0, LARGEUR, HAUTEUR)
    fond.fill.solid(); fond.fill.fore_color.rgb = BLEU; fond.line.fill.background()
    t = s.shapes.add_textbox(Emu(700000), Emu(2300000), Emu(10800000), Emu(1500000))
    _txt(t.text_frame, "Plateforme ELT Eckert — détection des contrats en déshérence",
         34, gras=True, couleur=BLANC)
    t.text_frame.word_wrap = True
    st = s.shapes.add_textbox(Emu(700000), Emu(3900000), Emu(10800000), Emu(1000000))
    _txt(st.text_frame, "Bloc 4 — Spécialité Data Engineer — RNCP 39586", 22, couleur=GRIS_CLAIR)
    _notes(s, "Se présenter en 20 s. Annoncer : obligation Eckert, plateforme data conçue et "
              "opérée, périmètre honnête. 45 min + 15 min de questions.")

    # ---- 0-4 min Contexte ---------------------------------------------------
    contenu(prs, "Une obligation légale : identifier les adhérents décédés", "Contexte",
            ["Loi Eckert : contrats non réglés au décès du souscripteur",
             "Risque de sanction ACPR + enjeu de restitution aux ayants droit",
             "Source de vérité : fichier des décès de l'INSEE (data.gouv.fr)"],
            "Poser l'enjeu réglementaire en 30 s : une mutuelle doit rechercher ses assurés "
            "décédés et reverser les capitaux non réclamés, sous peine de sanction.")
    contenu(prs, "Ce que je présente : une plateforme reconstruite sur un contexte réel", "Contexte",
            ["Contexte métier réel (alternance Prévifrance)",
             "Plateforme entièrement RECONSTRUITE pour ce dossier",
             "Fichier INSEE réel + référentiel adhérents synthétique (Faker)",
             "Aucune donnée d'entreprise ni personnelle réelle"],
            "LA diapo d'honnêteté, à dire clairement : ce n'est pas le SI de l'entreprise. "
            "Le fichier décès est la vraie donnée publique, le référentiel est synthétique.")
    contenu(prs, "Mon rôle : de l'ingestion Eckert en production à l'incident vécu", "Contexte",
            ["Chargé d'étude Data / AMOA",
             "Traitement de collecte Eckert orchestré (Airflow) en production",
             "Étude d'architecture cible Snowflake menée puis non retenue"],
            "Ancrer la légitimité : j'ai vécu l'ingestion Eckert et l'incident que je rejouerai.")
    contenu(prs, "La donnée qui justifie tout : des dizaines de millions de décès", "Contexte",
            ["Fichier INSEE à largeur fixe (176 caractères)",
             "Publication mensuelle + fichiers annuels historiques",
             "Volumétrie cumulée : dizaines de M de lignes → justifie le distribué"],
            "Cette volumétrie annoncée ici servira à justifier Spark plus tard.")

    # ---- 4-10 C4.1.1 --------------------------------------------------------
    diviseur(prs, "Analyser l'environnement", "C4.1.1")
    contenu(prs, "Le besoin : transformer une obligation en donnée actionnable", "C4.1.1",
            ["Ingérer la source de vérité (INSEE)",
             "Rapprocher décès × portefeuille d'adhérents",
             "Produire une liste priorisée, fiable et tracée",
             "Rythme mensuel, valeur réglementaire → traçabilité non négociable"],
            "Traduire loi → besoin technique (B1 à B6 du livrable).")
    contenu(prs, "L'enjeu structurant : ne pas dépendre d'une source non maîtrisée", "C4.1.1",
            ["Conformité, fiabilité de la détection",
             "Résilience aux sources externes (← l'incident)",
             "RGPD : cloisonnement, aucune donnée réelle hors périmètre"],
            "L'enjeu n°3 (résilience) a provoqué l'incident réel et justifie l'architecture de validation.")
    contenu(prs, "Trois contraintes qui cadrent toute la conception", "C4.1.1",
            ["Coût nul : rien de managé, tout en local conteneurisé",
             "Délai < 1 mois : chaque brique démontrable en 5 min",
             "Complexité : volumétrie + source non contractuelle + pas d'ID pivot"],
            "Ces contraintes expliquent les choix techniques du livrable suivant.")
    contenu(prs, "L'existant et les quatre trous à combler en priorité", "C4.1.1",
            ["Existant : SQL Server, SSRS, un traitement Eckert sous Airflow",
             "Trous sans matériau : Spark, CI/CD, alerting, tests de sécurité",
             "C'est précisément ce que le Bloc 4 demande de produire"],
            "Distinguer étudié / maquetté / en production. Les 4 trous sont la feuille de route.")

    # ---- 10-16 C4.1.2 -------------------------------------------------------
    diviseur(prs, "Sélectionner les composants et chiffrer", "C4.1.2")
    contenu(prs, "Une architecture locale, portable, sans réécriture pour le cloud", "C4.1.2",
            ["Airflow · PostgreSQL · MinIO (S3) · Spark · GitHub Actions",
             "Principe : interfaces standard (S3, SQL, PySpark)",
             "Open source, local, démontrable"],
            "Montrer le schéma d'architecture. Chaque brique répond à un besoin de C4.1.1.")
    contenu(prs, "Chaque composant : un avantage attendu, un point de vigilance", "C4.1.2",
            ["Postgres : rôles + index + schémas par couche",
             "MinIO : versionne le brut, prépare le cloud",
             "Spark : distribué justifié par la donnée",
             "Vigilance : mémoire du Compose, scale horizontal de Postgres"],
            "Ne pas survendre : chaque avantage a sa contrepartie, assumée.")
    contenu(prs, "Le vendor lock-in est traité par des interfaces standard", "C4.1.2",
            ["S3 → AWS/Azure/GCS ; SQL → Azure SQL/Aurora ; PySpark → Databricks/EMR",
             "Point le plus propriétaire : le YAML GitHub Actions (réécriture marginale)",
             "Réversibilité voulue par conception"],
            "Résultat d'un choix délibéré, pas d'un hasard.")
    contenu(prs, "Trois scénarios de coût, avec hypothèses explicites", "C4.1.2",
            ["Local (retenu) : ~ coût du temps humain seul",
             "Cloud Azure : ~ 50 à 145 € / mois",
             "SaaS Snowflake/Fabric : ~ 80 à 250 € / mois",
             "Hypothèses : ~60k décès/mois, ~25 M cumulés, 1 run/mois"],
            "Le jury attend une méthode + des hypothèses, pas un devis exact. Le lock-in se traite ici.")
    contenu(prs, "Pourquoi le SaaS n'a pas été retenu (décision réelle, année 2)", "C4.1.2",
            ["Coût récurrent injustifié sur un besoin mensuel faible",
             "Souveraineté des données de santé/identité",
             "Maturité des équipes sur l'existant + pas de gain décisif",
             "Décision collégiale (équipe data + DBA)"],
            "Matériau direct de la question de jury sur le lock-in et le non-retenu.")

    # ---- 16-21 C4.2.1 -------------------------------------------------------
    diviseur(prs, "Concevoir l'entrepôt", "C4.2.1")
    contenu(prs, "Quatre couches, une responsabilité et un niveau d'accès chacune", "C4.2.1",
            ["bronze : source brute tracée ; silver : typé, dédoublonné",
             "gold : résultat métier ; ops : journal & qualité",
             "Le métier ne voit jamais le brut"],
            "La séparation des couches = colonne vertébrale de la sécurité et de la qualité.")
    contenu(prs, "La clé de rapprochement, normalisée à l'identique SQL et Python", "C4.2.1",
            ["Clé : nom | premier prénom | date de naissance",
             "Normalisation identique des deux côtés (accents, casse, non-alpha)",
             "C'est ce qui fait fonctionner le rapprochement sur noms composés"],
            "Point de conception sensible : sans cette cohérence, le rapprochement rate les noms accentués.")
    contenu(prs, "Deux rôles, moindre privilège — et c'est TESTÉ, pas déclaré", "C4.2.1",
            ["elt_writer écrit ; elt_reader lit gold seulement",
             "reader → INSERT gold = refusé ; reader → SELECT bronze = refusé",
             "Tests SEC-02/03 verts contre la base réelle"],
            "Point fort réel : la sécurité est prouvée par des tests, pas seulement affirmée.")
    contenu(prs, "Le métier consomme une vue priorisée, en lecture seule", "C4.2.1",
            ["gold.v_contrats_a_instruire : colonne priorité prête à l'emploi",
             "CERTAIN d'abord, puis décès anciens, puis gros capitaux",
             "Même point de branchement pour un outil BI (Metabase)"],
            "Montrer la capture de la vue lue par elt_reader.")

    # ---- 21-28 C4.2.2 -------------------------------------------------------
    diviseur(prs, "Les trois pipelines, dont le distribué", "C4.2.2")
    contenu(prs, "Trois méthodes, trois régimes de traitement", "C4.2.2",
            ["Fil de l'eau (SQL) : typage, nettoyage, déduplication",
             "Orchestration (Airflow) : enchaîne et fiabilise",
             "Distribué (Spark) : absorbe le volume du rapprochement"],
            "Annoncer les trois. La grille exige les trois, dont le distribué.")
    contenu(prs, "Fil de l'eau : le nettoyage vit dans le moteur, pas dans l'appli", "C4.2.2",
            ["Découpage largeur fixe + typage + dédup en une requête SQL",
             "DISTINCT ON (clé naturelle), ON CONFLICT DO NOTHING",
             "Traitement au fil de l'eau, PAS du streaming permanent"],
            "Nommage assumé : à l'arrivée d'un fichier, pas de Kafka (source mensuelle).")
    contenu(prs, "Orchestration : le DAG Airflow fiabilise la chaîne réelle", "C4.2.2",
            ["4 tâches, planification mensuelle, retries backoff",
             "SLA 30 min + callbacks (échec / SLA)",
             "Exécution réelle sur le vrai fichier INSEE : tout vert"],
            "Montrer la capture du DAG vert. Brique héritée du vécu, reconstruite proprement.",
            image=PREUVES / "C4-2-2_airflow_run.png", image_pleine=True)
    contenu(prs, "Distribué : Spark parce que la DONNÉE l'exige", "C4.2.2",
            ["Rapprochement décès × contrats sur cluster (master + worker)",
             "Justifié par la volumétrie cumulée, pas par la grille",
             "Sur le volume mensuel seul, Postgres suffirait (assumé)"],
            "Question piège anticipée : reconnaître que Postgres suffirait au mois, justifier par la trajectoire.")
    contenu(prs, "Le rapprochement gradue la confiance en trois niveaux", "C4.2.2",
            ["CERTAIN : clé + sexe + lieu concordants",
             "PROBABLE : clé exacte seule",
             "A_VERIFIER : homonymie (levée humaine)"],
            "Pas d'identifiant national → rapprochement probabiliste → graduation nécessaire.")
    contenu(prs, "Résultat : 4 162 contrats détectés, 88 M€ en niveau CERTAIN", "C4.2.2",
            ["CERTAIN : 2 846 contrats (88,1 M€)",
             "PROBABLE : 1 259 (38,4 M€) — A_VERIFIER : 57 (2,0 M€)",
             "Écrit dans gold, application Spark FINISHED"],
            "Montrer la Spark UI (application FINISHED) et les chiffres gold.",
            image=PREUVES / "C4-2-2_spark_ui.png", image_pleine=True)

    # ---- 28-31 C4.2.3 -------------------------------------------------------
    diviseur(prs, "Industrialiser : CI/CD", "C4.2.3")
    contenu(prs, "Un pipeline CI/CD construit de zéro, cinq étages", "C4.2.3",
            ["Qualité (ruff) · Tests (pytest) · Sécurité (pip-audit)",
             "Validation des DAG Airflow",
             "Déploiement de l'image applicative"],
            "Déploiement 100 % manuel à l'origine : ce pipeline est neuf.")
    contenu(prs, "Exécution réelle : les cinq jobs au vert", "C4.2.3",
            ["Déclenché à chaque push sur main",
             "Rapport de tests + couverture archivés",
             "Rouge = pas de fusion"],
            "Montrer l'onglet Actions. Assumer : le 1er run rouge (garde-fous qui mordent).",
            image=PREUVES / "C4-2-3_ci_run_vert.png", image_pleine=True)
    contenu(prs, "Déploiement réel : l'image est publiée sur un registre (GHCR)", "C4.2.3",
            ["build → push ghcr.io/ratpigene/eckert-elt → pull + smoke test",
             "Authentifié par le token intégré, aucun secret externe",
             "Image récupérable par tout consommateur (docker pull)"],
            "Déploiement d'artefact au sens propre. Limite honnête : pas de mise en service auto sur cluster cible.",
            image=PREUVES / "C4-2-3_deploiement_ghcr.png", image_pleine=True)

    # ---- 31-36 Exploitation -------------------------------------------------
    diviseur(prs, "Exploiter : supervision, MCO, documentation", "C4.3.1 · C4.3.2 · C4.3.3")
    contenu(prs, "Supervision : ce qui est surveillé et ses seuils", "C4.3.1",
            ["Statut de tâche, durée/SLA, taux de rejet, volumétrie",
             "Seuils explicites et centralisés (taux de rejet 2 %, min 1000 lignes)",
             "Journal ops = mémoire historisée"],
            "La supervision réutilise l'orchestrateur (choix de légèreté assumé).")
    contenu(prs, "Alertes : trois canaux, une escalade — et réellement délivrées", "C4.3.1",
            ["Journal ops → webhook (échec) → courriel (SLA)",
             "Alerte reçue : titre + corps + destinataire capturés",
             "Panne à 3 h : notification immédiate + reprise (Clear)"],
            "Montrer l'Event Log (retry visible) + la preuve d'alerte délivrée.",
            image=PREUVES / "C4-3-1_airflow_eventlog.png", image_pleine=True)
    contenu(prs, "Exploitation : un calendrier de MCO, secrets et certificats", "C4.3.2",
            ["Cycle mensuel / trimestriel / semestriel / annuel",
             "Rotation des secrets (trim.), certificats TLS (sem.)",
             "Point de vigilance n°1 : dérive du taux de rejet"],
            "Format calendaire. La dérive du taux de rejet = signal précoce d'un changement de format.")
    contenu(prs, "Documentation : un successeur reprend sans moi", "C4.3.3",
            ["Public + objectif énoncés",
             "Procédure de configuration depuis zéro",
             "Runbook : DAG en échec, Spark, rotation, reset propre"],
            "La procédure a été validée dans les faits : c'est ainsi que la plateforme a été montée.")

    # ---- 36-42 Qualité & incident -------------------------------------------
    diviseur(prs, "Qualité et résilience", "C4.4.1 · C4.4.2")
    contenu(prs, "Un cahier de recette automatisé, rejoué à chaque push", "C4.4.1",
            ["19 tests : fonctionnels, structurels ET sécurité",
             "Droits, secrets, dépendances testés",
             "Ce n'est pas un instantané, c'est un filet permanent"],
            "Démo live possible : lancer pytest (< 1 s, 19 verts). La sécurité testée est souvent le trou des dossiers.")
    contenu(prs, "L'incident réel : la confiance aveugle dans les métadonnées", "C4.4.2",
            ["La V1 validait sur les métadonnées DÉCLARÉES (taille, empreinte)",
             "Le producteur cesse de les publier → rejet systématique",
             "Fichiers pourtant parfaitement exploitables"],
            "LE MOMENT FORT. Raconter : 2 mois nominal, puis échec quotidien, cause non triviale.")
    contenu(prs, "Le correctif et le rejeu vert : valider le CONTENU, pas la promesse", "C4.4.2",
            ["Métadonnées → alerte ; contenu → seule source de vérité",
             "Fichier sain sans métadonnées : CONFORME + alerte",
             "Fichier corrompu : toujours bloqué. Test de non-régression"],
            "Démo live possible : le rejeu avant/après en < 1 s. Une ligne de code change tout.")

    # ---- 42-45 Bilan --------------------------------------------------------
    diviseur(prs, "Bilan", "Synthèse")
    contenu(prs, "Ce qui tourne, ce que j'assume comme limite", "Bilan",
            ["Chaîne complète prouvée : ingestion → Spark → gold → restitution",
             "Sécurité testée, CI verte, incident rejoué",
             "Limites assumées : Postgres unique, Spark soumis manuellement, pas de supervision infra"],
            "Assumer les limites plutôt que les masquer : marque de maturité d'ingénieur.")
    contenu(prs, "Ce que je referais autrement", "Bilan",
            ["Outiller le déclenchement Spark par Airflow",
             "Ajouter une supervision d'infrastructure",
             "Exposer un environnement de recette pour un déploiement complet"],
            "Terminer sur une note d'ingénieur : lucidité sur les prochaines étapes.")

    # ---- Annexes ------------------------------------------------------------
    diviseur(prs, "Annexes", "Pour les questions du jury")
    contenu(prs, "A1 — Schéma détaillé des tables et rôles", "Annexe",
            ["4 schémas, 6 tables, 2 rôles, 1 vue", "Preuve : C4-2-1_schema_postgres.txt"],
            "Ouvrir si le jury creuse l'entrepôt.")
    contenu(prs, "A2 — Tableau de coûts détaillé (3 scénarios)", "Annexe",
            ["Hypothèses de volumétrie explicites", "Comparatif local / Azure / SaaS"],
            "Ouvrir sur une question de coût ou de lock-in.")
    contenu(prs, "A3 — Workflow CI/CD complet", "Annexe",
            [".github/workflows/ci.yml", "5 jobs, déploiement GHCR"],
            "Ouvrir sur une question CI/CD ou déploiement.")

    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(SORTIE))
    return SORTIE


if __name__ == "__main__":
    chemin = construire()
    prs = Presentation(str(chemin))
    print(f"Support généré : {chemin} — {len(prs.slides.__iter__.__self__._sldIdLst)} diapositives")
