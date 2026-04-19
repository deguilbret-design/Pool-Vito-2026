import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="Pool Hockey 2026", layout="wide")
st.title("🏆 Pool de Hockey - Vito, Joy & Mister B")

# --- CONNEXION AU GOOGLE SHEET ---
# Note: On configurera le lien secret à l'étape suivante.
URL_SHEET = "https://docs.google.com/spreadsheets/d/1j4g-7V5cLo9WcHNj_T063-rD1rvUKrn11VoRi3TdXww/export?format=csv"
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_part = conn.read(spreadsheet=URL_SHEET, worksheet="Participants")
    df_pred = conn.read(spreadsheet=URL_SHEET, worksheet="Prédictions")
    df_res = conn.read(spreadsheet=URL_SHEET, worksheet="Résultats")
except:
    st.info("🔄 En attente de la configuration finale du lien Google Sheet...")
    st.stop()

# --- LOGIQUE DE CALCUL ---
def calculer_score(nom):
    points = 0
    p_info = df_part[df_part['Nom'] == nom].iloc[0]
    p_preds = df_pred[df_pred['Nom'] == nom]
    
    pts_ronde = {"1/8": 1, "1/4": 2, "1/2": 3, "Finale": 4}
    bonus_matchs_dict = {4: 4, 5: 3, 6: 2, 7: 1}

    for _, pred in p_preds.iterrows():
        ronde = pred['Ronde']
        match_res = df_res[df_res['Série/Équipes'] == pred['Série/Équipes']]
        
        if not match_res.empty:
            res = match_res.iloc[0]
            # Victoires de l'équipe choisie
            vics = res['Victoires A'] if pred['Team Win'] == res['Équipe A'] else res['Victoires B']
            points += (vics * pts_ronde.get(ronde, 1))

            if str(res['Fini']).upper() == "OUI":
                v_reel = res['Équipe A'] if res['Victoires A'] > res['Victoires B'] else res['Équipe B']
                m_reel = int(res['Victoires A'] + res['Victoires B'])
                
                if pred['Team Win'] == v_reel:
                    points += 2 # Bonus série gagnée
                    if int(pred['#Match']) == m_reel:
                        points += bonus_matchs_dict.get(m_reel, 0)
                elif int(pred['#Match']) == 7 and m_reel == 7:
                    points += 1 # Exception Match 7
    return points

# --- AFFICHAGE DU CLASSEMENT ---
scores = []
for nom in df_part['Nom']:
    pts = calculer_score(nom)
    scores.append({"Participant": nom, "Points": pts})

df_final = pd.DataFrame(scores).sort_values("Points", ascending=False)
st.table(df_final)
