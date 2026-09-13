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
**À dire** : «Je vais découper cette analyse en 2 parties, pour isoler les besoins et contraintes côté entreprise et côté soutenance. Tout d'abord côté entreprise, il y a ce besoin d'avoir une donnée actionnable donc rapprochable avec notre référentiel pour détecter des correspondances, une donnée nettoyée pour être utilisable et finalement une donnée tracée et traçable pour justifier de potentielles actions, tout ça à échéance mensuelle pour coller aux dépots sur datagouv.

Au niveau des contraintes, j'ai d'abord mis cout nul, ça cache surtout un besoin de souveraineté du fait de travailler avec des données personnelles de santé donc soumises à la RGPD et aussi un manque de compétence en interne sur des problématiques cloud, Saas, conformité qui ferait automatiquement exploser le budget d'un projet comme celui ci en forcant à déléguer ou recruter des profils cohérents. Ensuite il y avait le délai, un peu moins d'un mois suite à l'audit réalisé par les CACs l'idée étant surtout de montrer que le sujet est pris en main pas nécessairement d'avoir un produit abouti et mature à l'issue. Finalement une forte volumétrie, on parle d'environ 60k lignes par mois, ça peut paraitre ridicule mais jusqu'à présent la mutuelle n'avait pas à gérer des fluxs aussi importants avec une échéance aussi courte.

Pour l'état des lieux de l'existant ici je vais surtout parler des technologies du SI qui pouvaient servir pour ce projet, tout d'abord l'entrepot de données SQL server en interne chez prévifrance, ce dernier alimente notre outil de gestion des contrats fourni par un prestataire et nous y avons greffé d'autres éléments au fil du temps. Ensuite SSRS et PBI au sein d'un portail décisionnel et opérationnel, la quasi totalité du reporting au sein de la mutuelle se fait de cette façon et finalement l'utilisation de Python et Airflow pour piloter le vrai traitement mis en place au sein de l'entreprise

A la vue des éléments que je viens de citer on réalise que je n'ai absolument pas parlé de cloud, d'architecture distribué, de CI/CD, d'alerting ou de tests de sécurité. C'est normal, malheureusement c'est des points que je n'ai pas eu la chance de pouvoir traiter dans le cadre de mon expérience en entreprise. C'est donc pour ça que pour cette soutenance j'ai essayé d'intégrer ces problématiques au sein de ma solution.
»

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
J'ai comparé trois scénarios dont celui retenu. 

Tout d'abord le local qui n'est pas gratuit, Le logiciel l'est, le serveur on l'a déjà, mais il reste mon temps. Si je chiffre le coût chargé d'un alternant autour de 90 € la journée, ça fait une construction à peu près à 1 350 € en one-shot, et une exploitation récurrente autour de 45 € par mois. 

Pour le cloud ensuite j'ai choisi de faire mon estimation via Azure, en détaillant les ressources — un PostgreSQL managé burstable, du stockage objet, Data Factory pour l'orchestration et un petit cluster Databricks à la demande — j'arrive autour 90€ par mois en laissant l'entrepot allumé en 24/24. 

Pour le SaaS, ça dépend vraiement du modèle de facturation : par exemple avec Snowlflake, en pay as you go on est autour de 40 à 80€ par mois. Par contre avec Fabric qui nous facture selon la capacité souhaitée on démarre autour de 150€, cette étude de cout j'y avais participé côté entreprise et c'est un des éléments qui nous avait fait penché pour la solution locale en plus du besoin de souveraineté et les "lacunes" techniques en interne. »

## Diapo 7 — L'entrepôt · C4.2.1 · (9:00)
**Aborder** : 4 couches, **3 rôles dont l'administration (DBA)**, moindre privilège testé, vue métier.
**À dire** : « Je vais maintenant passer rapidement sur l'entrepot de données associé au projet, j'ai choisi une architecture en médaillon en 4 couches. Les classiques avec le bronze pour toute la donnée brute, le silver pour la donnée typée et nettoyée et finalement le gold pour la donnée utile au métier une fois le passage via spark. En plus des 3 couches classiques j'ai greffé une couche ops, ici l'idée c'est de faire atterir les différents journaux techniques quelque part pour potentiellement déclencher des alertes et permettre de les explorer sous SQL.

Ces couches elles sont accompagnées de permissions, j'ai repris la structure côté SI avec 1 rôle DBA qui fait office de gatekeeper, c'est le seul qui peut faire évoluer l'infrastructure et ses composants, un rôle pour notre pipeline qui a uniquement les permissions en écriture, il sert juste à alimenter et finalement un rôle en lecture avec uniquement des permissions sur le gold. C'est le rôle destiné aux utilisateurs métiers pour consommer la donnée actionnable, on applique ici le principe de moindre privilège et les rôles restent évolutif si par exemple le métier est amené à devoir consulter le silver pour une étude. Cela dit le métier ne touche pas aux tables directement, uniquement à des vues côté gold qui priorisent la donnée par niveau de confiance sur les correspondances trouvées. »

## Diapo 8 — Trois méthodes de pipeline · C4.2.2 · (11:00)
**Aborder** : le choix **ELT (vs ETL)**, puis les 3 méthodes (dont le distribué).
**À dire** : « J'arrive sur le cœur de la technique, les pipelines. Je vais commencer par le choix de méthode, ici je fais de l'ELT pas de l'ETL. La différence, c'est l'ordre. Je charge d'abord la donnée brute en bronze et je transforme ensuite, à l'intérieur de l'entrepôt et de Spark. Cette façon de faire elle présente 2 gains, d'abord on conserver systématiquement la donné source donc on est en mesure de rejouer notre traitements et ensuite je transforme la donnée au sein de mon infra pas en passerelle entre ma destination et l'endroit ou je pioche cette donnée.
 
Sur cette base, la compétence demande trois méthodes, et chacune
produit vraiment une donnée : le temps réel en SQL pour le typage et la déduplication,
l'orchestration Airflow qui enchaîne et fiabilise, et le calcul distribué avec Spark pour le
rapprochement. Je vais pouvoir vous montrer quelques captures d'écrans pour les 2 derniers. »

## Diapo 9 — Orchestration (capture DAG) · C4.2.2 · (13:00)
**Aborder** : le DAG réel vert + **le rôle de chacune des 4 tâches**.
**À dire** : « On commence avec l'orchestration via Airflow, ici on retrouve le dag qui va du bronze au silver. Il est structuré en 4 taches avec d'abord l'interrogation de datagouv pour vérifier que le fichier demandé existe, ensuite la seconde pour le télécharger, l'archiver et le valider, je reviendrai sur ce point quand je vous parlerai de l'incident en prod côté entreprise d'ailleurs. Une précision sur l'archivage justement : le fichier brut reçu est déposé tel quel dans MinIO, mon stockage objet. C'est mon bronze « fichiers » — une archive versionnée de la source, avec un manifeste — qui me permet de rejouer à tout moment depuis le fichier exact reçu. La troisième tache, elle, charge les lignes de ce fichier dans le bronze relationnel, côté Postgres. Et finalement on a la promotion en silver avec toutes les transformations côté SQL, découpage, typage, dédoublonnage.

Ce qui compte avant tout c'est la fiabilisation, on a donc des relances automatiques en cas d'erreur, un SLA et des callbacks pour déclencher des alertes si ça casse. Là en l'occurence j'ai pu lancer ce DAG de mon côté sur les données de data.gouv donc on est sur un vrai traitement pas une simulation. »

**Détail MinIO — bloc séparé (à dire si le jury demande « où/quand intervient MinIO ? », ou à glisser à ta main)** :
« MinIO, c'est mon stockage objet, la couche bronze "fichiers". Concrètement : dès qu'un fichier
arrive, avant tout traitement, je le dépose tel quel dans un bucket, avec un manifeste — sa
taille, son empreinte, l'exécution qui l'a produit. C'est mon archive immuable et versionnée de la
source : si je dois rejouer un traitement, je repars du fichier exact reçu, pas d'une copie
retravaillée. La table bronze de Postgres, elle, contient les lignes de ce fichier pour le
traitement SQL. En résumé : MinIO garde le fichier, Postgres garde les lignes. Et comme MinIO
expose une API S3 standard, une bascule vers un stockage objet cloud se ferait sans réécriture. »

## Diapo 10 — Distribué / Spark (capture) · C4.2.2 · (14:30)
**Aborder** : partage **Postgres/Spark**, l'**INSEE partiel reconstruit** (comme le réel), 3 niveaux, Spark assumé.
**À dire** : « On a parlé d'orchestration, je vais maintenant pouvoir vous parler du rapprochement INSEE/référentiel métier qui consititue la partie distribuée du projet. Cette distribution elle se fait via un cluster Spark, toute la donnée vit dans PostgreSQL, le référentiel comme la donnée INSEE sont en silver. Spark ne stocke rien, il lit juste les tables via JDBC qui fait office de connecteur. Ensuite il fait la jointure de maniètre distribuée et il réécrit le résultat en gold toujours dans Postgres. Sur le principe métier je reprends ce qui est fait côté entreprise, reconstruction d'un pseudo INSEE via date de naissance, sexe, commune de naissance etc. De mon côté dans la mesure ou le Faker me génère des valeurs aléatoires j'ai déporté le rapprochement sur d'autres critères pour avoir quelques correspondances facilement.

Le rapprochement fonctionne sur 3 niveaux de confiance, certain/probable/à vérifier dans le SI chaque niveau correspondait au niveau de correspondance du pseudo INSEE couplé à d'autres critères comme le nom/prenom, la date des dernières prestations etc...

Avec mon raprochement simplifié j'arrivais à 4 162 contrats potentiellement en déshérence, dont 88 millions d'euros au niveau certain. Donc en théorie 4 162 contrats actionnables dès maintenant.

Pour finir je vais clarifier l'usage de Spark, effectivement pour un volume de donnée aussi faible on pouvait totaltement envisagé de rester sur un traitement côté SQL, une bonne indexation aurait suffi, c'est d'ailleurs ce qui est fait côté entreprise. Ici le choix de passer par Spark il s'explique par le besoin de démontrer cette compétence mais aussi pour anticiper un périmètre potentiellement en expension et la volumétrie cumulée si on souhaite rejouer le rapprochement sur tout le silver par exemple. »

## Diapo 11 — CI/CD + déploiement (capture) · C4.2.3 · (17:00)
**Aborder** : les 5 jobs, le déploiement réel GHCR, le 1er run rouge assumé.
**À dire** : « On passe sur l'industrialisation, et c'est un vrai trou que j'ai comblé : à
l'origine, le déploiement était 100 % manuel. J'ai donc construit une CI/CD de zéro.

À chaque fois que je pousse du code, cinq contrôles se déclenchent tout seuls : la qualité du code, les tests, un scan de sécurité des dépendances, la validation que mes DAG s'importent sans erreur, et le
déploiement. 

L'image de l'application est publiée sur un registre, puis re-téléchargée et testée pour vérifier qu'elle démarre sur un environnement vierge. L'idée ici est d'avoir une solution redéployable à l'infini. »

## Diapo 12 — Supervision + alerte (capture) · C4.3.1 · (19:00)
**Aborder** : indicateurs, seuils, alerte réellement délivrée, escalade.
**À dire** : « Ici aussi aucune matière côté entreprise : il n'y avait pas d'alerting, on lisait les logs à la main et c'est aussi ça qui a contribué à l'incident que je vous détaillerai vers la fin de cette soutenance.

De mon côté j'ai mis en place une supervision partielle. Je surveille le statut des traitements, les temps d'exécution, et surtout le taux de rejet des fichiers. Tout est journalisé en base dans la couche ops et quand un traitement échoue, une alerte part vers un destinataire défini avec le type d'erreur et le lien vers le journal. J'ai aussi prévu une escalade : un simple échec notifie l'équipe, mais un dépassement de délai déclencherait plutôt un mail ou l'ouverture d'un ticket par exemple. »

## Diapo 13 — Exploitation + doc · C4.3.2 / C4.3.3 · (21:00)
**Aborder** : feuille de route MCO, secrets/certificats, runbook.
**À dire** : « Une solution ça se maintient dans le temps. J'ai donc formalisé une feuille de
route d'exploitation sous forme de calendrier, c'est déjà quelque chose que j'avais réalisé côté entreprise via Confluence.

Le but est de détailler ce qui est à faire à échéance, par exemple la rotation des mot de passe Airflow chaque trimestre, les montées de version python etc. Cette documentation elle comporte également un runbook. 

Le principe est d'accompagner un utilisateur sur plusieur scénarios, par exemple le crash d'un DAG, un service qui ne démarre pas, que faire pour repartir de 0 proprement. Ici on cherche à s'assurer que le projet peut vivre sans nous, d'ailleurs c'est en partie cette documentation qui m'a permis de remonter le projet de mon côté. »

## Diapo 14 — Recette · C4.4.1 · (23:00) — ⚡ démo live possible
**Aborder** : recette automatisée, la sécurité testée.
**À dire** : « 
Concernant la qualité et la sécurité, dès le projet d'entreprise j'ai été amené à rédiger un cahier de recette. L'idée étant de verouiller les fonctionnalités de la solution derrière des tests pour éviter les régressions. 

Ce cahier comprend 19 tests à la fois sur le fonctionnel, le structurel et surtout sur la sécurité. On retrouve par exemple un test de droits d'accès, la recherche de secrets et mot de passe en dur dans le code et le scan de dépendances. 

Via la CI/CD ces tests tournent à chaque push de mon côté donc on est sur un vrai filet de sécurité. »
**(Option live)** : « Je peux la lancer devant vous. » → `pytest` → 19 verts en < 1 s.

## Diapo 15 — L'incident · C4.4.2 · (24:30) — 🔴 MOMENT FORT
**Aborder** : le récit, la cause racine non triviale. Ralentir.
**À dire** : « 
J'en arrive à la au diagnostic et à la résolution d'un incident technique que j'ai eu la chance de pouvoir aborder via le projet d'entreprise. Pour contextualiser un peu, en vous présentant le dag d'ingestion j'ai parlé d'une tache de récupération et de validation du fichier datagouv, pour ce faire on se fiait aux métadonnées annoncées sur la plateforme, taille, empreinte. 

Ca a très bien marché les deux premiers mois puis le checksum a disparu côté datagouv, du moins à l'endroit ou l'on le récupérait, donc il manquait un élément pour la validation du fichier et le traitement se mettait en erreur faute d'élément à comparer. 

Dans les faits les fichiers restaient exploitables mais notre filet de sécurité était devenu un point de blocage. Une information non contractuelle est devenu une condition bloquante. Faute d'alerting ciblé nous n'avons réalisé l'erreur qu'une semaine après le traitement, bien après les retry au moment ou les gestionnaires en charge des contrôles de correspondance à valider ont constaté que les rapports sortaient vides.»

## Diapo 16 — Le correctif + rejeu · C4.4.2 · (26:30) — ⚡ démo live possible
**Aborder** : l'inversion de logique, le rejeu vert, la leçon.
**À dire** : « Côté entreprise le correctif a été de renverser cette logique de validation afin de valider le contenu réel du fichier, sa structure, volumétrie, son taux de rejet et de ne déclencher que des alertes en cas d'incohérence avec les métadonnées annoncées.

Concrètement un fichier sain est intégré même si datagouv ne nous fournit pas ses métadonnées via notre appel. Dans un second temps nous avons tout de même intégré un mécanisme pointant vers la page "fichiers" qui contient également ces métadonnées de cette façon nous disposons d'un second mécanisme de récupération quand l'API ne nous sert pas les données attendues.

Finalement j'ai ajouté un test de non regression sur cette logique pour m'assurer que cet incident je puisse plus se produire.»

## Diapo 17 — Bilan · (28:00 → 30:00)
**Aborder** : ce qui tourne, limites assumées, ouverture, remerciement.
**À dire** : « Pour conclure. Ce que je retiens, c'est que la chaîne complète tourne et que je
peux le prouver : de l'ingestion jusqu'au résultat métier, en passant par le distribué. La
sécurité est testée, l'intégration continue est verte, et l'incident est rejouable. Je tiens aussi
à assumer mes limites, parce que pour moi c'est ça la maturité d'ingénieur : je n'ai qu'une seule
instance PostgreSQL qui héberge à la fois le métastore Airflow et l'entrepôt, mon job Spark je le
lance encore à la main, et ma supervision reste applicative — elle ne couvre pas l'infrastructure.
Mais ces limites, je sais comment les lever : pour Spark, je le déclencherais directement depuis
Airflow avec un opérateur dédié ; et pour l'infrastructure, je brancherais une stack
Prometheus-Grafana, avec des exporteurs — node-exporter pour la machine, postgres-exporter pour
l'entrepôt, cAdvisor pour les conteneurs — des tableaux de bord et des seuils d'alerte sur le CPU,
la mémoire et le disque. Je vous remercie de votre attention, et je suis à votre disposition pour
vos questions. »

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
