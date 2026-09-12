# Support projetable — plan (soutenance 30 min)

**Format révisé : 30 minutes** de présentation + 15 min de questions.
**17 diapositives projetées** (~1,7 min/diapo) + 3 annexes **masquées** pour les questions.
Une idée par diapo, **titre assertif**, bandeau de compétence, ≤ 5 lignes projetées — le reste
se dit (notes de commentaire). Fichier généré : `soutenance/support_eckert.pptx`.

## Minutage (30 min)

| Temps | Séquence | Diapos | Compétences |
|---|---|---|---|
| 0-2 min | Contexte + **périmètre honnête** | 1-3 | — |
| 2-5 min | Analyse (besoins, contraintes, existant) | 4 | C4.1.1 |
| 5-9 min | Composants + **coûts** | 5-6 | C4.1.2 |
| 9-11 min | Entrepôt (couches, droits testés) | 7 | C4.2.1 |
| 11-17 min | **Les trois pipelines dont le distribué** | 8-10 | C4.2.2 |
| 17-19 min | CI/CD + déploiement | 11 | C4.2.3 |
| 19-23 min | Exploitation (supervision, MCO, doc) | 12-13 | C4.3.1/2/3 |
| 23-28 min | Recette + **incident rejoué** | 14-16 | C4.4.1/2 |
| 28-30 min | Bilan | 17 | — |
| +15 min | Questions, appui annexes A1-A3 | (masquées) | toutes |

## Les 17 diapositives

1. **Titre** — Plateforme ELT Eckert.
2. Une obligation légale : identifier les adhérents décédés — *Contexte*.
3. Une plateforme reconstruite sur un contexte réel, et mon rôle — *Contexte (honnêteté)*.
4. Analyse : besoins, contraintes, et les quatre trous à combler — *C4.1.1*.
5. Des composants open source, locaux, portables vers le cloud — *C4.1.2*.
6. Trois scénarios de coût, avec hypothèses explicites — *C4.1.2*.
7. Un entrepôt en 4 couches, avec des droits testés — *C4.2.1*.
8. Trois méthodes de pipeline, dont le distribué — *C4.2.2*.
9. Orchestration : le DAG réel tourne vert sur le fichier INSEE — *C4.2.2* (capture).
10. Distribué : Spark détecte 4 162 contrats, 88 M€ en CERTAIN — *C4.2.2* (capture).
11. CI/CD : cinq jobs verts et un déploiement réel sur registre — *C4.2.3* (capture).
12. Supervision : indicateurs, seuils, et une alerte réellement délivrée — *C4.3.1* (capture).
13. Exploitation : un calendrier de MCO et une doc réutilisable — *C4.3.2/3.3*.
14. Une recette automatisée : 19 tests, dont la sécurité — *C4.4.1*.
15. L'incident : la confiance aveugle dans les métadonnées — *C4.4.2* (**moment fort**).
16. Le correctif : valider le contenu, pas la promesse — rejeu vert — *C4.4.2*.
17. Bilan : ce qui tourne, les limites assumées — *Bilan*.

Annexes masquées : **A1** schéma entrepôt · **A2** coûts détaillés · **A3** workflow CI/CD.

## Règles

- **4 démos live possibles et sûres** (< 1 s, sans réseau) : `pytest` (diapo 14) et le **rejeu
  de l'incident** (diapo 16). Le reste passe par les captures intégrées.
- Le pic est **15-16** (l'incident). Le ralentir, le raconter.
- Toute séquence qui déborde de +30 s est coupée, pas accélérée (le budget est serré à 30 min).
- Régénérer après modif du script : `PYTHONPATH=. python -m tools.build_pptx`.
