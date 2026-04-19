import streamlit as st
import pandas as pd
import urllib.parse

# Configuration de la page
st.set_page_config(page_title="Pool Hockey 2026", layout="wide")
st.title("🏆 Pool de Hockey - Vito, Joy & Mister B")

# --- CONNEXION AU GOOGLE SHEET ---
SHEET_ID = "1j4g-7V5cLo9WcHNj_T063-rD1rvUKrn11VoRi3TdXww"

def load_data(sheet_name):
    # On encode le nom de l'onglet pour gérer les accents (é, à, etc.)
    sheet_name_encoded = urllib.parse.quote(sheet_name)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name_encoded}"
    return pd.read_csv(url)

try:
    # Lecture des trois onglets
    df_part = load_data("Participants")
    df_pred = load_data("Prédictions")
    df_res = load_data("Résultats")
except Exception as e:
    st.error(f"Oups ! Erreur de lecture. Vérifie le partage du Google Sheet. Détails : {e}")
    st.stop()

# --- LOGIQUE DE CALCUL ---
def calculer_score(nom):
    points = 0
    p_preds = df_pred[df_pred['Nom'] == nom]
    
    pts_ronde = {"1/8": 1, "1/4": 2, "1/2": 3, "Finale": 4}
    bonus_matchs_dict = {4: 4, 5: 3, 6: 2, 7: 1}

    for _, pred in p_preds.iterrows():
        match_res = df_res[df_res['Série/Équipes'] == pred['Série/Équipes']]
        if not match_res.empty:
            res = match_res.iloc[0]
            vics = res['Victoires A'] if pred['Team Win'] == res['Équipe A'] else res['Victoires B']
            points += (vics * pts_ronde.get(pred['Ronde'], 1))

            if str(res['Fini']).upper() == "OUI":
                v_reel = res['Équipe A'] if res['Victoires A'] > res['Victoires B'] else res['Équipe B']
                m_reel = int(res['Victoires A'] + res['Victoires B'])
                if pred['Team Win'] == v_reel:
                    points += 2
                    if int(pred['#Match']) == m_reel:
                        points += bonus_matchs_dict.get(m_reel, 0)
                elif int(pred['#Match']) == 7 and m_reel == 7:
                    points += 1
    return points

# --- AFFICHAGE ---
st.subheader("Classement en direct")
scores = []
for nom in df_part['Nom']:
    pts = calculer_score(nom)
    scores.append({"Participant": nom, "Points": pts})

if scores:
    df_final = pd.DataFrame(scores).sort_values("Points", ascending=False)
    st.table(df_final)
