import streamlit as st
import pandas as pd
import urllib.parse
import requests
from datetime import datetime

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="Pool de Hockey 2026", layout="wide")

# 2. DESIGN & STYLE CSS (Le "Look & Feel")
st.markdown("""
    <style>
    /* BANNIÈRE NHL TICKER */
    .nhl-ticker {
        background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
        color: white;
        padding: 15px 0;
        overflow: hidden;
        border-bottom: 3px solid #1f77b4;
        margin: -50px -50px 30px -50px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .ticker-content {
        display: inline-block;
        animation: marquee 45s linear infinite;
    }
    .game-card {
        display: inline-flex;
        align-items: center;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 8px 15px;
        margin: 0 15px;
        border-left: 4px solid #444;
        min-width: 220px;
    }
    .game-card.live { border-left-color: #ff4b4b; background: rgba(255, 75, 75, 0.1); }
    .game-card.final { border-left-color: #28a745; }
    .team-name { font-weight: 800; font-size: 0.95rem; color: #f8fafc; }
    .team-score { 
        font-family: 'Monaco', monospace; 
        font-size: 1.1rem; 
        font-weight: bold; 
        background: #000; 
        padding: 2px 8px; 
        border-radius: 4px;
        margin: 0 5px;
        color: #fbbf24;
    }
    .game-status { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1px; margin-left: 10px; padding: 2px 6px; border-radius: 4px; background: rgba(255,255,255,0.1); }
    .live-dot { height: 8px; width: 8px; background-color: #ff4b4b; border-radius: 50%; display: inline-block; margin-right: 5px; animation: blink 1s infinite; }

    @keyframes blink { 0% {opacity: 1;} 50% {opacity: 0.3;} 100% {opacity: 1;} }
    @keyframes marquee { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }

    /* TITRES & INTERFACE */
    .main-title { text-align: center; color: #1f77b4; font-size: 2.5rem; font-weight: bold; margin-bottom: 10px; }
    .sub-title { text-align: center; color: #333; margin-top: 20px; font-weight: bold; font-size: 1.5rem; }
    
    /* TABLEAUX */
    .classement-container { display: flex; justify-content: center; margin-bottom: 30px; }
    table { width: 100%; border-collapse: collapse; border-radius: 8px; overflow: hidden; }
    th { background-color: #1f77b4; color: white; padding: 12px; text-align: center !important; }
    td { padding: 10px; text-align: center !important; border-bottom: 1px solid #eee; font-size: 1rem; }
    
    /* CARTES BONUS (Champion/MVP) */
    .bonus-card { 
        background-color: #eef6fb; 
        border: 1px solid #b6d4fe; 
        border-radius: 10px; 
        padding: 15px; 
        margin-bottom: 20px; 
        display: flex; 
        align-items: center; 
        justify-content: flex-start;
        gap: 20px;
        min-height: 85px;
    }
    .bonus-label { color: #084298; font-weight: bold; font-size: 0.75rem; text-transform: uppercase; display: block; }
    .bonus-value { font-size: 1.2rem; font-weight: bold; color: #333; }
    .bonus-icon { font-size: 2.2rem; min-width: 40px; text-align: center; }

    /* RÈGLEMENT */
    .rules-section { background-color: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 5px solid #1f77b4; margin-bottom: 20px; }
    .rules-table { width: auto !important; margin: 10px 0; }
    .rules-table th { background-color: #444 !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. FONCTION SCORES NHL
def get_nhl_ticker():
    try:
        url = "https://api-web.nhle.com/v1/score/now"
        response = requests.get(url, timeout=5)
        data = response.json()
        games = data.get('games', [])
        if not games: return '<div class="game-card">🏒 Aucun match aujourd\'hui</div>'
        
        ticker_html = ""
        for game in games:
            away = game['awayTeam']['abbrev']
            home = game['homeTeam']['abbrev']
            away_score = game['awayTeam'].get('score', 0)
            home_score = game['homeTeam'].get('score', 0)
            status = game['gameState']
            
            card_class = "game-card"
            status_text = ""
            
            if status in ["OFF", "FINAL"]:
                card_class += " final"
                status_text = '<span class="game-status">FIN</span>'
            elif status in ["LIVE", "CRIT"]:
                card_class += " live"
                p = game.get('periodDescriptor', {}).get('number', 1)
                status_text = f'<span class="game-status"><span class="live-dot"></span>P{p}</span>'
            else:
                status_text = '<span class="game-status">À VENIR</span>'

            ticker_html += f'''
                <div class="{card_class}">
                    <span class="team-name">{away}</span><span class="team-score">{away_score}</span>
                    <span style="color: #64748b;">vs</span>
                    <span class="team-score">{home_score}</span><span class="team-name">{home}</span>
                    {status_text}
                </div>'''
        return ticker_html + ticker_html
    except:
        return '<div class="game-card">⚠️ Scores NHL indisponibles</div>'

# AFFICHAGE DU TICKER
st.markdown(f'<div class="nhl-ticker"><div class="ticker-content">{get_nhl_ticker()}</div></div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">🏆 Pool de Hockey 2026</div>', unsafe_allow_html=True)

# 4. CONNEXION AUX DONNÉES GOOGLE SHEETS
SHEET_ID = "1j4g-7V5cLo9WcHNj_T063-rD1rvUKrn11VoRi3TdXww"

def load_data(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
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
    st.error(f"Erreur de lecture : {e}")
    st.stop()

# 5. LOGIQUE DE CALCUL DES POINTS
def calculer_tout(nom):
    total_points = 0
    liste_details = []
    p_preds = df_pred[df_pred['Nom'].astype(str).str.strip() == str(nom).strip()]
    pts_ronde_dict = {"1/8": 1, "1/4": 2, "1/2": 3, "Finale": 4}
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
            pts_serie += (vics * pts_ronde_dict.get(ronde, 1))
            
            if str(res['Fini']).upper() == "OUI":
                v_reel = res['Équipe A'] if res['Victoires A'] > res['Victoires B'] else res['Équipe B']
                m_reel = int(res['Victoires A'] + res['Victoires B'])
                if choix == str(v_reel).strip():
                    pts_serie += 2
                    try:
                        if int(pred['#Match']) == m_reel: pts_serie += bonus_matchs_dict.get(m_reel, 0)
                    except: pass
                elif str(pred['#Match']) == "7" and m_reel == 7:
                    pts_serie += 1
            if pts_serie > 0: statut = "✅"
            total_points += pts_serie
        liste_details.append({"Statut": statut, "Série": serie, "Choix": choix, "Points": int(pts_serie)})
    return int(total_points), liste_details

# 6. INTERFACE UTILISATEUR
if 'Nom' in df_part.columns:
    participants = df_part['Nom'].dropna().unique()
    scores_finaux = []
    tous_details = {}

    for nom in participants:
        pts, details = calculer_tout(nom)
        scores_finaux.append({"Participant": nom, "Points": pts})
        tous_details[nom] = details

    # CLASSEMENT
    df_rank = pd.DataFrame(scores_finaux).sort_values("Points", ascending=False)
    df_rank.insert(0, "Rang", range(1, len(df_rank) + 1))
    st.markdown('<div class="sub-title">📊 Classement Général
