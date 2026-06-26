# Dashboard MC & Animateurs - Flask App

Application Flask pour suivre la qualité des **masterclasses** et des **animateurs** : tableaux de bord, leaderboards (tout temps & 30 jours), recherche par rôle, récap Slack, et affichage stylisé des avis négatifs. Elle inclut également un module de réévaluation du temps des exercices.

---

## Fonctionnalités

* **Navbar Bootstrap** avec Login/Logout à droite et lien vers le module de réévaluation
* **Dashboard** :
  * Wall of Fame / Wall of Not Fame
  * Commentaires négatifs formatés, avec liens Meeting & User
* **Animateurs** :
  * Liste groupée par **Rôle** (+ recherche par nom)
  * Page **détail animateur** (stats globales & 30 jours)
* **Masterclasses** :
  * Liste de masterclasses cliquables
  * Page **détail MC** (stats globales & 30 jours)
* **Leaderboards** (2 colonnes configurables) :
  * Animateurs / 30 jours / Masterclasses / 30 jours
  * **Slider** du seuil minimal de sessions (une session = Meeting ID unique)
* **Slack Bot** :
  * 3 boutons pour envoyer les récap (Top, Not Top, Commentaires négatifs)
* **Time Reevaluation (Time Reeval)** :
  * Comparaison du temps recommande et reel pour les exercices
  * Authentification separee via les identifiants Nexus
  * Ajout de sources de donnees par User ID ou Cohort ID
  * Chargement rapide de cohortes echantillons predefinies
  * Graphiques interactifs et table de details triable

---

## Démarrage Rapide

### Option A: Avec Docker (Recommandé)

1. **Construire et lancer le conteneur :**

   ```bash
   docker compose up -d --build
   ```

2. **Accéder à l'application :**
   Rendez-vous sur [http://localhost:80](http://localhost:80)

### Option B: Sans Docker (Développement local)

**1. Installation**

```bash
# Créer un venv
python -m venv .venv
# Activer le venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

**2. Configuration**

Renommez `.env.example` en `.env` (si disponible) et configurez vos variables :
```
SLACK_TOKEN=xoxb-...
SLACK_CHANNEL=...
```

**3. Lancement**

```bash
python run.py
```
L'application sera accessible sur http://127.0.0.1:5000

---

## Déploiement sur EC2

Documentation complète disponible dans [DEPLOYMENT.md](DEPLOYMENT.md).

En résumé :
1. Clonez le repo sur l'instance.
2. Créez votre fichier `.env`.
3. Lancez avec `docker compose up -d --build`.

---

## Structure du projet

```
slack_bot_flask/
├─ app/
│  ├─ __init__.py
│  ├─ routes.py                     # endpoints dont dashboard, leaderboard, etc.
│  ├─ slack_handler.py              # fonctions post_message et post_thread_message
│  ├─ static/
│  └─ templates/
├─ backend/
│  ├─ kpi_animators.py              # fonctions de traitement en logique animateurs
│  ├─ kpi_comments.py               # logique commentaires
│  ├─ kpi_masterclass.py            # logique masterclass
│  ├─ kpi_techaway.py               # logique techaway
│  ├─ preprocess.py                 # preprocess et light_preprocess
│  ├─ reporting.py                  # formattage des messages pour Slack
│  ├─ scheduler.py                  # WIP - reporting récurrent
│  ├─ utils.py                      # fonctions utilitaires
│  └─ mapping/
├─ data/
│  ├─ processed/
│  └─ uploads/
├─ reevaluation_time_exercise/      # module de reevaluation du temps des exercices
│  ├─ app/
│  │  ├─ static/
│  │  ├─ templates/
│  │  ├─ data_processor.py          # logique de traitement des modules et cohortes
│  │  ├─ nexus_client.py            # client API Nexus
│  │  └─ routes.py                  # endpoints reeval (login, dashboard, APIs)
├─ config.py                        # variables d'env (bot slack et app)
├─ Dockerfile
├─ docker-compose.yml
├─ DEPLOYMENT.md
└─ run.py
```

---

## Données

L'application attend un fichier `post_meeting_masterclass.csv` dans `data/uploads/` pour générer les statistiques. Le fichier `merged_processed.csv` est généré automatiquement dans `data/processed/`.

