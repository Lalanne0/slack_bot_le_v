# Send monthly KPIs for animators and weekly negative feedback on masterclasses

from backend.utils import *
from backend.preprocess import preprocess_data



def job_generate_weekly_report():
    df_fr_raw = pd.read_csv("data/uploads/post_meeting_masterclass.csv")
    df_en_raw = pd.read_csv("data/uploads/post_meeting_masterclass_en.csv")
    df = preprocess_data(df_fr_raw, df_en_raw)
    
    
    # suite : kpi_masterclass(df), reporting, envoi Slack
    return