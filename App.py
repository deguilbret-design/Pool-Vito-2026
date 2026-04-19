import streamlit as st
import pandas as pd
import urllib.parse

# 1. CONFIGURATION ET STYLE
st.set_page_config(page_title="Pool Hockey 2026", layout="wide")

st.markdown("""
    <style>
    .main-title { text-align: center; color: #1f77b4; font-size: 2.2rem; font-weight: bold; margin-bottom: 20px; }
    .sub-title { text-align: center; color: #333; margin-top: 20px; font-weight: bold; }
    
    /* Style pour les tableaux */
    .classement-container { display: flex; justify-content: center; margin-bottom: 30px; }
    table { width: 100%; border-collapse: collapse; border-radius: 8px; overflow: hidden; font-family: sans-serif; }
    th { background-color: #1f77b4; color: white; padding: 12px; text-align: center !important; }
    td { padding: 10px; text-align: center !important; border-bottom: 1px solid #eee; }
    tr:hover { background-color: #f9f9f9; }
    
    /* Style spécifique pour le règlement */
    .rules-table th { background-color: #444; }
    .rules-section { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 5px solid #1f77b4; margin-bottom: 15px; }
    
    .stExpander { border: 1px solid #ddd !important; border-radius: 8px !important; margin-bottom: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title">🏆 Pool de Hockey - Vito, Joy & Mister B</div>', unsafe_allow_html=True)

# --- CONNEXION DONNÉES ---
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
    df_res['Victoires A'] = pd.to_numeric(df_res['Victoires A'], errors='coerce').fillna(0)
    df_res['Victoires B'] = pd.to_numeric(df_res['Victoires B'], errors='coerce').fillna(0)
except Exception as e:
    st.error(f"Erreur de lecture des données : {e}")
    st.stop()

# --- LOGIQUE DE CALCUL ---
def calculer_tout(nom):
    total_points = 0
    liste_details = []
    p_preds = df_pred[df_pred['Nom'].astype(str).str.strip() == str(nom).strip()]
    pts_ronde = {"1/8": 1, "1/4": 2, "1/2": 3, "Finale": 4}
    bonus_matchs_dict = {4: 4, 5: 3, 6: 2, 7: 1}

    for _, pred in p_preds.iterrows():
        serie = str(pred['Série/Équipes']).strip()
        choix = str(pred['Team Win']).strip()
        ronde = str(pred['Ronde']).strip()
        match_res = df_res[df_res['Série/Équipes'].astype(str).str.strip() == serie]
        pts_serie, statut = 0, "❌"
        
        if not match_res.empty:
            res = match_res.iloc[0]
            eqA, eqB = str(res['Équipe A']).strip(), str(res['Équipe B']).strip()
            vics = res['Victoires A'] if choix == eqA else (res['Victoires B'] if choix == eqB else 0)
            pts_serie += (vics * pts_ronde.get(ronde, 1))
            
            if str(res['Fini']).upper() == "OUI":
                v_reel = res['Équipe A'] if res['Victoires A'] > res['Victoires B'] else res['Équipe B']
                m_reel = int(res['Victoires A'] + res['Victoires B'])
                if choix == str(v_reel).strip():
                    pts_serie += 2
                    if int(pred['#Match']) == m_reel:
                        pts_serie += bonus_matchs_dict.get(m_reel, 0)
                elif str(pred['#Match']) == "7" and m_reel == 7:
                    pts_serie += 1
            if pts_serie > 0: statut = "✅"
            total_points += pts_serie

        liste_details.append({"Statut": statut, "Série": serie, "Choix": choix, "Points": int(pts_serie)})
    return int(total_points), liste_details

# --- AFFICHAGE ---
if 'Nom' in df_part.columns:
    participants = df_part['Nom'].dropna().unique()
    scores_finaux = []
    tous_details = {}

    for nom in participants:
        pts, details = calculer_tout(nom)
        scores_finaux.append({"Participant": nom, "Points": pts})
        tous_details[nom] = details

    # 1. CLASSEMENT
    df_rank = pd.DataFrame(scores_finaux).sort_values("Points", ascending=False)
    df_rank.insert(0, "Rang", range(1, len(df_rank) + 1))
    st.markdown('<div class="sub-title">📊 Classement Général</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown(f'<div class="classement-container">{df_rank.to_html(index=False)}</div>', unsafe_allow_html=True)

    st.write("---")

    # 2. ANALYSE DES POINTS
    with st.expander("🔍 Pourquoi ce score ? (Détails par série)"):
        for nom in participants:
            st.subheader(f"Joueur : {nom}")
            st.write(pd.DataFrame(tous_details[nom]).to_html(index=False, escape=False), unsafe_allow_html=True)
            st.write("<br>", unsafe_allow_html=True)

    # 3. PRÉDICTIONS INITIALES
    with st.expander("📋 Voir les sélections de chaque participant"):
        for nom in participants:
            st.subheader(f"Prédictions de {nom}")
            preds_nom = df_pred[df_pred['Nom'].astype(str).str.strip() == str(nom).strip()]
            cols_show = ['Ronde', 'Série/Équipes', 'Team Win', '#Match']
            st.write(preds_nom[cols_show].to_html(index=False), unsafe_allow_html=True)
            st.write("<br>", unsafe_allow_html=True)

    # 4. RÈGLEMENT OFFICIEL
    with st.expander("📜 Règlement officiel - Vito's Super Hockey Pool 2026"):
        st.markdown("""
        <div class="rules-section">
            <h4>1. Structure du Pool</h4>
            <ul>
                <li><b>Format :</b> Éliminatoire (1/8, 1/4, 1/2 et Finale).</li>
                <li><b>Choix Initiaux :</b> Gagnant Coupe Stanley et MVP (Conn Smythe).</li>
                <li><b>Choix par Ronde :</b> Avant chaque ronde, prédiction du vainqueur et du nombre de matchs.</li>
            </ul>
        </div>
        
        <div class="rules-section">
            <h4>2. Système de Pointage Évolutif</h4>
            <table>
                <tr><th>Ronde</th><th>Points / Victoire</th><th>Bonus Vainqueur</th></tr>
                <tr><td>1/8 de finale</td><td>1 pt</td><td>+2 pts</td></tr>
                <tr><td>1/4 de finale</td><td>2 pts</td><td>+2 pts</td></tr>
                <tr><td>1/2 finale</td><td>3 pts</td><td>+2 pts</td></tr>
                <tr><td>Finale</td><td>4 pts</td><td>+2 pts</td></tr>
            </table>
        </div>

        <div class="rules-section">
            <h4>3. Bonus de Précision (# Matchs)</h4>
            <p>Si ton équipe gagne ET que le nombre de matchs est exact :</p>
            <ul>
                <li><b>4 matchs :</b> +4 pts | <b>5 matchs :</b> +3 pts</li>
                <li><b>6 matchs :</b> +2 pts | <b>7 matchs :</b> +1 pt</li>
            </ul>
            <p><i><b>Exception Match 7 :</b> Le +1 pt est accordé si la série se rend en 7, même si ton équipe perd.</i></p>
        </div>

        <div class="rules-section">
            <h4>4. Bonus Long Terme</h4>
            <ul>
                <li><b>Parcours Champion :</b> Ronde 1 (+2), Ronde 2 (+2), Ronde 3 (+2), Finale (+4).</li>
                <li><b>Trophée MVP :</b> +10 pts si ton choix initial gagne le Conn Smythe.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
