# C4.4.1 — Cahier de recette

> **Compétence visée.** Élaborer et exécuter un cahier de recette couvrant **toutes les
> fonctionnalités attendues**, avec des tests **fonctionnels, structurels ET de sécurité**, et
> consigner les **résultats obtenus**.

> **Trou comblé.** Dans le vécu Prévifrance, les contrôles de cohérence et la revue DBA
> existaient mais **n'étaient pas consignés**, et la sécurité n'était pas testée. Ce cahier est
> formalisé et **automatisé** (rejouable dans la CI à chaque modification).

---

## 1. Périmètre : les fonctionnalités attendues

| # | Fonctionnalité | Couverte par |
|---|---|---|
| F1 | Ingérer un fichier décès et le tracer en bronze | pipeline + REC-STR-* |
| F2 | Valider la conformité **par le contenu** (structure, typage, volumétrie) | REC-STR-01→08 |
| F3 | Ne pas dépendre des métadonnées déclarées (incident) | REC-FON-01, REC-FON-02 |
| F4 | Typer, nettoyer, dédoublonner vers silver | pipeline (bronze→silver) |
| F5 | Rapprocher décès × contrats à 3 niveaux de confiance | job Spark → gold |
| F6 | Exposer au métier une vue priorisée, en lecture seule | REC-SEC-02, vue gold |
| F7 | Cloisonner les accès (moindre privilège) | REC-SEC-04, REC-SEC-05 |
| F8 | Ne versionner aucun secret | REC-SEC-01, REC-SEC-03 |

---

## 2. Méthode

Les tests sont **automatisés** (`pytest`) et **rejoués en CI** (job `tests`). Chaque cas porte
un identifiant, un attendu, un obtenu et un verdict. Les tests de sécurité qui nécessitent
l'entrepôt sont exécutés contre le PostgreSQL réel ; ils sont **ignorés proprement** si la base
n'est pas joignable (CI sans base), ce qui est tracé.

Exécution de référence : `preuves/C4-4-1_recette_complete.txt` (**19 tests, 19 réussis**, base
joignable).

---

## 3. Tests fonctionnels

| ID | Cas | Attendu | Obtenu | Verdict |
|---|---|---|---|---|
| REC-FON-01 | Fichier sain, **métadonnées absentes** (l'incident) | CONFORME + alerte non bloquante | conforme, alerte levée | ✅ |
| REC-FON-02 | Écart taille déclarée / réelle | alerte, **pas** de blocage | 1 alerte, non bloquant | ✅ |
| REC-FON-03 | Jour de naissance/décès inconnu (`00`) | accepté (ramené au 1er) | 0 rejet | ✅ |
| REC-FON-04 | Restitution métier priorisée (vue gold) | lecture possible, ordre CERTAIN d'abord | 10 lignes lues par `elt_reader` | ✅ |

*(tests : `test_metadonnees_absentes_ne_bloquent_pas`, `test_ecart_de_taille_declare_leve_une_alerte_sans_bloquer`, `test_jour_inconnu_reste_accepte`, preuve `C4-2-1_vue_restitution.txt`)*

---

## 4. Tests structurels

| ID | Cas | Attendu | Obtenu | Verdict |
|---|---|---|---|---|
| REC-STR-01 | Fichier nominal (≥ 1000 lignes valides) | conforme, 0 rejet | conforme | ✅ |
| REC-STR-02 | Longueur de ligne = spécification (176) | vrai | 176 | ✅ |
| REC-STR-03 | Fichier vide | bloquant | « fichier vide » | ✅ |
| REC-STR-04 | Fichier absent | bloquant | bloquant | ✅ |
| REC-STR-05 | Volumétrie < 1000 | bloquant | « volumétrie… » | ✅ |
| REC-STR-06 | Ligne tronquée | rejetée (longueur_insuffisante) | 1 rejet | ✅ |
| REC-STR-07 | Date de décès impossible | rejetée (date_deces_invalide) | 1 rejet | ✅ |
| REC-STR-08 | Sexe invalide | rejeté (sexe_invalide) | 1 rejet | ✅ |
| REC-STR-09 | Taux de rejet > 2 % | **bloquant** | 17 % → bloqué | ✅ |
| REC-STR-10 | Encodage inattendu (utf-8 / latin-1) | ne plante pas | 2/2 OK | ✅ |

*(tests : `tests/test_contract.py` — voir noms exacts dans la preuve)*

---

## 5. Tests de sécurité

| ID | Cas | Attendu | Obtenu | Verdict |
|---|---|---|---|---|
| REC-SEC-01 | Aucun fichier `.env` versionné | vrai | 0 fichier | ✅ |
| REC-SEC-02 | `elt_reader` tente un INSERT en gold | refusé (`InsufficientPrivilege`) | refusé | ✅ |
| REC-SEC-03 | `.gitignore` couvre `.env`, `*.pem`, `*.key` | vrai | vrai | ✅ |
| REC-SEC-04 | `elt_reader` tente un SELECT en bronze | refusé (`InsufficientPrivilege`) | refusé | ✅ |
| REC-SEC-05 | Pas de mot de passe en dur dans `src/` | vrai (lecture par environnement) | vrai | ✅ |
| REC-SEC-06 | Scan de vulnérabilités des dépendances | 0 CVE connue (`pip-audit --strict`) | « No known vulnerabilities found » | ✅ |

*(tests : `tests/test_securite.py` + job `securite` de la CI, preuves `C4-4-1_tests_securite.txt`, `C4-2-3_pip_audit.txt`)*

---

## 6. Synthèse

| Catégorie | Cas | Réussis |
|---|---|---|
| Fonctionnels | 4 | 4 |
| Structurels | 10 | 10 |
| Sécurité | 6 | 6 (5 pytest + 1 CI) |
| **Total automatisé** | **19 (pytest) + audit CI** | **100 %** |

Le cahier est **rejoué automatiquement à chaque `push`** (CI verte, `C4-2-3_ci_jobs.txt`) : la
recette n'est pas un instantané, c'est un filet permanent.

---

## 7. Couverture des critères de la compétence C4.4.1

| Critère de la grille | Section | Preuve |
|---|---|---|
| **Toutes les fonctionnalités** attendues | §1 | matrice §3-§5 |
| Tests **fonctionnels** | §3 | `test_contract.py` |
| Tests **structurels** | §4 | `test_contract.py` |
| Tests **de sécurité** | §5 | `test_securite.py`, job CI `securite` |
| Tests **exécutés** avec **résultats** | §2, §6 | `preuves/C4-4-1_recette_complete.txt` |
