# Conducteur de soutenance — 30 min

Document de conduite (à garder à côté de soi / imprimer). Pour chaque diapo :
le **temps cumulé visé**, ce qu'il faut **aborder**, et le **texte à dire** (au mot près, à
adapter à ta voix). Objectif : ~1,7 min par diapo. **Si une diapo déborde de +30 s, on coupe.**

Repères clés à ne jamais oublier :
- **Diapo 3** : dire le périmètre honnête (plateforme reconstruite ≠ SI de l'entreprise).
- **Diapos 14 et 16** : **démo live possible** (pytest / rejeu de l'incident, < 1 s).
- **Diapos 15-16** : le **moment fort**. Ralentir, raconter.

---

## Diapo 1 — Titre · (0:00)
**Aborder** : se présenter, annoncer le format.
**À dire** : « Bonjour. Je suis [Prénom Nom], alternant chez Prévifrance. En 30 minutes, je vous
présente une plateforme data que j'ai conçue et opérée pour répondre à l'obligation loi Eckert,
puis je répondrai à vos questions. »

## Diapo 2 — L'obligation légale · Contexte · (0:20)
**Aborder** : le problème métier et son enjeu réglementaire.
**À dire** : « Une mutuelle doit repérer ses adhérents décédés pour verser les capitaux des
contrats en déshérence. C'est une obligation légale — la loi Eckert — sous risque de sanction de
l'ACPR, avec un vrai enjeu de restitution aux ayants droit. La source de vérité, c'est le fichier
des personnes décédées publié par l'INSEE. »

## Diapo 3 — Périmètre honnête + mon rôle · Contexte · (1:00)
**Aborder** : l'honnêteté du périmètre (crucial) + légitimité.
**À dire** : « Un point d'honnêteté d'emblée : j'ai reconstruit entièrement cette plateforme, sur
un contexte métier réel. Ce n'est pas le système d'information de l'entreprise. Le fichier décès
est la vraie donnée publique de l'INSEE, mais le référentiel adhérents est synthétique, généré
avec Faker — aucune donnée personnelle réelle. J'ai vécu en production l'ingestion Eckert, et
l'incident que je rejouerai à la fin. »

## Diapo 4 — Analyse et les 4 trous · C4.1.1 · (2:00)
**Aborder** : besoins, contraintes, existant, les 4 compétences sans matériau.
**À dire** : « Trois contraintes cadrent tout : un coût nul, donc tout tourne en local ; un délai
court, donc chaque brique doit être démontrable ; et une forte volumétrie. L'existant couvrait
SQL Server et un Airflow. Mais quatre compétences n'avaient aucun matériau : le calcul distribué,
la CI/CD, l'alerting et les tests de sécurité. Ce sont les priorités que j'ai construites. »

## Diapo 5 — Les composants · C4.1.2 · (5:00)
**Aborder** : la stack et la portabilité (anti-lock-in).
**À dire** : « J'ai retenu cinq briques open source : Airflow, PostgreSQL, MinIO, Spark et GitHub
Actions. Toutes exposent des interfaces standard — S3, SQL, PySpark — ce qui traite le vendor
lock-in par conception : je peux basculer vers le cloud sans réécriture majeure. »

## Diapo 6 — Les coûts · C4.1.2 · (6:30)
**Aborder** : les 3 scénarios chiffrés + le non-retenu réel.
**À dire** : « Sur le coût, j'ai chiffré trois scénarios avec des hypothèses assumées. Le local
retenu coûte surtout du temps humain ; le cloud Azure, 50 à 145 € par mois ; le SaaS type
Snowflake, 80 à 250. Dans le contexte réel, le SaaS a été écarté pour son coût récurrent et la
souveraineté des données de santé. Le jury attend une méthode de chiffrage et des hypothèses,
pas un devis exact. »

## Diapo 7 — L'entrepôt · C4.2.1 · (9:00)
**Aborder** : 4 couches, moindre privilège testé, vue métier.
**À dire** : « L'entrepôt est organisé en quatre couches : le brut, le nettoyé, le métier et le
journal technique. Deux rôles appliquent le moindre privilège : le pipeline écrit, le métier lit
seulement la couche métier. Et je le prouve par des tests : le rôle de lecture ne peut ni écrire,
ni même lire le brut. Le métier consomme une vue déjà priorisée par niveau de confiance. »

## Diapo 8 — Trois méthodes de pipeline · C4.2.2 · (11:00)
**Aborder** : annoncer les 3 méthodes (dont le distribué).
**À dire** : « La compétence pipelines exige trois méthodes. Le fil de l'eau, en SQL, nettoie et
dédoublonne au plus près de la donnée. L'orchestration Airflow enchaîne et fiabilise les étapes.
Et le distribué, avec Spark, absorbe le volume du rapprochement. Les trois tournent réellement et
produisent chacune une donnée. »

## Diapo 9 — Orchestration (capture DAG) · C4.2.2 · (13:00)
**Aborder** : le DAG réel vert sur le vrai fichier.
**À dire** : « Voici le DAG réel : quatre tâches, de la récupération du catalogue jusqu'à la
promotion en silver, avec des retries, un SLA et des callbacks d'alerte. Il tourne au vert sur le
vrai fichier INSEE téléchargé depuis data.gouv. »

## Diapo 10 — Distribué / Spark (capture) · C4.2.2 · (14:30)
**Aborder** : le rapprochement, 3 niveaux, le résultat, la justification honnête de Spark.
**À dire** : « Le rapprochement tourne sur un cluster Spark et gradue la confiance en trois
niveaux, faute d'identifiant national. Résultat : 4 162 contrats potentiellement en déshérence,
dont 88 millions d'euros au niveau certain. Et je serai honnête : sur le seul volume mensuel, un
Postgres bien indexé suffirait. Spark se justifie par la volumétrie cumulée — des dizaines de
millions de lignes — et par la trajectoire de croissance. »

## Diapo 11 — CI/CD + déploiement (capture) · C4.2.3 · (17:00)
**Aborder** : les 5 jobs, le déploiement réel GHCR, le 1er run rouge assumé.
**À dire** : « La CI/CD, construite de zéro, enchaîne cinq contrôles à chaque push : qualité du
code, tests, scan de sécurité des dépendances, validation des DAG, et déploiement. Le déploiement
est réel : l'image applicative est publiée sur le registre GitHub, puis re-téléchargée et testée.
Détail que j'assume : mon tout premier run était rouge — c'est la preuve que les garde-fous
mordent vraiment. »

## Diapo 12 — Supervision + alerte (capture) · C4.3.1 · (19:00)
**Aborder** : indicateurs, seuils, alerte réellement délivrée, escalade.
**À dire** : « La supervision surveille le statut des tâches, les SLA et surtout le taux de rejet.
Chaque étape est journalisée en base. Et sur un échec, une alerte part réellement : j'ai capturé
la notification reçue par le destinataire, avec le lien vers le journal. Un dépassement de délai,
plus grave pour une obligation réglementaire, escalade par courriel. »

## Diapo 13 — Exploitation + doc · C4.3.2 / C4.3.3 · (21:00)
**Aborder** : feuille de route MCO, secrets/certificats, runbook.
**À dire** : « Côté exploitation, une feuille de route calendaire cadre la maintenance : rotation
des secrets au trimestre, certificats au semestre, montées de version à l'année. Et une
documentation avec runbook permet à un successeur de reprendre sans moi — c'est d'ailleurs cette
même procédure qui a servi à monter la plateforme. »

## Diapo 14 — Recette · C4.4.1 · (23:00) — ⚡ démo live possible
**Aborder** : recette automatisée, la sécurité testée.
**À dire** : « La recette est automatisée : dix-neuf tests fonctionnels, structurels et de
sécurité — les droits, la non-exposition des secrets, le scan des dépendances. Elle est rejouée à
chaque push : ce n'est pas un instantané, c'est un filet permanent. »
**(Option live)** : « Je peux la lancer devant vous. » → `pytest` → 19 verts en < 1 s.

## Diapo 15 — L'incident · C4.4.2 · (24:30) — 🔴 MOMENT FORT
**Aborder** : le récit, la cause racine non triviale. Ralentir.
**À dire** : « Et j'en viens à l'incident, vécu en production. Le contrôle d'entrée validait le
fichier sur ses métadonnées déclarées : la taille et l'empreinte annoncées sur la plateforme.
Après environ deux mois de fonctionnement nominal, le producteur a cessé de publier ces
métadonnées. Résultat : le contrôle n'avait plus rien à comparer et rejetait systématiquement le
fichier. Le traitement tombait en erreur chaque jour — alors que les fichiers étaient parfaitement
exploitables. La cause n'est pas triviale : le contrat de données change sans préavis, du côté du
producteur. »

## Diapo 16 — Le correctif + rejeu · C4.4.2 · (26:30) — ⚡ démo live possible
**Aborder** : l'inversion de logique, le rejeu vert, la leçon.
**À dire** : « Le correctif inverse la logique : les métadonnées ne font plus qu'alerter, et la
vérité, c'est le contenu — la structure, la volumétrie, le taux de rejet. Un fichier sain sans
métadonnées passe désormais ; un fichier corrompu reste bloqué. Et un test de non-régression
verrouille le cas, pour qu'il ne revienne jamais en silence. La leçon que j'en tire : une source
externe n'est jamais un contrat. »
**(Option live)** : « Je peux rejouer l'avant/après. » → le fichier sans métadonnées passe
CONFORME, le corrompu est bloqué, en < 1 s.

## Diapo 17 — Bilan · (28:00 → 30:00)
**Aborder** : ce qui tourne, limites assumées, ouverture, remerciement.
**À dire** : « En bilan : la chaîne complète tourne et est prouvée — ingestion, distribué,
restitution ; la sécurité est testée, la CI est verte, l'incident est rejoué. J'assume mes
limites : une seule instance PostgreSQL, un job Spark que je lance encore manuellement, et pas de
supervision d'infrastructure. Si je continuais, j'outillerais le déclenchement de Spark par
Airflow et j'ajouterais une supervision d'infra. Je vous remercie, et je suis prêt pour vos
questions. »

---

## Annexes (masquées — à ouvrir sur question)

- **A1** — Schéma de l'entrepôt (couches, tables, rôles). *Si le jury creuse l'entrepôt.*
- **A2** — Estimation des coûts détaillée. *Sur une question de coût ou de lock-in.*
- **A3** — Workflow CI/CD complet. *Sur une question CI/CD ou déploiement.*

Pour les questions probables et leurs réponses en 60 s : voir `questions_jury.md`.

## Gestion du temps (repères de contrôle)
- À **9:00** tu dois être sur l'entrepôt (diapo 7). Si tu es en retard → accélère 5-6.
- À **17:00** tu dois attaquer la CI/CD (diapo 11). C'est le milieu.
- À **24:30** tu dois être sur l'incident (diapo 15) — garde-lui ses 3-4 min.
- Si tu es en avance : développe la diapo 10 (Spark) ou 15 (incident). Jamais les autres.
