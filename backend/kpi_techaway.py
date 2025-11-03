# Masterclass related functions for the backend


from backend.utils import *
# from backend.kpi_animators import *
# from backend.kpi_comments import *



# Calcule la satisfation moyenne par verticale
def get_satisfaction_moyenne_verticale(df, verticale=None):
    if verticale is not None and verticale != "Not TechAway":
        df = df[df['Verticale'] == verticale]
    else:
        return -1
    result = df.groupby('Verticale')['Content Grade'].mean().round(2).reset_index()
    return result['Content Grade'].values[0] if not result.empty else None


# Détermine le niveau à partir du nom de la Masterclass
def get_niveau(masterclass):
    if "N0" in masterclass:
        return "0"
    elif "N1" in masterclass:
        return "1"
    elif "N2" in masterclass:
        return "2"
    elif "N3" in masterclass:
        return "3"
    else:
        return "-1"


# Calcule la satisfation moyenne par niveau
def get_satisfaction_moyenne_niveau(df, verticale, niveau):
    df = df.copy()
    df = df[df['Verticale'] == verticale]
    df['Niveau'] = df['Masterclass'].apply(get_niveau)
    if niveau is not None:
        df = df[df['Niveau'] == niveau]
    result = df.groupby('Niveau')['Content Grade'].mean().round(2).reset_index()
    return result['Content Grade'].values[0] if not result.empty else None
