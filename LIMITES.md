# Limites assumées

Ce fichier existe parce qu'un dossier qui ne présente aucune limite n'est pas
crédible. Chaque entrée est un choix, pas un oubli — et se dit à l'oral.

| Limite | Raison | Ce qu'il faudrait pour la lever |
|---|---|---|
| Une seule instance PostgreSQL héberge le métastore Airflow et l'entrepôt | Empreinte mémoire d'un poste de travail | Deux instances séparées, ou un service managé |
| Pas de supervision d'infrastructure (Prometheus / Grafana) | Arbitrage de délai : la supervision applicative couvre le critère de la grille | Ajouter un exporteur et des tableaux de bord d'infra |
| Rapprochement probabiliste sur nom + prénom + date de naissance | Aucun identifiant national dans le périmètre | Un identifiant pivot, ou un moteur de rapprochement flou outillé |
| Pas de véritable streaming (Kafka) | Le fichier source est publié mensuellement : un flux permanent n'aurait aucun sens métier | Une source événementielle réelle |
| Déploiement continu : l'image est **construite, publiée sur GHCR et revérifiée par pull**, mais pas **mise en service automatiquement** sur un environnement cible | Aucun cluster de production exposé depuis un runner public | Un environnement de recette joignable + un secret de déploiement (`pull` → run sur l'hôte cible) |
| Référentiel adhérents synthétique | Aucune donnée réelle ne peut ni ne doit sortir de l'entreprise | Rien : c'est une limite définitive et volontaire |
| Volumétrie de démonstration inférieure à une production réelle | Contrainte du poste de travail | Un cluster dimensionné |
| Job Spark **soumis manuellement** (`spark-submit`), non déclenché par Airflow | L'image Airflow ne contient pas `spark-submit` ; l'ajouter alourdissait le Compose sur le délai | `SparkSubmitOperator` + connexion Spark, ou un `DockerOperator` |
| Image Spark `bitnamilegacy/spark:3.5.3` | Bitnami a retiré les tags non-`latest` de `bitnami/*` en 2025 ; le namespace `bitnamilegacy` est figé mais fonctionnel | Bascule vers l'image officielle `apache/spark` (commandes master/worker explicites) |
| Rapprochement démontré sur un **fichier décès synthétique à recouvrement contrôlé** | Les identités du vrai fichier INSEE ne recoupent pas le référentiel synthétique | Un référentiel dérivé en partie du fichier réel, ou un pivot d'identité |
