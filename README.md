# 🎛️ Dashboard MC & Animateurs — Flask App

Application Flask pour suivre la qualité des **masterclasses** et des **animateurs** : tableaux de bord, leaderboards (tout temps & 30 jours), recherche par rôle, récap Slack, et affichage stylisé des avis négatifs.

---

## ✨ Fonctionnalités

* **Authentification simple** (session Flask) : `kpi:kpi`
* **Navbar Bootstrap** avec Login/Logout à droite
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

---

## 🏗️ Structure du projet

```
slack_bot_flask/
├─ app/
│  ├─ __init__.py
│  ├─ routes.py                     # endpoints dont dashboard, leaderboard, etc.
│  ├─ slack_handler.py              # fonctions post_message et post_thread_message
│  ├─ static/
│  │  ├─ styles.css
│  │  └─ images/
│  │     └─ slack-logo.png
│  └─ templates/
│     ├─ base.html
│     ├─ dashboard.html
│     ├─ leaderboard.html
│     ├─ commentaires.html
│     ├─ animateurs.html
│     ├─ animateur.html
│     ├─ masterclasses.html
│     ├─ masterclass.html
│     ├─ login.html
│     ├─ upload.html
│     └─ slack_bot.html
├─ backend/
│  ├─ kpi_animators.py              # fonctions de traitement en logique animateurs
│  ├─ kpi_comments.py               # logique commentaires
│  ├─ kpi_masterclass.py            # logique masterclass
│  ├─ kpi_techaway.py               # logique techaway
│  ├─ preprocess.py                 # preprocess et light_preprocess
│  ├─ reporting.py                  # formattage des messages pour Slack
│  ├─ scheduler.py                  # WIP - reporting récurrent
│  ├─ utils.py                      # fonctions utilitaires (filter_by_date_range, etc.)
│  └─ mapping/
│     ├─ meeting_mapping.json       # pour extraire la MC depuis le nom du meeting
│     └─ role_mapping.json          # pour extraire le rôle d'un animateur depuis son mail
├─ data/
│  ├─ processed/
│  │  └─ merged_processed.csv       # généré automatiquement
│  └─ uploads/                      # dossier de destination de post_meeting_masterclass.csv
├─ config.py                        # variables d'env (bot slack et app)
└─ run.py
```

---

## 🧩 Dépendances principales

* Python 3.9.7
* Flask, Jinja2
* pandas, numpy
* Bootstrap 5 (CDN déjà intégré dans `base.html`)

---

## ⚙️ Installation

```bash
# 1) Créer un venv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) Installer les dépendances
pip install -r requirements.txt

# 3) Lancer l'app
python run.py

# 3) Visiter http://127.0.0.1:5000
```

---

## 🔐 Authentification

* URL : `/login`
* Identifiants : **kpi / kpi**
* Toutes les routes du blueprint `main` sont protégées via `before_request`.
* Bouton **Login/Logout** dans la navbar (à droite).

---

## 🗃️ Données attendues

Fichier : `post_meeting_masterclass.csv` (français et/ou anglais)

## 🧹 Prétraitement des données (preprocess)

### 📥 Entrée (schéma d’origine)

```text
Language, Survey Answer Time, Survey Answer Date, Cohort ID, Cohort Program,
Cohort Subpartner Name, User ID, User Fullname, User Email, Question ID, Question,
Answer, Meeting Animator, Meeting Name, Meeting ID, Meeting Start Date, Project ID
```

### 🔁 Transformations (vue d’ensemble)

* Sélection / renommage des colonnes utiles.
* Normalisation des champs de notes et commentaires issus des réponses d’enquête.
* Harmonisation des libellés de masterclass et des rôles (si applicable via mapping).
* Nettoyage basique (espaces, valeurs manquantes).
* Préparation des champs pour l’analyse (types simples, colonnes standardisées).

> ⚠️ Le fichier exporté **ne peut pas** être utilisé tel quel : il faut ré-appliquer le typage (ex. `datetime`) et quelques corrections via `light_preprocess`.

### 📤 Sortie

```text
Cohort ID, User ID, User Fullname, Animator Grade, Content Grade, Comment,
Meeting Animator, Meeting Name, Meeting ID, Meeting Start Date, Masterclass,
Verticale, Animator Role
```

* **Animator Grade** : note liée à l’animateur (numérique).
* **Content Grade** : note liée au contenu (numérique).
* **Comment** : verbatim de l’apprenant.
* **Masterclass** : intitulé standardisé de la séance.
* **Verticale** : indique la verticale techaway (TechForAll, Data Analysis, etc.).
* **Animator Role** : rôle normalisé de l’animateur.

### 🗂️ Emplacement de l’export

* Le résultat du preprocess est écrit dans :
  `data/processed/merged_processed.csv`

---

Les colonnes **Masterclass** et **Animator Role** sont générées via mapping manuel dans les fichiers JSON. Il sont à mettre à jour si de nouvelles masterclasses / de nouveaux animateurs apparaissent.

---

## 🧭 Routes principales

* `/dashboard`
  Wall of Fame / Not Fame, commentaires négatifs (HTML préformaté).
* `/animateurs?q=...`
  Liste groupée par **Rôle** (fallback "Autres" si colonne manquante), recherche par nom, sections pliables (via `<details>`).
* `/animateur/<animateur>`
  Détail d’un animateur (stats & tables).
* `/masterclasses`
  Liste de masterclasses cliquables.
* `/masterclass/<masterclass>`
  Détail d’une MC (stats & tables).
* `/leaderboard?left=&right=&min_sessions=`
  Page **2 colonnes** configurables :

  * `left`/`right` ∈ `{anim, anim30, mc, mc30}`
  * `min_sessions` (par défaut 20) — appliqué aux leaderboards **animateurs**
    Une session = **Meeting ID unique** (filtrage via `get_animateurs_plus_de_20_dessions(df, min_sessions)`).
* `/slack_bot`
  3 boutons : Top animateurs, Not Top, Commentaires négatifs.

---

## 🧱 UI / Templates

* **Bootstrap 5** via CDN (déjà dans `base.html`)
* `styles.css` (chargé via `url_for('static', filename='styles.css')`)