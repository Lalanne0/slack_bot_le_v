import os
import io
import base64
from pathlib import Path

import pandas as pd
from flask import current_app, render_template, request, redirect, url_for, flash, session, Blueprint
from werkzeug.utils import secure_filename
from functools import wraps
import math
from backend.preprocess import preprocess_data, light_preprocess
from backend.kpi_animators import *
from backend.kpi_masterclass import *
from backend.kpi_comments import *
from backend.kpi_techaway import *
from backend.reporting import *
from config import APP_USERNAME, APP_PASSWORD

ALLOWED_EXTENSIONS = {"csv"}
bp = Blueprint("main", __name__)

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def _upload_dir() -> Path:
    p = Path(current_app.config.get("UPLOAD_FOLDER", "data/uploads"))
    p.mkdir(parents=True, exist_ok=True)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    return p

def _processed_path() -> Path:
    return Path("data/processed/merged_processed.csv")

def _load_processed_df() -> pd.DataFrame:
    path = _processed_path()
    if not path.exists():
        raise FileNotFoundError(
            "Aucun fichier traité. Uploade un ou deux CSV puis traite-les depuis la page d’accueil."
        )
    return pd.read_csv(path)

def _animator_column(df: pd.DataFrame) -> str:
    candidates = [
        "meeting_animator",
        "Meeting Animator",
        "meeting_animator_email",
        "Meeting Animator Email"
    ]
    for c in candidates:
        if c in df.columns:
            return c
    raise KeyError(
        f"Colonne 'Meeting Animator' introuvable. Colonnes disponibles : {df.columns.tolist()}"
    )


def _masterclass_column(df: pd.DataFrame) -> str:
    candidates = [
        "Masterclass",
        "MC",
        "masterclass",
        "mc"
    ]
    for c in candidates:
        if c in df.columns:
            return c
    raise KeyError(
        f"Colonne 'Meeting Animator' introuvable. Colonnes disponibles : {df.columns.tolist()}"
    )
    

@bp.route("/", methods=["GET", "POST"])
def upload_files():
    if request.method == "POST":
        file_fr = request.files.get("file_fr")
        file_en = request.files.get("file_en")

        if not file_fr and not file_en:
            flash("Veuillez uploader au moins un fichier (FR ou EN).")
            return redirect(request.url)

        upload_dir = _upload_dir()
        df_fr = df_en = None

        if file_fr and allowed_file(file_fr.filename or ""):
            filename_fr = secure_filename(file_fr.filename or "")
            if filename_fr:
                save_path_fr = upload_dir / filename_fr
                file_fr.save(str(save_path_fr))
                df_fr = pd.read_csv(save_path_fr)

        if file_en and allowed_file(file_en.filename or ""):
            filename_en = secure_filename(file_en.filename or "")
            if filename_en:
                save_path_en = upload_dir / filename_en
                file_en.save(str(save_path_en))
                df_en = pd.read_csv(save_path_en)

        df_processed = preprocess_data(df_fr, df_en)
        df_processed.to_csv(_processed_path(), index=False)

        flash("Fichiers uploadés et traités avec succès.")
            
        return redirect(url_for("main.dashboard"))

    return render_template("upload.html")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("main.login", next=request.url))
        return view(*args, **kwargs)
    return wrapped


@bp.before_request
def _protect_routes():
    allowed = {"main.login", "main.logout", "static"}
    if request.endpoint in allowed or (request.endpoint or "").startswith("static"):
        return
    if not session.get("logged_in"):
        return redirect(url_for("main.login", next=request.url))


@bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()
        if username == APP_USERNAME and password == APP_PASSWORD:
            session["logged_in"] = True
            session["username"] = username
            return redirect(request.args.get("next") or url_for("main.dashboard"))
        error = "Identifiants invalides."
    return render_template("login.html", error=error)


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))


@bp.route("/dashboard")
def dashboard():
    try:
        processed_path = os.path.join("data/processed", "merged_processed.csv")
        if not os.path.exists(processed_path):
            return "Aucun fichier traité disponible."

        df = light_preprocess(pd.read_csv(processed_path))

        WoF = wall_of_fame(df)
        WoS = wall_of_not_fame(df)
        comments = get_masterclasses_with_negative_feedback(df)

        comments_html = ""
                
        if isinstance(comments, str):
            comments_html = f"<p>{comments}</p>"
        elif hasattr(comments, "empty") and comments.empty:
            comments_html = "<p>Aucun avis négatif à afficher.</p>"
        else:
            for _, row in comments.iterrows():
                mc = row.get("Masterclass")
                n_neg = row.get("Nombre Avis Négatifs", 0)
                n_sess = row.get("Nombre Sessions 30j", 0)

                comments_html += f"<div>📉 {mc} - {n_neg} avis négatifs sur {n_sess} sessions</div>"

                avis_list = row.get("Avis Négatifs", [])
                if isinstance(avis_list, pd.DataFrame):
                    avis_iter = avis_list.to_dict(orient="records")
                elif isinstance(avis_list, list):
                    avis_iter = avis_list
                else:
                    avis_iter = []

                for avis in avis_iter:
                    meeting_id = avis.get("Meeting ID")
                    mc_link = f"https://nexus.datascientest.com/meeting/{meeting_id}" if meeting_id else "#"

                    user_id = avis.get("User ID")
                    user_link = f"https://nexus.datascientest.com/user/{user_id}" if user_id else "#"

                    date_val = avis["Meeting Start Date"]
                    date_str = format_date(date_val)


                    animator = avis.get("Meeting Animator", "")
                    comment_text = (avis.get("Comment") or "").strip().replace("\n", " ")
                    author_name = avis.get("User Fullname", "")
                    rating = avis.get("Answer") or avis.get("Content Grade") or avis.get("Note")
                    rating_str = f"{rating}/5" if rating is not None else "—/5"
                    

                    comments_html += (
                        f"<div>🔸 <strong>Date</strong> : <a href=\"{mc_link}\" target=\"_blank\" rel=\"noopener\">{date_str}</a></div>"
                        f"<div>🧑 <strong>Animateur</strong> : {animator}</div>"
                        f"<div>📝 <strong>Commentaire</strong> : <em>{comment_text}</em></div>"
                        f"<div>✍ <strong>Auteur</strong> : "
                        f"<a href=\"{user_link}\" target=\"_blank\" rel=\"noopener\">{author_name}</a></div>"
                        f"<div>⭐ <strong>Note</strong> : {rating_str}</div>"
                        f"<br>"
                    )

                comments_html += "<hr>"

        return render_template("dashboard.html", wof=WoF, wos=WoS, comments=comments, comments_html=comments_html)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Erreur : {e}"


@bp.route("/animateurs")
def animateurs():
    """
    Liste de tous les animateurs, groupés par rôle, avec recherche par nom.
    """
    try:
        df = light_preprocess(_load_processed_df())

        q = (request.args.get("q") or "").strip().lower()

        col = _animator_column(df)  # colonne contenant le nom d'animateur
        role_col = "Animator Role" if "Animator Role" in df.columns else ("Role" if "Role" in df.columns else None)

        if role_col:
            sub = df[[col, role_col]].dropna().drop_duplicates()
            grouped = {}
            for _, r in sub.iterrows():
                name = str(r[col]).strip()
                role = str(r[role_col]).strip()
                if not name or not role:
                    continue
                if q and q not in name.lower():
                    continue
                grouped.setdefault(role, set()).add(name)

            # tri des rôles et des noms + supprime les rôles vides après filtre
            animateurs_by_role = {
                role: sorted(names, key=lambda x: x.lower())
                for role, names in sorted(grouped.items(), key=lambda x: x[0].lower())
                if names
            }
        else:
            # fallback si pas de colonne rôle
            names = [str(a).strip() for a in df[col].dropna().unique()]
            if q:
                names = [n for n in names if q in n.lower()]
            animateurs_by_role = {"Autres": sorted(names, key=lambda x: x.lower())}

        return render_template("animateurs.html", animateurs_by_role=animateurs_by_role, q=request.args.get("q", ""))
    except Exception as e:
        return f"Erreur : {e}"




@bp.route("/animateur/<path:animateur>")
def animateur_detail(animateur: str):
    """
    Page dédiée à un animateur (email unique).
    """
    try:
        df = light_preprocess(_load_processed_df())

        # Métriques générales
        sessions_total = get_nb_sessions_animateur(df, animateur)
        moyenne_generale = get_moyenne_animateur(df, animateur)
        classement = get_position_classement_animateur(df, animateur)

        best = get_best_mc_animateur(df, animateur)
        worst = get_worst_mc_animateur(df, animateur)

        # 30 derniers jours
        sessions_30j = get_nb_sessions_animateur_30j(df, animateur)
        moyenne_30j = get_moyenne_animateur_30j(df, animateur)
        classement_30j = get_position_classement_animateur_30j(df, animateur)

        df_sessions_30j = get_sessions_30j_animateur(df, animateur)
        df_mc = get_masterclasses_by_animateur(df, animateur)

        # Tables vers HTML
        def df_table_payload(d: pd.DataFrame):
            if d is None or d.empty:
                return {"columns": [], "rows": []}
            return {"columns": list(d.columns), "rows": d.to_dict(orient="records")}

        payload_sessions_30j = df_table_payload(df_sessions_30j)
        payload_mc = df_table_payload(df_mc)

        best_label = (
            f"{best['Masterclass']}" if best is not None else "Aucune masterclass trouvée")
        worst_label = (
            f"{worst['Masterclass']}" if worst is not None else "Aucune masterclass trouvée")
        
        feedback = get_last_feedback(df, animateur)    
        
        
        context = {
            "animateur": animateur,
            "sessions_total": sessions_total,
            "moyenne_generale": moyenne_generale,
            "classement": classement if classement else "Non classé",
            "best_label": best_label,
            "worst_label": worst_label,
            "sessions_30j": sessions_30j,
            "moyenne_30j": round(moyenne_30j, 2) if moyenne_30j else None,
            "classement_30j": classement_30j if classement_30j else "Non classé",
            "sessions_30j_table": payload_sessions_30j,
            "mc_table": payload_mc,
            "feedback": feedback,
        }
        return render_template("animateur.html", **context)

    except Exception as e:
        return f"Erreur : {e}"


@bp.route("/masterclasses")
def masterclasses():
    """
    Liste de toutes les masterclass.
    """
    try:
        df = light_preprocess(_load_processed_df())

        # Liste cliquable des masterclass
        col = _masterclass_column(df)
        masterclasses = sorted(m for m in df[col].dropna().unique())

        return render_template("masterclasses.html", masterclasses=masterclasses)
    except Exception as e:
        return f"Erreur : {e}"


@bp.route("/masterclass/<path:masterclass>")
def masterclass_detail(masterclass: str):
    """
    Page dédiée à une masterclass (nom unique).
    """
    try:
        df = light_preprocess(_load_processed_df())

        # Métriques générales
        sessions_total = get_nb_sessions_masterclass(df, masterclass)
        moyenne_generale = get_moyenne_masterclass(df, masterclass)
        classement = get_position_classement_masterclass(df, masterclass)

        best = get_mc_best_animateur(df, masterclass)
        worst = get_mc_worst_animateur(df, masterclass)

        # 30 derniers jours
        sessions_30j = get_nb_sessions_masterclass_30j(df, masterclass)
        moyenne_30j = get_moyenne_masterclass_30j(df, masterclass)

        df_mc_animateurs = get_mc_best_animateurs(df, masterclass)
        df_mc_animateurs_30j = get_mc_best_animateurs(filter_by_date_range(df, start_date=datetime.now() - timedelta(days=30)), masterclass)
        
        classement_30j = get_position_classement_masterclass_30j(df, masterclass)

        # Tables vers HTML
        def df_table_payload(d: pd.DataFrame):
            if d is None or d.empty:
                return {"columns": [], "rows": []}
            return {"columns": list(d.columns), "rows": d.to_dict(orient="records")}

        payload_sessions_30j = df_table_payload(df_mc_animateurs_30j)
        payload_mc = df_table_payload(df_mc_animateurs)

        best_label = (
            f"{best['Meeting Animator']}" if best is not None else "Aucun animateur trouvé")
        worst_label = (
            f"{worst['Meeting Animator']}" if worst is not None else "Aucun animateur trouvé")

        context = {
            "masterclass": masterclass,
            "sessions_total": sessions_total,
            "moyenne_generale": moyenne_generale,
            "classement": classement if classement else "Non classé",
            "best_label": best_label,
            "worst_label": worst_label,
            "sessions_30j": sessions_30j,
            "moyenne_30j": round(moyenne_30j, 2) if moyenne_30j else None,
            "classement_30j": classement_30j if classement_30j else "Non classé",
            "sessions_30j_table": payload_sessions_30j,
            "mc_table": payload_mc
        }
        return render_template("masterclass.html", **context)

    except Exception as e:
        return f"Erreur : {e}"
    
    
@bp.route("/leaderboard")
def leaderboard():
    try:
        processed_path = os.path.join("data/processed", "merged_processed.csv")
        if not os.path.exists(processed_path):
            return "Aucun fichier traité disponible."

        df = light_preprocess(pd.read_csv(processed_path))

        # Slider / query param: seuil minimum de sessions
        min_sessions = request.args.get("min_sessions", default=20, type=int)
        if not isinstance(min_sessions, int) or min_sessions < 1:
            min_sessions = 20

        df_anim = get_animateurs_plus_de_20_sessions(df, min_sessions)
        df_mc = get_masterclass_plus_de_10_sessions(df, min_sessions)

        lb_anim = get_leaderboard_animateurs(df_anim, min_sessions)
        lb_anim30 = get_leaderboard_animateurs_30j(df)
        lb_mc = get_leaderboard_masterclasses(df_mc, min_sessions)
        lb_mc30 = get_leaderboard_masterclasses_30j(df)

        # Selections (left/right), defaults: animateurs | animateurs 30j
        left_key = (request.args.get("left") or "anim").lower()
        right_key = (request.args.get("right") or "anim30").lower()

        options = {
            "anim": {"label": "Animateurs (tout)", "type": "animateur", "df": lb_anim},
            "anim30": {"label": "Animateurs (30 jours)", "type": "animateur", "df": lb_anim30},
            "mc": {"label": "Masterclasses (tout)", "type": "masterclass", "df": lb_mc},
            "mc30": {"label": "Masterclasses (30 jours)", "type": "masterclass", "df": lb_mc30},
        }
        if left_key not in options:
            left_key = "anim"
        if right_key not in options:
            right_key = "anim30"

        def prep(table, typ):
            if table is None or getattr(table, "empty", True):
                return {"columns": [], "rows": [], "label_col": None, "type": typ}
            cols = list(table.columns)  # rang | label | moyenne
            label_col = cols[1] if len(cols) >= 2 else None
            rows = table[cols].to_dict(orient="records")
            return {"columns": cols, "rows": rows, "label_col": label_col, "type": typ}

        left = prep(options[left_key]["df"], options[left_key]["type"])
        right = prep(options[right_key]["df"], options[right_key]["type"])

        return render_template(
            "leaderboard.html",
            left=left,
            right=right,
            left_label=options[left_key]["label"],
            right_label=options[right_key]["label"],
            left_key=left_key,
            right_key=right_key,
            all_options=options,
            min_sessions=min_sessions,
        )
    except Exception as e:
        return f"Erreur : {e}"



@bp.route("/slack_bot", methods=["GET", "POST"])
def slack_bot():
    """
    Page dédiée au Slack Bot.
    """
    try:
        message = None

        if request.method == "POST":
            df = light_preprocess(_load_processed_df())
            action = request.form.get("action")

            if action == "wof":
                send_top_animators_message(df)
                message = "Message Wall of Fame envoyé sur Slack."
            elif action == "wos":
                send_not_top_animators_message(df)
                message = "Message Wall of Not Fame envoyé sur Slack."
            elif action == "bad":
                send_bad_sessions(df)
                message = "Récap commentaires négatifs envoyé sur Slack."
            else:
                message = "Action inconnue."

        return render_template("slack_bot.html", message=message)
    except Exception as e:
        return f"Erreur : {e}"


@bp.route("/techaway")
def techaway():
    try:
        processed_path = os.path.join("data/processed", "merged_processed.csv")
        if not os.path.exists(processed_path):
            return "Aucun fichier traité disponible."

        df = light_preprocess(pd.read_csv(processed_path))
        
        T4A_satisf = get_satisfaction_moyenne_niveau(df, verticale="TECHFORALL", niveau="0")
        DA_N1_satisf = get_satisfaction_moyenne_niveau(df, verticale="DATAANALYSIS", niveau="1")
        DA_N2_satisf = get_satisfaction_moyenne_niveau(df, verticale="DATAANALYSIS", niveau="2")
        DA_N3_satisf = get_satisfaction_moyenne_niveau(df, verticale="DATAANALYSIS", niveau="3")
        PROG_N1_satisf = get_satisfaction_moyenne_niveau(df, verticale="PROGRAMING", niveau="1")
        PROG_N2_satisf = get_satisfaction_moyenne_niveau(df, verticale="PROGRAMING", niveau="2")
        PROG_N3_satisf = get_satisfaction_moyenne_niveau(df, verticale="PROGRAMING", niveau="3")
        NOCODE_N1_satisf = get_satisfaction_moyenne_niveau(df, verticale="NOCODE", niveau="1")
        NOCODE_N2_satisf = get_satisfaction_moyenne_niveau(df, verticale="NOCODE", niveau="2")
        NOCODE_N3_satisf = get_satisfaction_moyenne_niveau(df, verticale="NOCODE", niveau="3")
        CYBER_N1_satisf = get_satisfaction_moyenne_niveau(df, verticale="CYBERSECURITY", niveau="1")
        CYBER_N2_satisf = get_satisfaction_moyenne_niveau(df, verticale="CYBERSECURITY", niveau="2")
        CYBER_N3_satisf = get_satisfaction_moyenne_niveau(df, verticale="CYBERSECURITY", niveau="3")
        AI_N1_satisf = get_satisfaction_moyenne_niveau(df, verticale="AI", niveau="1")
        AI_N2_satisf = get_satisfaction_moyenne_niveau(df, verticale="AI", niveau="2")
        AI_N3_satisf = get_satisfaction_moyenne_niveau(df, verticale="AI", niveau="3")
        
        def style_and_label(val):
            # Convertit une note (1..5) en couleur HSL + libellé "x.xx/5"
            if val is None:
                return "background: #9ca3af;", "—"
            try:
                v = float(val)
            except Exception:
                return "background: #9ca3af;", "—"
            if math.isnan(v):
                return "background: #9ca3af;", "—"
            v = max(1.0, min(5.0, v))
            hue = int(round((v / 5.0) * 120))  # 1->rouge, 5->vert
            return f"background: hsl({hue}, 70%, 45%);", f"{v:.2f}/5"
        
        
        # ➜ Nouveau: style de remplissage pour les NIVEAUX (2.5 → 50%, 4.0 → 80%, etc.)
        def fill_style(val):
            try:
                v = float(val)
                if math.isnan(v):
                    raise ValueError
            except Exception:
                pct = 0.0
            else:
                v = max(0.0, min(5.0, v))
                pct = (v / 5.0) * 100.0
            # fond vert rempli jusqu’à pct%, puis gris au-dessus
            return (
                f"background: linear-gradient(to top, "
                f"#16a34a {pct:.0f}%, #f3f4f6 {pct:.0f}%); "
                f"border: 1px solid #e5e7eb;"
            )

        # ====== HERO : TECHFORALL ======
        hero_name = "TECHFORALL"
        hero_overall = get_satisfaction_moyenne_verticale(df, hero_name)
        hero_style, hero_score_label = style_and_label(hero_overall)

        # Un seul bloc "Niveau 0" cliquable (fusion des 3 niveaux précédents)
        hero_levels = [{
            "name": "Niveau 0",
            "code": "N0",
            "style": fill_style(T4A_satisf),
            "score_label": style_and_label(T4A_satisf)[1],
        }]

        # --- Autres verticales + leurs niveaux ---
        level_vars = {
            "DATAANALYSIS": {"N1": DA_N1_satisf, "N2": DA_N2_satisf, "N3": DA_N3_satisf},
            "PROGRAMING":   {"N1": PROG_N1_satisf, "N2": PROG_N2_satisf, "N3": PROG_N3_satisf},
            "NOCODE":       {"N1": NOCODE_N1_satisf, "N2": NOCODE_N2_satisf, "N3": NOCODE_N3_satisf},
            "CYBERSECURITY":{"N1": CYBER_N1_satisf, "N2": CYBER_N2_satisf, "N3": CYBER_N3_satisf},
            "AI":           {"N1": AI_N1_satisf, "N2": AI_N2_satisf, "N3": AI_N3_satisf},
        }

        verticals = ["DATAANALYSIS", "PROGRAMING", "NOCODE", "CYBERSECURITY", "AI"]
        tiles = []
        for v in verticals:
            overall = get_satisfaction_moyenne_verticale(df, v)
            tile_style, tile_label = style_and_label(overall)

            levels = []
            for code, label in [("N1", "Niveau 1"), ("N2", "Niveau 2"), ("N3", "Niveau 3")]:
                lvl_val = level_vars.get(v, {}).get(code)
                levels.append({
                    "name": label,
                    "code": code,
                    "style": fill_style(lvl_val),
                    "score_label": style_and_label(lvl_val)[1],
                })

            tiles.append({"name": v, "style": tile_style, "score_label": tile_label, "levels": levels})

        # ====== META par TP (pour Hero N0 + autres verticales N1..N3) ======
        tp_meta = {}
        
        T4A_TP1_satisf = get_moyenne_masterclass(df, "TECHFORALL-N0 - TP 1")
        T4A_TP2_satisf = get_moyenne_masterclass(df, "TECHFORALL-N0 - TP 2")
        T4A_TP3_satisf = get_moyenne_masterclass(df, "TECHFORALL-N0 - TP 3")
        T4A_TP4_satisf = get_moyenne_masterclass(df, "TECHFORALL-N0 - TP 4")


        # Hero N0
        for tp, val in [(1, T4A_TP1_satisf), (2, T4A_TP2_satisf), (3, T4A_TP3_satisf), (4, T4A_TP4_satisf)]:
            v = 0.0 if val is None or (isinstance(val, float) and math.isnan(val)) else float(val)
            pct = int(round(max(0.0, min(5.0, v)) / 5.0 * 100))
            tp_meta[f"{hero_name}_N0_TP{tp}"] = {"pct": pct, "label": f"{v:.2f}/5" if val is not None else "—"}

        # Autres verticales
        for v in verticals:
            for code in ["N1", "N2", "N3"]:
                for tp in [1, 2, 3, 4]:
                    val = get_moyenne_masterclass(df, f"{v}-{code} - TP {tp}")
                    vv = 0.0 if val is None or (isinstance(val, float) and math.isnan(val)) else float(val)
                    pct = int(round(max(0.0, min(5.0, vv)) / 5.0 * 100))
                    tp_meta[f"{v}_{code}_TP{tp}"] = {"pct": pct, "label": f"{vv:.2f}/5" if val is not None else "—"}

        return render_template(
            "techaway.html",
            hero_name=hero_name,
            hero_style=hero_style,
            hero_score_label=hero_score_label,
            hero_levels=hero_levels,   # contient un seul niveau N0
            tiles=tiles,
            tp_meta=tp_meta,
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Erreur : {e}"


@bp.route("/commentaires", methods=["GET"])
def commentaires():
    """
    Page listant les commentaires des masterclasses avec filtres :
    - étoiles (Content Grade) multi-choix
    - nombre minimum de mots
    - période en jours (par défaut 30)
    """
    try:
        processed_path = os.path.join("data/processed", "merged_processed.csv")
        if not os.path.exists(processed_path):
            return "Aucun fichier traité disponible."

        df = light_preprocess(pd.read_csv(processed_path))

        # Widgets (GET params)
        selected_grades = request.args.getlist("grades", type=int)  # ex: ?grades=1&grades=3
        min_words = request.args.get("min_words", default=3, type=int)
        days = request.args.get("days", default=30, type=int)

        # Période
        end_date = datetime.now()
        start_date = end_date - timedelta(days=max(1, days))

        # 'seuil' : si rien sélectionné -> Ellipsis (...) => par défaut {1,2,3}
        seuil = selected_grades if selected_grades else ...

        comments_df = get_comments(
            df,
            seuil=seuil,
            longueur_min_avis=min_words,
            start_date=start_date,
            end_date=end_date,
        )

        return render_template(
            "commentaires.html",
            comments_df=comments_df,
            selected_grades=set(selected_grades),
            min_words=min_words,
            days=days,
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Erreur : {e}"


def register_routes(app):
    app.register_blueprint(bp)
