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
**À dire** : « Bonjour. Je suis Emmanuel Jovanovic, alternant chez Prévifrance. Dans le cadre de cette soutenance je vais vous présenter une plateforme data que j'ai conçue et opérée pour répondre à l'obligation loi Eckert,
puis je répondrai à vos questions. »

## Diapo 2 — L'obligation légale · Contexte · (0:20)
**Aborder** : le problème métier et son enjeu réglementaire.
**À dire** : « Dans le cadre de la loi Eckert, une mutuelle comme plusieurs autres organismes se doit de lutter contre les contrats et capitaux déshérence, dans notre cas principalement les assurances décès. S'y soustraire présente un risque de sanction de
l'ACPR, avec un vrai enjeu de restitution aux ayants droit. Il y a de nombreuses façons d'y répondre, l'une d'elle étant l'exploitation du fichier des personnes décédées mis à disposition par l'INSEE sur la plateforme datagouv »

## Diapo 3 — Périmètre honnête + mon rôle · Contexte · (1:00)
**Aborder** : l'honnêteté du périmètre (crucial) + légitimité.
**À dire** : « Un point d'honnêteté d'emblée : j'ai reconstruit entièrement cette plateforme, sur
un contexte métier réel. Ce n'est pas le système d'information de l'entreprise. Le fichier décès
est la vraie donnée publique de l'INSEE, mais le référentiel adhérents est synthétique, généré
avec Faker — aucune donnée personnelle réelle. J'ai vécu en production l'ingestion Eckert, et
l'incident que je rejouerai à la fin. »

## Diapo 4 — Analyse et les 4 trous · C4.1.1 · (2:00)
**Aborder** : besoins, contraintes, existant, les 4 compétences sans matériau.
**À dire** : «Je vais découper cette analyse en 2 parties, pour isoler les besoins et contraintes côté entreprise et côté soutenance. Tout d'abord côté entreprise, il y a ce besoind d'avoir une donnée actionnable donc rapprochable avec notre référentiel pour détecter des correspondances, une donnée nettoyée pour être utilisable et finalement une donnée tracée et traçable pour justifier de potentielles actions, tout ça à échéance mensuelle pour coller aux dépots sur datagouv.

Au niveau des contraintes, j'ai d'abord mis cout nul, ça cache surtout un besoin de souveraineté du fait de travailler avec des données personnelles de santé donc soumises à la RGPD et aussi un manque de compétence en interne sur des problématiques cloud, Saas, conformité qui ferait automatiquement exploser le budget d'un projet comme celui ci en forcant à déléguer ou recruter des profils cohérents. Ensuite il y avait le délai, un peu moins d'un mois suite à l'audit réalisé par les CACs l'idée étant surtout de montrer que le sujet est pris en main pas nécessairement d'avoir un produit abouti et mature à l'issue. Finalement une forte volumétrie, on parle d'environ 60k lignes par mois, ça peut paraitre ridicule mais jusqu'à présent la mutuelle n'avait pas à gérer des fluxs aussi importants avec une échéance aussi courte.

Pour l'état des lieux de l'existant ici je vais surtout parler des technologies du SI qui pouvaient servir pour ce projet, tout d'abord l'entrepot de données SQL server en interne chez prévifrance, ce dernier alimente notre outil de gestion des contrats fourni par un prestataire et nous y avons greffé d'autres éléments au fil du temps. Ensuite SSRS et PBI au sein d'un portail décisionnel et opérationnel, la quasi totalité du reporting au sein de la mutuelle se fait de cette façon et finalement l'utilisation de Python et Airflow pour piloter le vrai traitement mis en place au sein de l'entreprise »

## Diapo 5 — Les composants · C4.1.2 · (5:00)
**Aborder** : la stack et la portabilité (anti-lock-in).
**À dire** : « J'ai retenu cinq briques open source pour mon redéveloppement : 
- Airflow pour l'orchestration, c'est facile d'utilisation et ça collait au projet d'entreprise,
- PostgreSQL pour la partie stockage relationnel, 
- MinIO pour le stockage objet, 
- Spark pour le data processing distribué,
- GitHub Actions pour la CI/CD. 

Toutes exposent des interfaces standard S3, SQL, PySpark, l'idée ici était de répondre au besoin initial de souveraineté. Toute la solution peut tourner sur un serveur interne sans dépendre d'un tiers. J'ai fait le choix d'y greffer une contrainte cloud en essayant de traiter le vendor-lock-in. L'idée ici étant que ce choix de technologies ne crée par un frein majeur si un basculement cloud est envisagé par la suite. »

## Diapo 6 — Les coûts · C4.1.2 · (6:30)
**Aborder** : la méthode, le coût humain du local chiffré, le détail Azure/SaaS, le non-retenu réel.
**À dire** : « Sur les coûts, je voulais surtout poser une méthode avec des hypothèses assumées.
J'ai comparé trois scénarios, et j'insiste sur un point : même le scénario local n'est pas
gratuit. Le logiciel l'est, le serveur on l'a déjà, mais il reste mon temps. Si je chiffre le coût
chargé d'un alternant autour de 90 € la journée, ça fait une construction à peu près à 1 350 € en
one-shot, et surtout une exploitation récurrente autour de 45 € par mois. Pour le cloud Azure, en
détaillant les ressources — un PostgreSQL managé burstable, du stockage objet, Data Factory pour
l'orchestration et un petit cluster Databricks à la demande — j'arrive autour de 30 à 90 € par
mois selon que je laisse l'entrepôt allumé ou non. Pour le SaaS, tout dépend du modèle de
facturation : Snowflake, à l'usage, reste entre 40 et 80 € ; mais Microsoft Fabric, qui facture à
la capacité, grimpe vite à 180-300 € si on maintient l'instance allumée. Et ce dernier scénario
n'est pas théorique : il a été étudié pour de vrai en année 2 chez Prévifrance, puis écarté — pour
le coût récurrent, mais surtout pour la souveraineté des données de santé. »

## Diapo 7 — L'entrepôt · C4.2.1 · (9:00)
**Aborder** : 4 couches, **3 rôles dont l'administration (DBA)**, moindre privilège testé, vue métier.
**À dire** : « Pour l'entrepôt, j'ai choisi une organisation en quatre couches : le bronze pour la
donnée brute telle que reçue, qui me sert de filet et de traçabilité ; le silver pour le typé, le
nettoyé, le dédoublonné ; le gold pour le résultat métier ; et une couche ops pour le journal
technique. Côté accès, j'ai repris la logique du SI d'origine, où un DBA jouait le rôle de gardien.
J'ai donc trois rôles, avec le moindre privilège. Un rôle d'administration, qui seul peut faire
évoluer la structure et gérer les droits — c'est le gatekeeper. Un rôle d'écriture, pour le
pipeline, qui alimente mais ne touche pas au schéma. Et un rôle de lecture, pour le métier, limité
au gold. Et je ne me contente pas de le déclarer, je le teste : mon rôle de lecture, s'il essaie
d'écrire dans le gold ou même de lire le brut, se fait refuser — c'est vérifié automatiquement. Le
métier ne touche jamais aux tables directement, il passe par une vue déjà priorisée par niveau de
confiance. »

## Diapo 8 — Trois méthodes de pipeline · C4.2.2 · (11:00)
**Aborder** : le choix **ELT (vs ETL)**, puis les 3 méthodes (dont le distribué).
**À dire** : « J'arrive sur le cœur technique, les pipelines. Et d'abord un choix d'architecture :
je fais de l'ELT, pas de l'ETL. La différence, c'est l'ordre. En ETL, on transforme la donnée
avant de la charger. Moi je fais l'inverse : je charge d'abord la donnée brute — c'est mon bronze —
et je transforme ensuite, à l'intérieur de l'entrepôt et de Spark. Ça m'apporte deux choses : je
garde toujours la donnée source pour pouvoir rejouer, et je transforme au plus près de la donnée,
là où c'est le plus efficace. Sur cette base, la compétence demande trois méthodes, et chacune
produit vraiment une donnée : le fil de l'eau en SQL pour le typage et la déduplication,
l'orchestration Airflow qui enchaîne et fiabilise, et le calcul distribué avec Spark pour le
rapprochement. Je vous montre les deux dernières en images. »

## Diapo 9 — Orchestration (capture DAG) · C4.2.2 · (13:00)
**Aborder** : le DAG réel vert + **le rôle de chacune des 4 tâches**.
**À dire** : « Voici le vrai DAG, tel qu'il tourne, avec ses quatre tâches. La première interroge
l'API de data.gouv pour repérer le bon fichier à récupérer. La deuxième le télécharge et le
valide — c'est là que je vérifie le contrat de données, j'y reviendrai avec l'incident. La
troisième charge le fichier brut dans le bronze, tel quel. Et la quatrième le promeut en silver :
elle le découpe, le type et le dédoublonne. Au-delà de l'enchaînement, ce qui compte c'est la
fiabilisation : des relances automatiques si une erreur est passagère, un SLA sur l'étape
sensible, et des callbacks qui déclenchent une alerte si ça casse. Et c'est bien le vrai fichier
INSEE qui passe, pas une simulation. »

## Diapo 10 — Distribué / Spark (capture) · C4.2.2 · (14:30)
**Aborder** : partage **Postgres/Spark**, l'**INSEE partiel reconstruit** (comme le réel), 3 niveaux, Spark assumé.
**À dire** : « Le rapprochement, c'est la partie distribuée, sur un cluster Spark. D'abord, qui
fait quoi : toute la donnée vit dans PostgreSQL — les décès et le référentiel adhérents sont en
silver. Spark, lui, ne stocke rien : il lit ces tables via JDBC, il fait la jointure de manière
distribuée, et il réécrit le résultat dans le gold, toujours dans Postgres. Sur le principe
métier, je reprends ce qu'on faisait dans le projet réel : je ne rapproche pas le fichier INSEE
entier, je reconstruis un INSEE partiel, ciblé sur les identités qui nous concernent — dans ma
plateforme ce jeu est synthétique et généré pour recouper le référentiel. Comme je n'ai pas
d'identifiant national pour une correspondance parfaite, je travaille sur une clé
nom-prénom-date de naissance, avec trois niveaux de confiance : certain, probable, et à vérifier
pour les homonymes. Résultat : 4 162 contrats potentiellement en déshérence, dont 88 millions
d'euros au niveau certain. Et je serai honnête sur la question qui vient toujours : sur le volume
d'un seul mois, un Postgres bien indexé suffirait. Ce qui justifie Spark, c'est la volumétrie
cumulée et la trajectoire si le périmètre grandit. »

## Diapo 11 — CI/CD + déploiement (capture) · C4.2.3 · (17:00)
**Aborder** : les 5 jobs, le déploiement réel GHCR, le 1er run rouge assumé.
**À dire** : « On passe sur l'industrialisation, et c'est un vrai trou que j'ai comblé : à
l'origine, le déploiement était 100 % manuel. J'ai construit une CI/CD de zéro. À chaque fois que
je pousse du code, cinq contrôles se déclenchent tout seuls : la qualité du code, les tests, un
scan de sécurité des dépendances, la validation que mes DAG s'importent sans erreur, et le
déploiement. Et le déploiement est réel : l'image de l'application est publiée sur un registre,
puis re-téléchargée et testée pour vérifier qu'elle démarre. Un détail que j'assume : mon tout
premier run était rouge. Pour moi c'est plutôt une bonne nouvelle — ça prouve que les garde-fous
servent vraiment à quelque chose. »

## Diapo 12 — Supervision + alerte (capture) · C4.3.1 · (19:00)
**Aborder** : indicateurs, seuils, alerte réellement délivrée, escalade.
**À dire** : « Autre trou d'origine : il n'y avait pas d'alerting, on lisait les logs à la main.
J'ai mis en place une supervision. Je surveille le statut des traitements, les temps d'exécution,
et surtout le taux de rejet des fichiers, parce que c'est le signal qui trahit un problème de
qualité. Tout est journalisé en base. Et quand un traitement échoue, une alerte part réellement —
je l'ai capturée : une notification qui arrive à son destinataire, avec le détail de l'erreur et
le lien vers le journal. J'ai aussi prévu une escalade : un simple échec notifie l'équipe, mais un
dépassement de délai, plus grave vu l'enjeu réglementaire, remonte par mail. »

## Diapo 13 — Exploitation + doc · C4.3.2 / C4.3.3 · (21:00)
**Aborder** : feuille de route MCO, secrets/certificats, runbook.
**À dire** : « Une plateforme, ça se maintient dans le temps. J'ai donc formalisé une feuille de
route d'exploitation sous forme de calendrier : ce qu'on fait chaque mois, chaque trimestre —
comme la rotation des mots de passe et des secrets — chaque semestre pour les certificats, chaque
année pour les montées de version. Et j'ai rédigé une documentation avec un vrai runbook : quoi
faire si un DAG plante, si Spark ne démarre pas, comment repartir proprement. L'objectif, c'est
qu'une personne qui reprend derrière moi puisse le faire sans moi — d'ailleurs c'est cette
procédure qui m'a servi à remonter la plateforme de zéro. »

## Diapo 14 — Recette · C4.4.1 · (23:00) — ⚡ démo live possible
**Aborder** : recette automatisée, la sécurité testée.
**À dire** : « Sur la qualité, j'ai écrit un cahier de recette, mais automatisé. Dix-neuf tests
qui couvrent le fonctionnel, le structurel, et surtout la sécurité — parce que c'est souvent ce
qui manque dans ce genre de projet : je teste les droits d'accès, le fait qu'aucun secret ne
traîne dans le code, et je scanne les dépendances. Et comme ces tests tournent à chaque push, ce
n'est pas une photo à un instant T, c'est un filet permanent. »
**(Option live)** : « Je peux la lancer devant vous. » → `pytest` → 19 verts en < 1 s.

## Diapo 15 — L'incident · C4.4.2 · (24:30) — 🔴 MOMENT FORT
**Aborder** : le récit, la cause racine non triviale. Ralentir.
**À dire** : « Et j'en arrive à ce qui est, pour moi, le plus intéressant : un incident que j'ai
réellement vécu en production. Au départ, pour valider qu'un fichier reçu était bon, on se fiait
aux métadonnées annoncées sur data.gouv — la taille et l'empreinte du fichier. Ça a marché pendant
environ deux mois. Et puis un jour, le producteur a tout simplement arrêté de publier ces
métadonnées. Du coup notre contrôle n'avait plus rien à comparer, et il rejetait tous les
fichiers, systématiquement. Le traitement tombait en erreur tous les jours — alors que les
fichiers, eux, étaient parfaitement exploitables. La cause racine est subtile : on avait
transformé une information de confort, non contractuelle, en condition bloquante. »

## Diapo 16 — Le correctif + rejeu · C4.4.2 · (26:30) — ⚡ démo live possible
**Aborder** : l'inversion de logique, le rejeu vert, la leçon.
**À dire** : « La correction, c'est un renversement de logique. Au lieu de faire confiance à ce
que le producteur annonce, je valide ce que le fichier contient vraiment : sa structure, sa
volumétrie, son taux de rejet. Les métadonnées ne servent plus qu'à lever une alerte, elles ne
bloquent plus rien. Concrètement, un fichier sain sans métadonnées passe maintenant sans problème,
mais un fichier réellement corrompu reste bloqué. Et j'ai ajouté un test de non-régression pour
que cet incident précis ne puisse plus jamais revenir en silence. La leçon que j'en retire, et que
j'ai appliquée aux autres flux : une source externe, ce n'est jamais un contrat. »
**(Option live)** : « Je peux rejouer l'avant/après. » → le fichier sans métadonnées passe
CONFORME, le corrompu est bloqué, en < 1 s.

## Diapo 17 — Bilan · (28:00 → 30:00)
**Aborder** : ce qui tourne, limites assumées, ouverture, remerciement.
**À dire** : « Pour conclure. Ce que je retiens, c'est que la chaîne complète tourne et que je
peux le prouver : de l'ingestion jusqu'au résultat métier, en passant par le distribué. La
sécurité est testée, l'intégration continue est verte, et l'incident est rejouable. Je tiens aussi
à assumer mes limites, parce que pour moi c'est ça la maturité d'ingénieur : je n'ai qu'une seule
instance PostgreSQL, mon job Spark je le lance encore à la main, et je n'ai pas de supervision
d'infrastructure. Si je devais continuer, je ferais déclencher Spark directement par Airflow et
j'ajouterais cette supervision. Je vous remercie de votre attention, et je suis à votre
disposition pour vos questions. »

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
