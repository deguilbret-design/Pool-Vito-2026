import streamlit as st
import pandas as pd
import urllib.parse
import requests

# 1. CONFIGURATION
st.set_page_config(page_title="Pool de Hockey 2026", layout="wide")

# 2. DESIGN PRO & VITESSE TURBO (15s)
st.markdown("""
    <style>
    .nhl-ticker-wrap {
        width: 100%; overflow: hidden; background: #0b0f19;
        border-bottom: 2px solid #1f77b4; margin: -50px -50px 30px -50px;
        padding: 10px 0; box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    .ticker { display: flex; white-space: nowrap; padding-left: 100%; animation: ticker 15s linear infinite; }
    @keyframes ticker { 0% { transform: translate3d(0, 0, 0); } 100% { transform: translate3d(-100%, 0, 0); } }
    .game-card {
        flex-shrink: 0; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 6px; margin-right: 20px; padding: 5px 15px; display: flex; align-items: center; gap: 10px; min-width: 230px;
    }
    .game-card.live { border-color: #ff4b4b; background: rgba(255, 75, 75, 0.1); }
    .game-card.final { border-color: #28a745; }
    .team { font-weight: 700; font-size: 0.9rem; color: #fff; width: 40px; text-align: center; }
    .score { background: #1e293b; color: #fbbf24; font-weight: 900; padding: 2px 8px; border-radius: 4px; min-width: 25px; text-align: center; }
    .status-badge { font-size: 0.6rem; font-weight: bold; padding: 2px 5px; border-radius: 3px; background: rgba(255,255,255,0.1); color: #94a3b8; }
    .live-dot { height: 6px; width: 6px; background: #ff4b4b; border-radius: 50%; display: inline-block; animation: blink 1s infinite; }
    @keyframes blink { 0% {opacity: 1;} 50% {opacity: 0.2;} 100% {opacity: 1;} }
    .main-title { text-align: center; color: #1f77b4; font-size: 2.2rem; font-weight: 800; margin-bottom: 5px; }
    .sub-title { text-align: center; color: #333; margin-top: 15px; font-weight: 700; font-size: 1.4rem; }
    table { width: 100%; border-radius: 10px; overflow: hidden; border-collapse: collapse; }
    th { background: #1f77b4; color: white; padding: 12px; font-size: 0.9rem; text-transform: uppercase; }
    td { padding: 12px; border-bottom: 1px solid #eee; text-align: center !important; }
    .bonus-card { background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; display: flex; align-items: center; gap: 15px; margin-bottom: 15px; }
    .bonus-label { color: #64748b; font-size: 0.7rem; font-weight: bold; text-transform: uppercase; }
    .bonus-value { color: #0f172a; font-size: 1.1rem; font-weight: 700; }
    .rules-section { background: #f8fafc; padding: 15px; border-left: 4px solid #1f77b4; margin-bottom: 10px; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

# 3. SCORES NHL
def get_nhl_ticker():
    try:
        url = "https://api-web.nhle.com/v1/score/now"
        data = requests.get(url, timeout=5).json()
        games = data.get('games', [])
        if not games: return '<div class="game-card">📅 Aucun match aujourd\'hui</div>'
        cards = ""
        for g in games:
            away, home = g['awayTeam']['abbrev'], g['homeTeam']['abbrev']
            ascor, hscor = g['awayTeam'].get('score', 0), g['homeTeam'].get('score', 0)
            status, css, badge = g['gameState'], "game-card", '<span class="status-badge">À VENIR</span>'
            if status in ["OFF", "FINAL"]:
                css += " final"; badge = '<span class="status-badge" style="color:#4ade80;">FINAL</span>'
            elif status in ["LIVE", "CRIT"]:
                css += " live"; p = g.get('periodDescriptor', {}).get('number', 1)
                badge = f'<span class="status-badge" style="color:#f87171;"><span class="live-dot"></span> P{p}</span>'
            cards += f'<div class="{css}"><span class="team">{away}</span><span class="score">{ascor}</span><span style="color:#475569;font-size:0.7rem;">VS</span><span class="score">{hscor}</span><span class="team">{home}</span>{badge}</div>'
        return cards
    except: return '<div class="game-card">⚠️ Données NHL indisponibles</div>'

st.markdown(f'<div class="nhl-ticker-wrap"><div class="ticker">{get_nhl_ticker()}</div></div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">🏆 Pool de Hockey 2026</div>', unsafe_allow_html=True)

# 4. DATA LOADING
SHEET_ID = "1j4g-7V5cLo9WcHNj_T063-rD1rvUKrn11VoRi3TdXww"
def load_data(sn):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sn)}"
    df = pd.read_csv(url); df.columns = df.columns.str.strip()
    return df

try:
    df_part, df_pred, df_res = load_data("Participants"), load_data("Prédictions"), load_data("Résultats")
    df_res['Victoires A'] = pd.to_numeric(df_res['Victoires A'], errors='coerce').fillna(0)
    df_res['Victoires B'] = pd.to_numeric(df_res['Victoires B'], errors='coerce').fillna(0)
except Exception as e:
    st.error(f"Erreur : {e}"); st.stop()

# 5. CALCULS
def calculer_tout(nom):
    total, details = 0, []
    p_preds = df_pred[df_pred['Nom'].astype(str).str.strip() == str(nom).strip()]
    pts_r = {"1/8": 1, "1/4": 2, "1/2": 3, "Finale": 4}
    bon_m = {4: 4, 5: 3, 6: 2, 7: 1}
    for _, pred in p_preds.iterrows():
        s, c, r = str(pred['Série/Équipes']).strip(), str(pred['Team Win']).strip(), str(pred['Ronde']).strip()
        m_res = df_res[df_res['Série/Équipes'].astype(str).str.strip() == s]
        pts_s, stt = 0, "❌"
        if not m_res.empty:
            res = m_res.iloc[0]
            v = res['Victoires A'] if c == str(res['Équipe A']).strip() else (res['Victoires B'] if c == str(res['Équipe B']).strip() else 0)
            pts_s += (v * pts_r.get(r, 1))
            if str(res['Fini']).upper() == "OUI":
                vr = res['Équipe A'] if res['Victoires A'] > res['Victoires B'] else res['Équipe B']
                mr = int(res['Victoires A'] + res['Victoires B
