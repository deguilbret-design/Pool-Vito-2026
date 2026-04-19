import streamlit as st
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="Pool Hockey 2026", layout="wide")
st.title("🏆 Pool de Hockey - Vito, Joy & Mister B")

# --- CONNEXION AU GOOGLE SHEET ---
# On utilise l'ID unique de ton fichier pour un accès direct
SHEET_ID = "1j4g-7V5cLo9WcHNj_T063-rD1rvUKrn11VoRi3TdXww"

def load_data(sheet_name):
    # Ce format de lien (gviz/tq) est le plus stable pour lire les onglets Google Sheets
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    return pd.read_csv(url)

try:
    # Lecture des trois onglets
    df_part = load_data("Participants")
    df_pred = load_data("Prédictions")
    df_res = load_data("Résultats")
except Exception as e:
    st.error(f"Oups ! Impossible de lire le fichier Google Sheet. Vérifie que le partage est bien à 'Tous les utilisateurs disposant du lien'. Erreur : {e}")
    st.stop()

# --- LOGIQUE DE CALCUL ---
def calculer_score(nom):
    points = 0
    # On filtre les prédictions pour ce participant
    p_preds = df_pred[df_pred['Nom'] == nom]
    
    pts_ronde = {"1/8": 1, "1/4": 2, "1/2": 3, "Finale": 4}
    bonus_matchs_dict = {4: 4, 5: 3, 6: 2, 7: 1}

    for _, pred in p_preds.iterrows():
        ronde = pred['Ronde']
        match_res = df_res[df_res['Série/Équipes'] == pred['Série/Équipes']]
        
        if not match_res.empty:
            res = match_res.iloc[0]
            # Points pour les victoires de l'équipe choisie
            vics = res['Victoires A'] if pred['Team Win'] == res['Équipe A'] else res['Victoires B']
            points += (vics * pts_ronde.get(ronde, 1))

            # Bonus de fin de série
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
st.subheader("Classement en direct")
scores = []
for nom in df_part['Nom']:
    pts = calculer_score(nom)
    scores.append({"Participant": nom, "Points": pts})

if scores:
    df_final = pd.DataFrame(scores).sort_values("Points", ascending=False)
    # On affiche un beau tableau propre
    st.table(df_final)
else:
    st.warning("Aucun participant trouvé.")
