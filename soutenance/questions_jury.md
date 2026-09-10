# Préparation aux questions du jury (15 min)

Règle de réponse : **une phrase directe, puis un fait, puis une limite honnête.** Ne jamais
surjouer la maîtrise d'un outil peu pratiqué. Deux questions probables par compétence.

---

## Questions transverses (les plus probables)

**Q. Quelle est la part réellement construite par vous, et la part reprise de l'entreprise ?**
> La plateforme est **entièrement reconstruite** par moi pour ce dossier. Du vécu Prévifrance je
> reprends le **contexte métier** (obligation Eckert), l'**incident** réel et l'**étude Snowflake**
> non retenue. Le code, l'infra, la CI, les tests et le job Spark sont neufs. Le fichier INSEE est
> réel ; le référentiel adhérents est synthétique (Faker). Limite : ce n'est pas le SI de
> l'entreprise, et je le dis dès la diapositive 2.

**Q. Où sont les données personnelles, qui y accède, RGPD ?**
> Aucune donnée personnelle réelle d'adhérent : le référentiel est synthétique. Le fichier des
> décès est une donnée **publique** de l'INSEE. Accès cloisonné : le pipeline écrit (`elt_writer`),
> le métier lit la seule couche `gold` (`elt_reader`), jamais le brut — c'est **testé** (REC-SEC).
> La durée de conservation et la purge figurent dans la feuille de route d'exploitation (C4.3.2).

**Q. Qu'est-ce qui n'a pas fonctionné, et qu'en avez-vous tiré ?**
> Le premier run de CI est tombé (format, puis conflit d'install Airflow). Je l'ai gardé comme
> preuve : les garde-fous mordent. Leçon : installer Airflow **avec ses contraintes** et ne pas
> supposer qu'un check local suffit après une dernière édition.

---

## C4.1.1 — Analyse

**Q. Pourquoi une plateforme locale plutôt que le cloud ?**
> Contrainte de coût nulle et besoin **mensuel à faible intensité** : le local conteneurisé est le
> mieux aligné. Le cloud reste ma trajectoire documentée de montée en charge (C4.1.2).

**Q. Comment l'architecture se comporte-t-elle si le volume est ×10 ?**
> Le distribué (Spark) absorbe le rapprochement ; le point de tension serait l'instance Postgres
> unique. À ×10 je séparerais métastore et entrepôt, et je passerais MinIO/Postgres sur un
> stockage dimensionné — c'est dans `LIMITES.md`.

## C4.1.2 — Composants et coûts

**Q. Pourquoi Snowflake / Fabric n'a-t-il pas été retenu (contexte réel) ?**
> Décision collégiale équipe data + DBA : coût récurrent injustifié sur ce volume, sensibilité des
> données (santé/identité), maturité sur l'existant SQL Server, pas de gain décisif. Chiffrage en
> ordre de grandeur : 80–250 €/mois selon l'usage, contre un coût quasi nul en local.

**Q. Comment traitez-vous le vendor lock-in ?**
> Par des interfaces standard : S3 (MinIO), SQL (Postgres), PySpark. Le point le plus propriétaire
> est le YAML GitHub Actions, dont la réécriture est marginale.

## C4.2.1 — Entrepôt

**Q. Pourquoi quatre couches et deux rôles ?**
> Les couches séparent responsabilités et droits : le brut n'est jamais exposé au métier. Deux
> rôles appliquent le moindre privilège — et je le **prouve** : `elt_reader` ne peut ni écrire en
> gold ni lire bronze (tests SEC-02/03 verts).

**Q. Comment garantissez-vous la rapidité ?**
> Index sur les clés de jointure et de filtre, chargement par `COPY`, transformations
> ensemblistes dans le moteur, et distribué quand le volume le justifie.

## C4.2.2 — Pipelines

**Q. Pourquoi Spark ici, alors qu'un Postgres bien indexé traiterait ce volume ? (piège)**
> Sur le **volume mensuel seul, Postgres suffirait — je l'assume.** Spark se justifie par la
> **volumétrie cumulée** (dizaines de M de lignes), la trajectoire de croissance et la maîtrise de
> la fenêtre de traitement. C'est un choix de donnée, pas de vitrine.

**Q. Votre « temps réel » est-il du streaming ?**
> Non, et je le nomme précisément : **traitement au fil de l'eau** déclenché à l'arrivée d'un
> fichier. La source est mensuelle ; un Kafka n'aurait aucun sens métier (`LIMITES.md`).

## C4.2.3 — CI/CD

**Q. Comment une modification est-elle testée avant production ? Retour arrière ?**
> Tout `push` déclenche 5 jobs : lint, tests+couverture, scan de sécurité, import des DAG, build
> d'image. Rouge = pas de fusion. Retour arrière = redéploiement du commit précédent (image
> taguée par SHA). Limite : pas d'environnement cible exposé depuis un runner public.

**Q. Le job de sécurité, concrètement ?**
> `pip-audit --strict` : **une** CVE connue fait rougir la CI (ça m'a obligé à monter requests,
> python-dotenv, pytest), plus un refus de tout `.env` versionné, plus l'image sans privilèges.

## C4.3.1 — Supervision

**Q. Que se passe-t-il si le traitement échoue à 3 h du matin ?**
> Le `on_failure_callback` journalise en `ops` et envoie un webhook à l'équipe. Un dépassement de
> SLA (plus grave, réglementaire) escalade par courriel. Les `retries` avec backoff gèrent le
> transitoire. Reprise via *Clear* de la tâche.

**Q. Pourquoi pas Prometheus/Grafana ?**
> Arbitrage de délai. La supervision **applicative** couvre le critère (indicateurs, seuils,
> canaux, escalade, visualisation Airflow + journal). L'infra est une évolution notée.

## C4.3.2 — Exploitation

**Q. Comment gérez-vous les secrets dans le temps ?**
> Rotation trimestrielle : `.env` + secrets GitHub + `ALTER ROLE … PASSWORD`, redémarrage,
> journalisation. Immédiate en cas de compromission. Certificats TLS renouvelés 30 j avant terme.

**Q. Que surveillez-vous en priorité chaque mois ?**
> Le **taux de rejet** : sa dérive est le signal précoce d'un changement de format côté producteur
> — exactement le déclencheur de l'incident.

## C4.3.3 — Documentation

**Q. Un successeur peut-il reprendre sans vous ?**
> Oui : procédure de configuration depuis zéro, exécution bout-en-bout commande par commande, et
> un **runbook** des incidents courants (DAG en échec, Spark, rotation de secret, reset propre).

## C4.4.1 — Recette

**Q. Vos tests couvrent-ils la sécurité, pas seulement le fonctionnel ?**
> Oui : 19 tests automatisés, dont 6 de sécurité (droits lecteur, non-exposition de secrets, scan
> de dépendances). Rejoués à chaque `push`. Ce n'est pas un instantané, c'est un filet permanent.

**Q. Comment testez-vous les droits ?**
> Le rôle `elt_reader` tente réellement un INSERT en gold et un SELECT en bronze → les deux lèvent
> `InsufficientPrivilege`. Test exécuté contre la base réelle (preuve versionnée).

## C4.4.2 — Incident

**Q. Racontez l'incident et sa cause racine.**
> Le contrôle d'entrée validait le fichier sur ses **métadonnées déclarées**. Le producteur a
> cessé de les publier : rejet systématique pendant des jours, alors que les fichiers étaient bons.
> Cause racine : avoir promu une donnée **non contractuelle** en condition bloquante.

**Q. Comment garantissez-vous qu'il ne revienne pas ?**
> La validation porte désormais sur le **contenu**, les métadonnées ne font qu'alerter, et un
> **test de non-régression** verrouille le cas « métadonnées absentes ». Rejeu vert prouvé
> (`preuves/C4-4-2_incident_rejeu.txt`).
