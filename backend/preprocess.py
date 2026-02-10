# Preprocess the raw csv file(s) into a cleaned csv file.


from backend.utils import *


# Prétraitement des données brutes
def preprocess_data(df_fr, df_en=None):
    """
    In: 
    Language,Survey Answer Time,Survey Answer Date,Cohort ID,Cohort Program,
    Cohort Subpartner Name,User ID,User Fullname,User Email,Question ID,Question,
    Answer,Meeting Animator,Meeting Name,Meeting ID,Meeting Start Date,Project ID

    Out:
    Cohort ID, User ID, User Fullname, Animator Grade, Content Grade, Comment,
    Meeting Animator, Meeting Name, Meeting ID, Meeting Start Date, Masterclass, 
    Animator Role
    """
    
    if df_en is not None:
        df = pd.concat([df_fr, df_en])
    else:
        df = df_fr
    
    df = df[['Survey Answer Date', 'Cohort ID', 'User ID', 'User Fullname', 'Meeting Animator',
            'Meeting Name', 'Meeting ID', 'Meeting Start Date', 'Question ID', 'Answer']]
    
    df = df.copy()
    
    # if Meeting Start Date has more than 90% NaNs, consider Survey Answer Time instead
    if df["Meeting Start Date"].isna().mean() > 0.9:
        df = df.drop(columns=["Meeting Start Date"])
        df = df.rename(columns={"Survey Answer Date": "Meeting Start Date"})
    else:
        df = df.drop(columns=["Survey Answer Date"])
    
    
    df["Meeting Animator"] = df["Meeting Animator"].fillna("Missing")
    # --- Modif: Normalisation datascientest.com -> liora.io ---
    df["Meeting Animator"] = df["Meeting Animator"].str.replace("@datascientest.com", "@liora.io", regex=False)
    
    df["Meeting Name"] = df["Meeting Name"].fillna("Missing")
    df["Meeting Start Date"] = df["Meeting Start Date"].fillna("01/01/1970 00:00")
        
    qid_map = {
        # Question 1 : Animator Grade
        '4d3a0ab6-2a9f-4dba-bc74-2b2aa48151a7': "Animator Grade",  # FR
        '94047627-ccd9-4a69-adfb-70f74ea00041': "Animator Grade",  # EN
        'ce772ac8-2fb5-48eb-87f0-ce4b84b6c307': "Animator Grade",  # FR TechAway post MC
        '43d41b33-2706-4161-aa1e-494e5f9efb6a': "Animator Grade",  # EN TechAway post MC
        '67a35ae4-390f-4ae4-8c0c-6c2dad0e60ce': "Animator Grade",  # FR TechAway post TP
        'ca5a0662-2f7f-46fe-8374-3391dff9b75c': "Animator Grade",  # EN TechAway post TP
        # Question 2 : Content Grade
        '998f7f91-a0f8-4ba8-9601-70071bb6957b': "Content Grade",  # FR
        'c50bf25c-8119-43f0-9c86-cc21d2f003bb': "Content Grade",  # EN
        'c4caac68-55a5-439f-8c1a-bcd002a41f59': "Content Grade",  # FR TechAway post MC
        '48de2d9e-2001-4978-9ae9-4a544725c42a': "Content Grade",  # EN TechAway post MC
        '4bc3ee94-453d-48c4-80b6-1bc08cec8fd5': "Content Grade",  # FR TechAway post TP
        '2416f1b2-39e3-4656-aced-4cb38f11bd80': "Content Grade",  # EN TechAway post TP
        # Question 3 : Comment
        '1c03a6e9-8479-462e-ab80-fc38a577f520': "Comment",  # FR
        '8a89e9cf-7935-414f-8c62-1e52f59882ff': "Comment",  # EN
        '5210391a-127a-4d9a-b6b9-6fe9a177b7a5': "Comment",  # FR TechAway post MC
        'd864fe39-11ed-47f9-a03d-5eaebbf70b02': "Comment",  # EN TechAway post MC
        '4fcb5e59-63d8-4dd7-b340-55d939b485e7': "Comment",  # FR TechAway post TP
        '2346e81c-4f44-409d-810c-56ca6c2891c6': "Comment",  # EN TechAway post TP
    }
    
    df["Answer_Type"] = df["Question ID"].map(qid_map)
    meta_cols = ["Cohort ID","User ID","User Fullname",
                 "Meeting Animator","Meeting Name","Meeting ID","Meeting Start Date"]
    pivoted = (
        df.pivot_table(
            index=["User ID","Meeting Name"],
            columns="Answer_Type",
            values="Answer",
            aggfunc=lambda x: next((v for v in x if pd.notna(v)), "")
        )
        .reset_index()
    )
        
    meta_unique = df.groupby(["User ID","Meeting Name"]).first().reset_index()[meta_cols]
    final = pd.merge(meta_unique, pivoted, on=["User ID","Meeting Name"], how="left")
    final_cols = meta_cols + ["Animator Grade","Content Grade","Comment"]
    final = final[final_cols]    
    final.dropna(subset=["Animator Grade"], inplace=True)    
    final["Content Grade"] = final["Content Grade"].fillna(final["Animator Grade"])
    final["Comment"] = final["Comment"].fillna("")
    
    # print(final.head())
    
    final["Meeting Start Date"] = pd.to_datetime(final["Meeting Start Date"], format="%d/%m/%Y %H:%M", errors='coerce')
    
    final.dropna(inplace=True)
    final["Animator Grade"] = pd.to_numeric(final["Animator Grade"], errors='coerce')
    final["Content Grade"] = pd.to_numeric(final["Content Grade"], errors='coerce')
    final["Masterclass"] = final["Meeting Name"].apply(get_mc_name)
    final["Verticale"] = final["Masterclass"].apply(get_verticale_techaway)
    final["Animator Role"] = final["Meeting Animator"].apply(get_role)
    
    final.drop_duplicates(subset=["User ID", "Meeting Name"], keep="first", inplace=True)

    return final


# Prétraitement léger pour importation
def light_preprocess(df):
    df = df.copy()
    df["Comment"] = df["Comment"].fillna("")
    df["Meeting Animator"] = df["Meeting Animator"].fillna("Unknown")
    # --- Modif: Normalisation datascientest.com -> liora.io ---
    df["Meeting Animator"] = df["Meeting Animator"].str.replace("@datascientest.com", "@liora.io", regex=False)

    df['Meeting Start Date'] = pd.to_datetime(df['Meeting Start Date'], errors='coerce')
    df.dropna(inplace=True)
    return df