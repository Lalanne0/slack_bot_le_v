# Send monthly KPIs for animators and weekly negative feedback on masterclasses

import os
import pandas as pd
from backend.utils import *
from backend.preprocess import preprocess_data, light_preprocess
from backend.nexus_client import refresh_data_from_nexus
from backend.reporting import send_bad_sessions
from datetime import datetime

def job_generate_weekly_report():
    print("Starting weekly background job: downloading new datasets...")
    # 1. Fetch the new datasets using saved credentials
    try:
        success = refresh_data_from_nexus()
        if not success:
            print("Failed to fetch new data from Nexus.")
            return
    except Exception as e:
        print(f"Error during scheduled Nexus fetch: {e}")
        return

    # 2. Process data
    try:
        df_fr_raw = pd.read_csv("data/uploads/post_meeting_masterclass.csv")
    except Exception:
        df_fr_raw = None
    
    try:
        df_en_raw = pd.read_csv("data/uploads/post_meeting_masterclass_en.csv")
    except Exception:
        df_en_raw = None

    if df_fr_raw is None and df_en_raw is None:
        print("No CSVs found to process.")
        return

    print("Preprocessing downloaded data...")
    df = preprocess_data(df_fr_raw, df_en_raw)
    
    if df is not None and not df.empty:
        os.makedirs("data/processed", exist_ok=True)
        # We overwrite to have latest history
        df.to_csv("data/processed/merged_processed.csv", index=False)
        with open("data/last_upload.txt", "w") as f:
            f.write(datetime.now().strftime("%d/%m/%Y à %H:%M"))
        
        # 3. Light preprocess and send Slack reporting for bad sessions
        print("Sending weekly bad sessions recap...")
        df_light = light_preprocess(df)
        send_bad_sessions(df_light)
        print("Weekly job completed successfully.")
    else:
        print("Processed dataframe is empty. Cannot send report.")

def main():
    job_generate_weekly_report()

if __name__ == "__main__":
    main()
