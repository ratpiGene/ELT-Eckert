# Support projetable — plan diapositive par diapositive

**Cible** : 37 diapositives + annexes. **Une idée par diapositive. Titre assertif** (il énonce la
conclusion). **≤ 5 lignes** projetées, le reste se dit (notes). Bandeau discret rappelant la
compétence (`C4.2.2`) sur chaque diapo de démonstration. Captures réelles > schémas génériques.

Légende : **T** = texte projeté (≤ 5 lignes) · **N** = note de commentaire (ce qui se dit) ·
**P** = preuve/capture à afficher.

---

## 0-4 min — Contexte (diapos 1-4)

**1. Une obligation légale : identifier les adhérents décédés**
- T : Loi Eckert · contrats en déshérence · risque ACPR · enjeu ayants droit.
- N : poser l'enjeu réglementaire en 30 s. Une mutuelle doit reverser les capitaux non réclamés.

**2. Ce que je présente : une plateforme reconstruite sur un contexte réel**
- T : contexte métier réel (Prévifrance) · plateforme **neuve** · données publiques + synthétiques.
- N : **la diapo d'honnêteté**. Le fichier INSEE est réel, le référentiel est Faker, aucune donnée
  d'entreprise. Ce n'est pas le SI de Prévifrance.

**3. Mon rôle**
- T : chargé d'étude Data / AMOA · traitement Eckert orchestré en prod · étude Snowflake.
- N : ancrer la légitimité : j'ai vécu l'ingestion Eckert et l'incident.

**4. La source de vérité : le fichier des décès de l'INSEE**
- T : data.gouv · largeur fixe 176 · mensuel + annuels · dizaines de M de lignes cumulées.
- N : la volumétrie annoncée ici justifiera Spark plus tard.

## 4-10 min — Analyse · C4.1.1 (diapos 5-8)

**5. Le besoin : de l'obligation à la donnée actionnable** — T : B1→B6. N : traduire loi → besoin technique.
**6. Les enjeux : conformité, fiabilité, résilience aux sources externes** — N : l'enjeu résilience = l'incident.
**7. Les contraintes : coût nul, moins d'un mois, volumétrie** — T : local, démontrable en 5 min, distribué justifié.
**8. L'existant et les 4 trous à combler** — T : Spark, CI/CD, alerting, tests sécu = à construire. P : tableau.

## 10-16 min — Composants et coûts · C4.1.2 (diapos 9-13)

**9. L'architecture cible en un schéma** — P : le diagramme (ingestion → bronze → validation → silver/Spark → gold).
**10. Chaque brique répond à un besoin** — T : tableau composant → avantage → vigilance.
**11. Le vendor lock-in est traité par des interfaces standard** — T : S3, SQL, PySpark. N : réversibilité voulue.
**12. Trois scénarios de coût, hypothèses explicites** — P : local (~0) / Azure (50-145€) / SaaS (80-250€).
**13. Pourquoi le SaaS n'a pas été retenu (décision réelle)** — N : coût/souveraineté/maturité, décision collégiale.

## 16-21 min — Entrepôt · C4.2.1 (diapos 14-17)

**14. Quatre couches, une responsabilité chacune** — P : bronze/silver/gold/ops.
**15. Le schéma et la clé de rapprochement** — T : clé nom|prénom|naissance normalisée SQL=Python.
**16. Deux rôles, moindre privilège — et c'est testé** — P : REC-SEC-02/03 verts. N : pas déclaratif, prouvé.
**17. Le métier lit une vue priorisée, en lecture seule** — P : `C4-2-1_vue_restitution.txt`.

## 21-28 min — Les trois pipelines · C4.2.2 (diapos 18-23)

**18. Trois méthodes, trois régimes** — T : fil de l'eau · orchestration · distribué.
**19. Fil de l'eau : le nettoyage vit dans le moteur (SQL)** — P : extrait 15 lignes, ligne clé surlignée.
**20. Orchestration : le DAG Airflow fiabilise la chaîne** — P : `C4-2-2_airflow_run.png` (vert).
**21. Distribué : Spark parce que la donnée l'exige** — N : volumétrie cumulée, pas la grille.
**22. Le rapprochement gradue la confiance (3 niveaux)** — P : extrait `F.when(...CERTAIN...)`.
**23. Résultat : 4162 contrats détectés, 88 M€ en CERTAIN** — P : `C4-2-2_spark_execution.txt` + Spark UI.

## 28-31 min — Industrialisation · C4.2.3 (diapos 24-26)

**24. Un pipeline CI/CD de zéro, 5 étages** — T : qualité, tests, sécurité, DAG, déploiement.
**25. Exécution réelle : les 5 jobs au vert** — P : `C4-2-3_ci_run_vert.png`.
**26. La CI est elle-même un contrôle de sécurité** — T : pip-audit strict, refus de secret, image sans privilège.

## 31-36 min — Exploitation · C4.3.1/2/3 (diapos 27-31)

**27. Supervision : ce qui est surveillé et ses seuils** — T : statut, SLA, taux de rejet, volumétrie.
**28. Alertes : 3 canaux, escalade** — T : journal → webhook → courriel (SLA). P : `alerte_echec.png`.
**29. Feuille de route : un calendrier de MCO** — T : mensuel/trim./sem./annuel + rotation des secrets.
**30. Documentation : un successeur reprend sans moi** — T : config + runbook.
**31. Panne à 3 h : qui est alerté, comment on reprend** — N : scénario concret (question de jury anticipée).

## 36-42 min — Qualité et résilience · C4.4.1/2 (diapos 32-35)

**32. Un cahier de recette automatisé, rejoué à chaque push** — P : 19 tests verts.
**33. On teste aussi la sécurité** — T : droits, secrets, dépendances.
**34. L'incident réel : la confiance aveugle dans les métadonnées** — N : **le moment fort**. Raconter.
**35. Le correctif et le rejeu vert** — P : `C4-4-2_incident_rejeu.txt`. Une ligne de code change tout.

## 42-45 min — Bilan (diapos 36-37)

**36. Ce qui tourne, ce que j'assume comme limite** — T : renvoi `LIMITES.md` (Postgres unique, Spark manuel…).
**37. Ce que je referais autrement** — N : Airflow→Spark outillé, supervision infra, environnement de recette.

---

## Annexes (après la conclusion, pour les questions)

- **A1** Schéma détaillé des tables et rôles (`C4-2-1_schema_postgres.txt`).
- **A2** Tableau de coûts détaillé (3 scénarios, hypothèses).
- **A3** Workflow CI/CD complet (`.github/workflows/ci.yml`).
- **A4** Sortie du job Spark et agrégats gold.
- **A5** Récit complet de l'incident (`docs/incident_metadonnees.md`).
- **A6** Matrice de recette (REC-FON / REC-STR / REC-SEC).

## Rappels de forme

- Texte projeté ≥ 18 pt ; ≤ 12 blocs par schéma ; extraits ≤ 15 lignes, ligne clé surlignée.
- 10 compétences en 45 min = **4 min chacune**. Toute séquence qui déborde de +1 min est coupée.
- Répéter **deux fois chronométré**. Soigner la séquence 34-35 (l'incident) : c'est le pic.
