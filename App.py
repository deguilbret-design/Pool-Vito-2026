import streamlit as st
import pandas as pd
import urllib.parse
import requests

# 1. CONFIGURATION
st.set_page_config(page_title="Pool Hockey 2026", layout="wide")

# 2. DESIGN PRO & FIXES (Ticker 15s, Tableau Compact, Centrage)
st.markdown("""<style>
.nhl-ticker-wrap { 
    width: 100%; overflow: hidden; background: #0b0f19; 
    border-bottom: 2px solid #1f77b4; margin: -50px -50px 30px -50px; padding: 10px 0; 
}
.ticker { display: inline-flex; width: max-content; animation: ticker 15s linear infinite; }
@keyframes ticker { 0% { transform: translate3d(0, 0, 0); } 100% { transform: translate3d(-50%, 0, 0); } }
.game-card { 
    flex-shrink: 0; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); 
    border-radius: 6px; margin-right: 20px; padding: 5px 15px; display: flex; align-items: center; gap: 10px; min-width: 230px; 
}
.game-card.live { border-color: #ff4b4b; background: rgba(255,75,75,0.1); }
.team { font-weight: 700; font-size: 0.9rem; color: #fff; width: 40px; text-align: center; }
.score { background: #1e293b; color: #fbbf24; font-weight: 900; padding: 2px 8px; border-radius: 4px; }
.live-dot { height: 6px; width: 6px; background: #ff4b4b; border-radius: 50%; display: inline-block; margin-right: 5px; animation: blink 1s infinite; }
@keyframes blink { 0% {opacity:1;} 50% {opacity:0.2;} 100% {opacity:1;} }
.table-container { display: flex; justify-content: center; width: 100%; margin-bottom: 20px; }
table { width: auto !important; margin: auto; border-radius: 10px; overflow: hidden; border-collapse: collapse; }
th { background: #1f77b4; color: white; padding: 10px 20px; text-align: center !important; }
td { padding: 10px 20px; border-bottom: 1px solid #eee; text-align: center !important; font-weight: 600; }
.bonus-card { background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px; display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.bonus-value { color: #0f172a; font-size: 1.1rem; font-weight: 700; }
</style>""", unsafe_allow_html=True)

# 3. SCORES NHL (Vitesse 15s et boucle infinie)
def get_scores():
    try:
        r = requests.get("https://api-web.nhle.com/v1/score/now", timeout=5).json()
        games = r.get('games', [])
        if not games: return '<div class="game-card">📅 Aucun match prévu</div>'
        h = ""
        for g in games:
            aw, hm = g['awayTeam']['abbrev'], g['homeTeam']['abbrev']
            ascor, hscor = g['awayTeam'].get('score', 0), g['homeTeam'].get('score', 0)
            stt, css, bdg = g['gameState'], "game-card", "À VENIR"
            if stt in ["OFF","FINAL"]: css += " final"; bdg = "FINAL"
            elif stt in ["LIVE","CRIT"]: 
                css += " live"; p = g.get('periodDescriptor',{}).get('number', 1)
                bdg = f'<span class="live-dot"></span> P{p}'
            h += f'<div class="{css}"><span class="team">{aw}</span><span class="score">{ascor}</span>VS'
            h += f'<span class="score">{hscor}</span><span class="team">{hm}</span>'
            h += f'<span style="font-size:0.6rem;margin-left:5px;">{bdg}</span></div>'
        return h + h
    except: return '<div class="game-card">⚠️ Scores NHL indisponibles</div>'

st.markdown(f'<div class="nhl-ticker-wrap"><div class="ticker">{get_scores()}</div></div>', unsafe_allow_html=True)
st.markdown('<h2 style="text-align:center;color:#1f77b4;margin-top:20px;">🏆 Pool Hockey 2026</h2>', unsafe_allow_html=True)

# 4. DONNÉES GOOGLE
SID = "1j4g-7V5cLo9WcHNj_T063-rD1rvUKrn11VoRi3TdXww"
def load(sn):
    u = f"https://docs.google.com/spreadsheets/d/{SID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sn)}"
    df = pd.read_csv(u); df.columns = df.columns.str.strip(); return df

try:
    df_p, df_pr, df_r = load("Participants"), load("Prédictions"), load("Résultats")
    df_r['Victoires A'] = pd.to_numeric(df_r['Victoires A'], errors='coerce').fillna(0)
    df_r['Victoires B'] = pd.to_numeric(df_r['Victoires B'], errors='coerce').fillna(0)
except Exception as e: 
    st.error(f"Erreur : {e}"); st.stop()

# 5. CALCULS
def calc(n):
    t, d = 0, []
    sub = df_pr[df_pr['Nom'].astype(str).str.strip() == str(n).strip()]
    r_pts, b_pts = {"1/8":1,"1/4":2,"1/2":3,"Finale":4}, {4:4,5:3,6:2,7:1}
    for _, p in sub.iterrows():
        se, ch, ro = str(p['Série/Équipes']).
