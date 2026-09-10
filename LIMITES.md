# Limites assumées

Ce fichier existe parce qu'un dossier qui ne présente aucune limite n'est pas
crédible. Chaque entrée est un choix, pas un oubli — et se dit à l'oral.

| Limite | Raison | Ce qu'il faudrait pour la lever |
|---|---|---|
| Une seule instance PostgreSQL héberge le métastore Airflow et l'entrepôt | Empreinte mémoire d'un poste de travail | Deux instances séparées, ou un service managé |
| Pas de supervision d'infrastructure (Prometheus / Grafana) | Arbitrage de délai : la supervision applicative couvre le critère de la grille | Ajouter un exporteur et des tableaux de bord d'infra |
| Rapprochement probabiliste sur nom + prénom + date de naissance | Aucun identifiant national dans le périmètre | Un identifiant pivot, ou un moteur de rapprochement flou outillé |
| Pas de véritable streaming (Kafka) | Le fichier source est publié mensuellement : un flux permanent n'aurait aucun sens métier | Une source événementielle réelle |
| Déploiement continu limité à la construction et au contrôle de l'image | Pas d'environnement cible exposé depuis un runner public | Un environnement de recette joignable et un secret de déploiement |
| Référentiel adhérents synthétique | Aucune donnée réelle ne peut ni ne doit sortir de l'entreprise | Rien : c'est une limite définitive et volontaire |
| Volumétrie de démonstration inférieure à une production réelle | Contrainte du poste de travail | Un cluster dimensionné |
