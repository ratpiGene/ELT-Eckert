# Incident — perte des métadonnées déclarées par le producteur

> C4.4.2 — Méthodologie d'investigation et de traitement d'un incident technique.
> Ce document est le récit de référence. Le livrable formalisé est
> `livrables/C4-4-2_methodologie_incident.md`.

## Nature du problème

Le traitement d'ingestion du fichier des personnes décédées validait la
conformité du fichier reçu en comparant ses caractéristiques aux **métadonnées
déclarées** par le producteur sur data.gouv : taille annoncée et empreinte
annoncée. Quand l'une ou l'autre ne correspondait pas, le fichier était rejeté
et le traitement mis en erreur.

Après environ deux mois de fonctionnement nominal, les fichiers récupérés ne
comportaient plus les métadonnées décrites sur la plateforme. Le contrôle
d'entrée n'avait plus rien à comparer et rejetait donc **systématiquement** le
fichier. Le traitement tombait en erreur à chaque exécution, alors que les
fichiers eux-mêmes étaient parfaitement exploitables.

## Symptômes observés

- Échec du traitement à chaque exécution, toujours à la même étape.
- Aucun changement côté code, ni côté infrastructure, dans la période.
- Le fichier téléchargé s'ouvrait et se lisait normalement.

## Investigation

1. **Localiser** l'étape en échec dans le journal d'exécution : le contrôle
   d'entrée, jamais le téléchargement.
2. **Écarter** une régression interne : aucune livraison sur la période, même
   version du code que lors des exécutions réussies.
3. **Rejouer** manuellement le téléchargement et comparer ce que renvoyait le
   catalogue à ce qu'attendait le contrôle : les champs de métadonnées
   attendus n'étaient plus renseignés.
4. **Vérifier** le fichier lui-même : structure, volumétrie et contenu
   conformes à la spécification.
5. **Conclure** : le défaut est côté producteur, mais la vulnérabilité est de
   notre côté — nous avions fait d'une métadonnée déclarative une condition
   bloquante.

## Cause racine

Une dépendance à un élément **non contractuel** de la source. Les métadonnées
publiées sur un portail open data sont un confort, pas un engagement : le
producteur peut cesser de les publier sans préavis et sans que la donnée
elle-même change.

## Actions mises en œuvre

| Action | Nature | Effet |
|---|---|---|
| Rendre les métadonnées non bloquantes | Correctif immédiat | Rétablissement du service |
| Valider le **contenu** : structure, longueur de ligne, typage, volumétrie, taux de rejet | Correctif structurel | La validation ne dépend plus de la source |
| Transformer les écarts déclaré/réel en alertes journalisées | Supervision | On garde l'information sans en dépendre |
| Ajouter un test de non-régression sur le cas « métadonnées absentes » | Recette | L'incident ne peut pas revenir silencieusement |

Le correctif est implémenté dans `src/eckert/validation/contract.py` et le test
de non-régression est `tests/test_contract.py::test_metadonnees_absentes_ne_bloquent_pas`.

## Communication aux parties prenantes

- **Équipe data** : notification immédiate de l'échec, puis point de situation
  une fois la cause identifiée.
- **Métier / conformité** : information sur le décalage de mise à disposition
  des résultats et sur l'absence d'impact sur la qualité des données produites
  — le point sensible sur une obligation réglementaire.
- **Producteur de la donnée** : signalement de l'anomalie de publication.
- **Après remise en service** : compte rendu écrit avec cause racine et mesures
  prises, pour éviter que la correction ne reste dans la mémoire d'une
  personne.

## Enseignement

Une source externe n'est jamais un contrat. Ce qui vient du producteur se
vérifie, ce dont on dépend se teste, et ce qu'on ne maîtrise pas ne doit pas
pouvoir arrêter la chaîne. Cette règle a été rejouée sur les autres flux
externes du périmètre.
