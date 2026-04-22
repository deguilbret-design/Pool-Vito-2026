import streamlit as st
import pandas as pd
import urllib.parse
import requests
from datetime import datetime

# 1. CONFIGURATION ET STYLE
st.set_page_config(page_title="Pool de Hockey 2026", layout="wide")

st.markdown("""
    <style>
    /* Style du Ticker NHL (Bannière de scores) */
    .nhl-ticker {
        background-color: #111;
        color: white;
        padding: 10px 0;
        overflow: hidden;
        white-space: nowrap;
        border-bottom: 2px solid #1f77b4;
        margin: -50px -50px 20px -50px; /* Pour coller au haut de la page */
    }
    .ticker-content {
        display: inline-block;
        animation: marquee 30s linear infinite;
    }
    .game-box {
        display: inline-block;
        padding: 0 30px;
        border-right: 1px solid #444;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
    }
    @keyframes marquee {
        0% { transform: translateX(0); }
        100% { transform: translateX(-50%); }
    }
    
    .main-title { text-align: center; color: #1f77b4; font-size: 2.2rem; font-weight: bold; margin-bottom: 20px; }
    .sub-title { text-align: center; color: #333; margin-top: 20px; font-weight: bold; }
    .bonus-card { background-color: #eef6fb; border: 1px solid #b6d4fe; border-radius: 10px; padding: 15px; margin-bottom: 20px; display: flex; align-items: center; gap: 15px; }
    .bonus-label { color: #084298; font-weight: bold; font-size: 0.75rem; text-transform: uppercase; }
    .bonus-value { font-size: 1.25rem; font-weight: bold; color: #333; }
    .stExpander { border: 1px solid #ddd !important; border-radius: 8px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTION SCORES NHL LIVE ---
def get_nhl_ticker():
    try:
        # API officielle NHL pour les scores du jour
        url = "https://api-web.nhle.com/v1/score/now"
        response = requests.get(url, timeout=5)
        data = response.json()
        games = data.get('games', [])
        
        if not games:
            return "Aucun match prévu aujourd'hui"
        
        ticker_text = ""
        for game in games:
            away = game['awayTeam']['abbrev']
            home = game['homeTeam']['abbrev']
            away_score = game['awayTeam'].get('score', 0)
            home_score = game['homeTeam'].get('score', 0)
            status = game['gameState'] # FINAL, LIVE, PRE
            
            # Formatage selon le statut
            if status == "OFF" or status == "FINAL":
                ticker_text += f'<div class="game-box">🏁 {away} {away_score} - {home_score} {home} (Final)</div>'
            elif status == "LIVE" or status == "CRIT":
                period = game.get('periodDescriptor', {}).get('number', 1)
                ticker_text += f'<div class="game-box" style="color:#ff4b4b;">🔴 {away} {away_score} - {home_score} {home} ({period}e Per)</div>'
            else:
                start_time = game.get('startTimeUTC', '').split('T')[-1][:5]
                ticker_text += f'<div class="game-box">📅 {away} vs {home} ({start_time} UTC)</div>'
        
        # On double le texte pour un défilement infini fluide
        return ticker_text + ticker_text
    except:
        return "Service des scores NHL temporairement indisponible"

# --- AFFICHAGE DE LA BANNIÈRE NHL ---
ticker_html = get_nhl_ticker()
st.markdown(f'<div class="nhl-ticker"><div class="ticker-content">{ticker_html}</div></div>', unsafe_allow_html=True)

st.markdown('<div class="main-title">🏆 Pool de Hockey 2026</div>', unsafe_allow_html=True)

# --- (RESTE DU CODE DE CONNEXION ET CALCUL - INCHANGÉ) ---
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
    st.error(f"Erreur : {e}")
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
    with c2: st.markdown(f'<div class="classement-container">{df_rank.to_html(index=False)}</div>', unsafe_allow_html=True)

    st.write("---")

    # 2. ANALYSE DES POINTS
    with st.expander("🔍 Pourquoi ce score ? (Détails par série)"):
        for nom in participants:
            st.subheader(f"Joueur : {nom}")
            st.write(pd.DataFrame(tous_details[nom]).to_html(index=False, escape=False), unsafe_allow_html=True)
            st.write("<br>", unsafe_allow_html=True)

    # 3. SÉLECTIONS
    with st.expander("📋 Voir les sélections de chaque participant"):
        all_cols_part = df_part.columns.tolist()
        col_champ = next((c for c in all_cols_part if any(x in c.upper() for x in ["STANLEY", "CUP", "COUPE", "CHAMP"])), None)
        col_mvp = next((c for c in all_cols_part if "MVP" in c.upper()), None)

        for nom in participants:
            st.markdown(f"### Prédictions de **{nom}**")
            user_row = df_part[df_part['Nom'].astype(str).str.strip() == str(nom).strip()]
            if not user_row.empty:
                ca, cb = st.columns(2)
                if col_champ:
                    val = user_row[col_champ].iloc[0]
                    ca.markdown(f'<div class="bonus-card"><span class="bonus-icon">🏆</span><div><span class="bonus-label">Champion Choisi</span><span class="bonus-value">{val}</span></div></div>', unsafe_allow_html=True)
                if col_mvp:
                    val = user_row[col_mvp].iloc[0]
                    cb.markdown(f'<div class="bonus-card"><span class="bonus-icon">🎖️</span><div><span class="bonus-label">MVP Choisi</span><span class="bonus-value">{val}</span></div></div>', unsafe_allow_html=True)
            
            p_preds = df_pred[df_pred['Nom'].astype(str).str.strip() == str(nom).strip()]
            match_data = p_preds[p_preds['Série/Équipes'].notna()]
            if not match_data.empty:
                cols_to_show = [c for c in ['Ronde', 'Série/Équipes', 'Team Win', '#Match'] if c in match_data.columns]
                st.write(match_data[cols_to_show].to_html(index=False), unsafe_allow_html=True)
            st.write("<hr>", unsafe_allow_html=True)

    # 4. RÈGLEMENT
    with st.expander("📜 Règlement officiel"):
        st.markdown("""
        <div class="rules-section">
            <h4>1. Structure du Pool</h4>
            <p>Format éliminatoire. Choix Coupe Stanley et MVP fixés au départ.</p>
        </div>
        """, unsafe_allow_html=True)
