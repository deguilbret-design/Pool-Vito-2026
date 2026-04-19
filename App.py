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
    
    # SÉCURITÉ : On transforme les cases vides en 0 pour les colonnes de points
    df_res['Victoires A'] = pd.to_numeric(df_res['Victoires A'], errors='coerce').fillna(0)
    df_res['Victoires B'] = pd.to_numeric(df_res['Victoires B'], errors='coerce').fillna(0)
except Exception as e:
    st.error(f"Erreur de lecture : {e}")
    st.stop()

def calculer_score_details(nom):
    points = 0
    details = []
    p_preds = df_pred[df_pred['Nom'].astype(str).str.strip() == str(nom).strip()]
    pts_ronde = {"1/8": 1, "1/4": 2, "1/2": 3, "Finale": 4}
    bonus_matchs_dict = {4: 4, 5: 3, 6: 2, 7: 1}

    for _, pred in p_preds.iterrows():
        serie = str(pred['Série/Équipes']).strip()
        choix = str(pred['Team Win']).strip()
        match_res = df_res[df_res['Série/Équipes'].astype(str).str.strip() == serie]
        
        if not match_res.empty:
            res = match_res.iloc[0]
            eqA = str(res['Équipe A']).strip()
            eqB = str(res['Équipe B']).strip()
            
            vics = res['Victoires A'] if choix == eqA else (res['Victoires B'] if choix == eqB else 0)
            pts_match = vics * pts_ronde.get(str(pred['Ronde']).strip(), 1)
            points += pts_match
            
            # Bonus de fin de série
            if str(res['Fini']).upper() == "OUI":
                v_reel = res['Équipe A'] if res['Victoires A'] > res['Victoires B'] else res['Équipe B']
                m_reel = int(res['Victoires A'] + res['Victoires B'])
                if choix == str(v_reel).strip():
                    points += 2
                    try:
                        if int(pred['#Match']) == m_reel:
                            points += bonus_matchs_dict.get(m_reel, 0)
                    except: pass
                elif str(pred['#Match']) == "7" and m_reel == 7:
                    points += 1
            
            details.append(f"✅ {serie} : {choix} ({int(vics)} vics) -> {int(pts_match)} pts")
        else:
            details.append(f"❌ {serie} : Match non trouvé")
            
    return int(points), details

# --- AFFICHAGE ---
st.subheader("Classement en direct")
scores = []
tous_les_details = {}

if 'Nom' in df_part.columns:
    for nom in df_part['Nom'].dropna().unique():
        pts, info = calculer_score_details(nom)
        scores.append({"Participant": nom, "Points": pts})
        tous_les_details[nom] = info

    if scores:
        df_final = pd.DataFrame(scores).sort_values("Points", ascending=False)
        df_final.insert(0, "Rang", range(1, len(df_final) + 1))
        st.table(df_final)
        
        with st.expander("🔍 Voir le détail des points"):
            for nom, logs in tous_les_details.items():
                st.write(f"**{nom} :** {', '.join(logs)}")
