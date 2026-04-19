import streamlit as st
import pandas as pd
import urllib.parse

st.set_page_config(page_title="Pool Hockey 2026", layout="wide")
st.title("🏆 Pool de Hockey - Vito, Joy & Mister B")

SHEET_ID = "1j4g-7V5cLo9WcHNj_T063-rD1rvUKrn11VoRi3TdXww"

def load_data(sheet_name):
    sheet_name_encoded = urllib.parse.quote(sheet_name)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name_encoded}"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    return df

try:
    df_part = load_data("Participants")
    df_pred = load_data("Prédictions")
    df_res = load_data("Résultats")
except Exception as e:
    st.error(f"Erreur de lecture : {e}")
    st.stop()

# --- LOGIQUE DE CALCUL AVEC LOGS ---
def calculer_score_details(nom):
    points = 0
    details = []
    p_preds = df_pred[df_pred['Nom'].astype(str).str.strip() == str(nom).strip()]
    
    pts_ronde = {"1/8": 1, "1/4": 2, "1/2": 3, "Finale": 4}
    
    for _, pred in p_preds.iterrows():
        serie = str(pred['Série/Équipes']).strip()
        choix = str(pred['Team Win']).strip()
        
        # On cherche le match
        match_res = df_res[df_res['Série/Équipes'].astype(str).str.strip() == serie]
        
        if not match_res.empty:
            res = match_res.iloc[0]
            eqA = str(res['Équipe A']).strip()
            eqB = str(res['Équipe B']).strip()
            
            # Calcul des points de victoires
            vics = 0
            if choix == eqA:
                vics = res['Victoires A']
            elif choix == eqB:
                vics = res['Victoires B']
            
            pts_match = vics * pts_ronde.get(str(pred['Ronde']).strip(), 1)
            points += pts_match
            details.append(f"✅ {serie} : {choix} a {vics} victoires ({pts_match} pts)")
        else:
            details.append(f"❌ {serie} : Non trouvé dans l'onglet Résultats")
            
    return int(points), details

# --- AFFICHAGE ---
st.subheader("Classement en direct")
scores = []
tous_les_details = {}

for nom in df_part['Nom'].dropna().unique():
    pts, info = calculer_score_details(nom)
    scores.append({"Participant": nom, "Points": pts})
    tous_les_details[nom] = info

if scores:
    df_final = pd.DataFrame(scores).sort_values("Points", ascending=False)
    df_final.insert(0, "Rang", range(1, len(df_final) + 1))
    st.table(df_final)
    
    # Section Diagnostic
    with st.expander("🔍 Pourquoi ce score ? (Diagnostic technique)"):
        for nom, logs in tous_les_details.items():
            st.write(f"**{nom} :**")
            for l in logs:
                st.write(l)
