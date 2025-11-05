# Fonctions utilitaires pour le backend


import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta


MAPPING_DIR = Path(__file__).parent / "mapping"


with open(MAPPING_DIR / "meeting_mapping.json", "r", encoding="utf-8") as f:
    meeting_mapping = json.load(f)

with open(MAPPING_DIR / "role_mapping.json", "r", encoding="utf-8") as f:
    role_mapping = json.load(f)


# Fonction pour nettoyer les noms de masterclass avec dictionnaire JSON
def get_mc_name(meeting_name):
    # If "-OPT1" appears in the meeting name, remove it
    if "-OPT1" in meeting_name:
        meeting_name = meeting_name.replace("-OPT1", "")
    elif "-OPT2" in meeting_name:
        meeting_name = meeting_name.replace("-OPT2", "")
   
    options = ["AI", "CYBERSECURITY", "TECHFORALL", "DATAANALYSIS", "NOCODE", "PROGRAMING", "PROGRAMMING"]
    # Replace TECHAWAY-option-L by TECHAWAY-option-N
    for option in options:
        if f"TECHAWAY-{option}-L" in meeting_name:
            meeting_name = meeting_name.replace(f"TECHAWAY-{option}-L", f"TECHAWAY-{option}-N")

    for key, value in meeting_mapping.items():
        if key.lower() in meeting_name.lower():
            return value
    return meeting_name


# Ajouter la colonne Verticale pour les TechAway
def get_verticale_techaway(masterclass):
    options = ["AI", "CYBERSECURITY", "TECHFORALL", "DATAANALYSIS", "NOCODE", "PROGRAMING"]
    for option in options:
        if option in masterclass:
            return option
    
    if "PROGRAMMING" in masterclass:
        return "PROGRAMING"
    
    if "Examen blanc" in masterclass:
        return "Examen blanc"
    
    else:
        return "Not TechAway"


# Fonction pour définir le rôle d'un animateur avec dictionnaire JSON
def get_role(animateur_email):
    for key, value in role_mapping.items():
        if key.lower() in animateur_email.lower():
            return value
    return "Rôle inconnu"


# Formatte le mail de l'animateur
def format_animator_label(animator):
    if '@' in animator:
        parts = animator.split('@')[0].split('.')
        return ' '.join(part.capitalize() for part in parts)
    return animator.title()


# Formatte une date en string + lisible
def format_date(date_str: str) -> str:
    # In : TimeStamp '2023-10-05 14:30:00'
    # Out: '05/10/2023 14:30'
    try:
        dt = pd.to_datetime(date_str)
        return dt.strftime("%d/%m %H:%M")
    except Exception:
        return date_str


# Filtrer les données par plage de dates
def filter_by_date_range(df, start_date=None, end_date=None):
    df = df.copy()
    if start_date is not None:
        df = df[df['Meeting Start Date'] >= pd.to_datetime(start_date)]
    if end_date is not None:
        df = df[df['Meeting Start Date'] <= pd.to_datetime(end_date)]
    return df


# Retourne la date du meeting, la Masterclass, son animateur, les avis, la moyenne
def get_meeting_info(df, meeting_id):
    # Filtrer par date
    df = filter_by_date_range(df, start_date=datetime.now() - timedelta(days=30))
    # Filtrer le meeting
    meeting_df = df[df["Meeting ID"] == meeting_id].copy()
    if meeting_df.empty:
        return None
    
    # Informations générales
    meeting_date = meeting_df["Meeting Start Date"].iloc[0]
    masterclass = meeting_df["Masterclass"].iloc[0]
    animator = meeting_df["Meeting Animator"].iloc[0]
    animator_label = format_animator_label(animator)
    
    # Avis (commentaires > 3 mots)
    comments = [
        c for c in meeting_df["Comment"].dropna().tolist()
        if isinstance(c, str) and len(c.strip().split()) > 3
    ]
    
    # Notes
    avg_grade = meeting_df["Animator Grade"].mean().round(2)
    animator_grades = meeting_df["Animator Grade"].dropna().tolist()
    
    return {
        "Meeting ID": meeting_id,
        "Date": meeting_date,
        "Masterclass": masterclass,
        "Animateur": animator_label,
        "Avis": comments,
        "Moyenne": avg_grade,
        "Animator Grades": animator_grades,
        "Link": f"https://nexus.datascientest.com/meeting/{meeting_id}"
    }