# C4.4.2 — Méthodologie d'investigation et de traitement d'un incident

> **Compétence visée.** Décrire la méthodologie de traitement d'un incident technique : **nature
> du problème**, **actions selon les scénarios**, **communication aux parties prenantes**,
> **résultats attendus** et **résolution effective**.

> **Incident réel.** Cet incident est **vécu** (traitement Eckert en production chez Prévifrance).
> Il est **rejoué dans la plateforme reconstruite**. Récit de référence :
> [`docs/incident_metadonnees.md`](../docs/incident_metadonnees.md).

---

## 1. Nature du problème

Le traitement d'ingestion validait la conformité du fichier des personnes décédées en comparant
ses caractéristiques aux **métadonnées déclarées** par le producteur sur data.gouv (taille et
empreinte annoncées). Après environ **deux mois** de fonctionnement nominal, le producteur a
**cessé de publier ces métadonnées**. Le contrôle d'entrée n'avait plus rien à comparer et
**rejetait systématiquement** le fichier. Le traitement tombait en erreur à chaque exécution,
**alors que les fichiers eux-mêmes étaient parfaitement exploitables**.

**Symptômes** : échec à chaque exécution, toujours à la même étape (contrôle d'entrée) ; aucun
changement de code ni d'infrastructure sur la période ; fichier téléchargé lisible normalement.

---

## 2. Investigation — méthode

| # | Étape | Constat |
|---|---|---|
| 1 | **Localiser** l'étape en échec (journal d'exécution) | le contrôle d'entrée, jamais le téléchargement |
| 2 | **Écarter** une régression interne | aucune livraison sur la période, même version du code |
| 3 | **Rejouer** le téléchargement, comparer catalogue attendu / reçu | les champs de métadonnées attendus ne sont plus renseignés |
| 4 | **Vérifier** le fichier lui-même | structure, volumétrie et contenu conformes |
| 5 | **Conclure** | défaut **côté producteur**, mais **vulnérabilité de notre côté** : une métadonnée déclarative avait été promue en condition bloquante |

## 3. Cause racine

Une **dépendance à un élément non contractuel** de la source. Les métadonnées publiées sur un
portail open data sont un **confort, pas un engagement** : le producteur peut cesser de les
publier sans préavis, sans que la donnée elle-même change. Nous avions transformé cette
information de confort en **point de rupture**.

---

## 4. Actions selon les scénarios

| Scénario | Décision | Action |
|---|---|---|
| Métadonnées **absentes** | ne pas bloquer | alerte journalisée, validation par le contenu |
| Métadonnées **présentes mais divergentes** (taille/empreinte ≠ réel) | ne pas bloquer | alerte d'**écart déclaré/réel**, on garde l'information sans en dépendre |
| Contenu **non conforme** (structure, volumétrie, taux de rejet) | **bloquer** | rejet motivé + journal `ECHEC` + alerte |

Le principe directeur : **ce qu'on ne maîtrise pas ne doit pas pouvoir arrêter la chaîne ; ce
dont on dépend se valide sur le contenu.**

### 4.1 Le correctif, en une ligne de code

Avant (V1), l'absence de métadonnée levait une exception. Après (V2,
`src/eckert/validation/contract.py`), elle devient une alerte :

```python
def controler_metadonnees(ecarts, metadonnees_absentes):
    alertes = []
    if metadonnees_absentes:
        alertes.append("Le producteur ne publie plus les métadonnées suivantes : "
                       + ", ".join(metadonnees_absentes)
                       + ". Validation assurée par le contenu du fichier.")
    alertes.extend(f"Écart déclaré/réel : {e}" for e in ecarts)
    return alertes          # ces constats ALERTENT, ils ne bloquent plus jamais
```

La validation repose désormais sur le **contenu réel** (`valider_fichier`) : longueur de ligne,
typage des dates, sexe, **volumétrie minimale**, **taux de rejet plafonné**.

---

## 5. Communication aux parties prenantes

| Partie prenante | Message | Moment |
|---|---|---|
| **Équipe data** | notification immédiate de l'échec, puis point de situation à l'identification de la cause | dès l'échec / après diagnostic |
| **Métier / conformité** | décalage de mise à disposition des résultats, **absence d'impact sur la qualité** des données produites (point sensible car obligation réglementaire) | pendant l'incident |
| **Producteur de la donnée** | signalement de l'anomalie de publication | pendant l'incident |
| **Tous (compte rendu écrit)** | cause racine + mesures prises, pour ne pas laisser la correction dans la mémoire d'une seule personne | après remise en service |

---

## 6. Résultats attendus et résolution effective

**Résultat attendu** : rétablir le service sans dégrader la qualité, et rendre l'incident
**non reproductible silencieusement**.

**Résolution effective, rejouée dans la plateforme** (`preuves/C4-4-2_incident_rejeu.txt`) :

```
[CAS INCIDENT] Fichier sain, métadonnées absentes côté producteur :
   -> CONFORME — 1050 lignes lues, 0 rejetées (0.00%)
   -> conforme=True | ALERTE non bloquante : « Le producteur ne publie plus les métadonnées … »
[CAS DÉGRADÉ]  30 lignes tronquées      -> rejetées au niveau ligne (longueur_insuffisante)
[CAS DÉGRADÉ]  dates de décès impossibles -> rejetées (date_deces_invalide)
[CAS BLOQUANT] taux de rejet 23.08 % > 2 % -> NON CONFORME, fichier bloqué
```

Le service est rétabli (le fichier sain passe), la qualité reste garantie (un vrai fichier
corrompu est toujours bloqué), et un **test de non-régression** verrouille le cas :
`tests/test_contract.py::test_metadonnees_absentes_ne_bloquent_pas`.

---

## 7. Enseignement

Une source externe n'est **jamais un contrat**. Ce qui vient du producteur se vérifie, ce dont
on dépend se teste, et ce qu'on ne maîtrise pas ne doit pas pouvoir arrêter la chaîne. Cette
règle a été généralisée aux autres flux externes du périmètre.

---

## 8. Couverture des critères de la compétence C4.4.2

| Critère de la grille | Section | Preuve |
|---|---|---|
| **Nature du problème** | §1 | `docs/incident_metadonnees.md` |
| **Actions selon les scénarios** | §4 | `src/eckert/validation/contract.py` |
| **Communication aux parties prenantes** | §5 | tableau §5 |
| **Résultats attendus** | §6 | — |
| **Résolution effective** | §6 | `preuves/C4-4-2_incident_rejeu.txt`, test de non-régression |
