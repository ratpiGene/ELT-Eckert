# C4.3.1 — Supervision et système d'alertes

> **Compétence visée.** Mettre en place la supervision de l'infrastructure : **éléments et
> indicateurs surveillés**, **choix et configuration** des outils, **visualisation**, et un
> **système d'alertes** (seuils, canaux, destinataires, escalade).

> **Trou comblé.** Dans le vécu Prévifrance, la supervision se limitait à des **logs consultés à
> la main** (SQL Server Agent, SSRS). Aucun alerting outillé. Tout ce qui suit est construit.

---

## 1. Ce qui est surveillé

La supervision porte sur la **chaîne de traitement** (le critère de la grille est applicatif,
pas infra — voir la limite §6), à trois niveaux :

| Niveau | Élément surveillé | Où |
|---|---|---|
| **Exécution** | succès/échec de chaque tâche, tentatives, durée | Airflow + `ops.journal_execution` |
| **Respect du délai** | dépassement de SLA sur l'étape sensible | Airflow SLA + callback |
| **Qualité de la donnée** | lignes lues / rejetées, taux de rejet, volumétrie, écarts de métadonnées | `ops.journal_execution`, `ops.controle_qualite` |

---

## 2. Indicateurs et seuils

| Indicateur | Source | Seuil / règle | Action |
|---|---|---|---|
| Statut de tâche | callback Airflow | `ECHEC` | alerte immédiate (webhook) + journal |
| Durée d'étape | SLA Airflow | `> 30 min` sur la validation | escalade (courriel) |
| Taux de rejet | `valider_fichier` | `> 2 %` | **blocage** du fichier + journal `ECHEC` |
| Volumétrie | `valider_fichier` | `< 1 000 lignes` | **blocage** (fichier suspect) |
| Métadonnées absentes | ingestion | présence | **alerte** non bloquante (cf. incident C4.4.2) |

Les seuils sont **explicites et centralisés** (`TAUX_REJET_MAX`, `LIGNES_MINIMUM` dans
`src/eckert/validation/contract.py`), donc auditables et modifiables sans toucher à la logique.

---

## 3. Choix et configuration des outils

### 3.1 Airflow comme socle de supervision

Choix assumé : **réutiliser l'orchestrateur** comme socle de supervision, plutôt que d'ajouter
une pile Prometheus/Grafana que le délai ne permettait pas de fiabiliser. Configuration
(`dags/eckert_ingestion.py`) :

```python
ARGUMENTS_DEFAUT = {
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "on_failure_callback": alerter_echec,     # ─► alerte + journal
    "execution_timeout": timedelta(hours=2),
}
@dag(..., sla_miss_callback=alerter_sla)       # ─► escalade sur dépassement de SLA
def eckert_ingestion_deces():
    @task(sla=timedelta(minutes=30))           # ─► SLA sur l'étape sensible
    def recuperer_catalogue(...): ...
```

### 3.2 Le journal en base — la mémoire de la supervision

`ops.journal_execution` reçoit une ligne par étape (`run_id`, `etape`, `statut`, `lignes_lues`,
`lignes_rejetees`, `duree_secondes`, `message`, `horodatage`). C'est la **source de vérité
historisée** : on y lit ce qui s'est passé, quand, et avec quel volume. La fonction
`journaliser` (`src/eckert/supervision/alerte.py`) est écrite pour **ne jamais faire tomber le
traitement** si la journalisation échoue (le contrôle ne doit pas casser le contrôlé).

---

## 4. Système d'alertes : seuils, canaux, destinataires, escalade

Trois canaux, **par ordre de gravité croissante** (`src/eckert/supervision/alerte.py`) :

| Canal | Déclencheur | Destinataire | Rôle |
|---|---|---|---|
| **Journal `ops`** | chaque étape | supervision / tableau de bord | trace systématique |
| **Webhook** | échec de tâche (`on_failure_callback`) | équipe data | notification immédiate |
| **Courriel** | dépassement de SLA (`sla_miss_callback`) | responsable + équipe | **escalade** |

```python
def alerter_echec(contexte):        # échec de tâche
    corps = f"DAG {dag_id} — tâche {tache} en échec (tentative {essai}) ..."
    journaliser(run_id, etape=tache, statut="ECHEC", message=corps)
    _notifier(f"[ECKERT] Échec {dag_id}.{tache}", corps)   # webhook

def alerter_sla(dag, task_list, ...):   # dépassement de SLA -> escalade
    _notifier("[ECKERT] Dépassement de SLA", corps)
```

**Escalade** : un échec ponctuel notifie l'équipe (webhook) ; un **dépassement de délai** —
plus grave pour une obligation réglementaire — déclenche la voie courriel vers le responsable.
Les canaux sont configurés par variables d'environnement (`ALERT_WEBHOOK_URL`,
`ALERT_EMAIL_TO`) : **aucun secret dans le code**, et l'envoi réel se désactive en laissant la
variable vide (mode local/démonstration).

---

## 5. Visualisation

- **Airflow** : vues *Grid* et *Graph* du DAG (statut par tâche, historique des exécutions,
  durées, logs par tentative) — la visualisation opérationnelle immédiate.
- **Tableau de bord qualité** : requêtes sur `ops.journal_execution` et `ops.controle_qualite`
  (taux de rejet dans le temps, volumétrie par exécution, alertes de métadonnées). Exploitable
  directement en SQL, ou branché sur Metabase (même rôle lecture seule).

**Preuve** : `preuves/C4-3-1_airflow_grid.png` (Grid view), `preuves/C4-3-1_journal_ops.txt`
(extrait du journal), `preuves/C4-3-1_alerte_echec.png` (alerte sur échec provoqué).

---

## 6. Limite assumée

Pas de **supervision d'infrastructure** (CPU, mémoire, disque via Prometheus/Grafana) :
arbitrage de délai. La supervision **applicative** couvre le critère de la grille (éléments,
indicateurs, outils, visualisation, alertes). L'ajout d'un exporteur et de tableaux de bord
d'infra est décrit dans `LIMITES.md` comme évolution.

---

## 7. Couverture des critères de la compétence C4.3.1

| Critère de la grille | Section | Preuve |
|---|---|---|
| **Éléments et indicateurs** surveillés | §1, §2 | `ops.journal_execution` |
| **Choix et configuration** des outils | §3 | `dags/eckert_ingestion.py` |
| **Visualisation** | §5 | `preuves/C4-3-1_airflow_grid.png` |
| Système d'**alertes** (seuils) | §2, §4 | seuils dans `contract.py` |
| Alertes : **canaux, destinataires, escalade** | §4 | `src/eckert/supervision/alerte.py` |
