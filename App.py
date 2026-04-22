import streamlit as st
import pandas as pd
import urllib.parse
import requests
from datetime import datetime
import pytz

# 1. CONFIGURATION
st.set_page_config(page_title="Pool de Hockey 2026", layout="wide")

# 2. STYLE CSS (LIGNES COURTES POUR ÉVITER LES COUPURES)
css = """
<style>
.nhl-ticker-wrap {
    width: 100%; overflow: hidden; background: #0b0f19;
    border-bottom: 2px solid #1f77b4; margin: -50px -50px 30px -50px;
    padding: 10px 0; box-shadow: 0 4px 10px rgba(0,0,0,0.5);
}
.ticker { display: inline-flex; width: max-content; animation: ticker 15s linear infinite; }
@keyframes ticker { 
    0% { transform: translate3d(0, 0, 0); } 
    100% { transform: translate3d(-50%, 0, 0); } 
}
.game-card {
    flex-shrink: 0; background: rgba(255, 255, 255, 0.05); 
    border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 6px; 
    margin-right: 20px; padding: 5px 15px; display: flex; 
    align-items: center; gap: 10px; min-width: 230px;
}
.game-card.live { border-color: #ff4b4b; background: rgba(255, 75, 75, 0.1); }
.game-card.final { border-color: #28a745; }
.team { font-weight: 700; font-size: 0.9rem; color: #fff; width: 40px; text-align: center; }
.score { 
    background: #1e293b; color: #fbbf24; font-weight: 900; 
    padding: 2px 8px; border-radius: 4px; min-width: 25px; text-align: center; 
}
.status-badge { font-size: 0.6rem; font-weight: bold; padding: 2px 5px; color: #94a3b8; }
.live-dot { 
    height: 6px; width: 6px; background: #ff4b4b; border-radius: 50%; 
    display: inline-block; margin-right: 5px; animation: blink 1s infinite; 
}
@keyframes blink { 0% {opacity: 1;} 50% {opacity: 0.2;} 100% {opacity: 1;} }
.main-title { text-align: center; color: #1f77b4; font-size: 2.2rem; font-weight: 800; }
.sync-time { text-align: center; color: #64748b; font-size: 0.85rem; font-style: italic; margin-bottom: 25px; }
.table-container { display: flex; justify-content: center; width: 100%; }
table { width: auto !important; margin: auto; border-radius: 10px; overflow: hidden; border-collapse: collapse; }
th { background: #1f77b4; color: white; padding: 12px 25px; text-align: center !important; }
td { padding: 12px 25px; border-bottom: 1px solid #eee; text-align: center !important; font-weight: 600; }
.bonus-card { 
    background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; 
    padding: 12px; display: flex; align-items: center; gap: 15px; margin-bottom: 15px; 
}
.bonus-label { color: #64748b; font-size: 0.7rem; font-weight: bold; text-transform: uppercase; }
.bonus-value { color: #0f172a; font-size: 1.1rem; font-weight: 700; }
.rules-section { background: #f8fafc; padding: 15px; border-left: 4px solid #1f77b4; margin-bottom: 10px; }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# 3. SCORES NHL
def get_nhl_ticker():
    try:
        url = "https://api-web.nhle.com/v1/score/now"
        data = requests.get(url, timeout=5).json()
        games = data.get('games', [])
        if not games: return '<div class="game-card">📅 Aucun match aujourd\'hui</div>'
        html = ""
        for g in games:
            away, home = g['awayTeam']['abbrev'], g['homeTeam']['abbrev']
            ascor, hscor = g['awayTeam'].get('score', 0), g['homeTeam'].get('score', 0)
            status, css_c, badge = g['gameState'], "game-card", "À VENIR"
            if status in ["OFF", "FINAL"]:
                css_c += " final"; badge = "FINAL"
            elif status in ["LIVE", "CRIT"]:
                css_c += " live"; p = g.get('periodDescriptor', {}).get('number', 1)
                badge = f'<span class="live-dot"></span> P{p}'
            html += f'<div class="{css_c}"><span class="team">{away}</span>'
            html += f'<span class="score">{ascor}</span><span style="color:#475569;">VS</span>'
            html += f'<span class="score">{hscor}</span><span class="team">{home}</span>'
            html += f'<span class="status-badge">{badge}</span></div>'
        return html + html
    except: return '<div class="game-card">⚠️ NHL indisponible</div>'

st.markdown(f'<div class="nhl-ticker-wrap"><div class="ticker">{get_nhl_ticker()}</div></div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">🏆 Pool de Hockey 2026</div>', unsafe_allow_html=True)

# 4. DATA
SID = "1j4g-7V5cLo9WcHNj_T063-rD1rvUKrn11VoRi3TdXww"
def load_data(sn):
    u = f"https://docs.google.com/spreadsheets/d/{SID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sn)}"
    df = pd.read_csv(u); df.columns = df.columns.str.strip(); return df

try:
    df_part, df_pred, df_res = load_data("Participants"), load_data("Prédictions"), load_data("Résultats")
    try:
        df_sys = load_data("System")
        raw_d = df_sys.columns[0]
        tz = pytz.timezone('America/Montreal')
        dt = pd.to_datetime(raw_d).tz_localize('UTC').tz_convert(tz)
        sync_txt = dt.strftime("%d/%m/%Y à %H:%M:%S")
    except: sync_txt = "En attente de modification..."
    st.markdown(f'<div class="sync-time">Dernière modif. fichier : {sync_txt}</div>', unsafe_allow_html=True)
    df_res['Victoires A'] = pd.to_numeric(df_res['Victoires A'], errors='coerce').fillna(0)
    df_
