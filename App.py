import streamlit as st
import pandas as pd
import urllib.parse
import requests
from datetime import datetime

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="Pool de Hockey 2026", layout="wide")

# 2. DESIGN & STYLE CSS
st.markdown("""
    <style>
    .nhl-ticker {
        background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
        color: white; padding: 15px 0; overflow: hidden;
        border-bottom: 3px solid #1f77b4; margin: -50px -50px 30px -50px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .ticker-content { display: inline-block; animation: marquee 45s linear infinite; }
    .game-card {
        display: inline-flex; align-items: center; background: rgba(255, 255, 255, 0.05);
        border-radius: 8px; padding: 8px 15px; margin: 0 15px; border-left: 4px solid #444; min-width: 220px;
    }
    .game-card.live { border-left-color: #ff4b4b; background: rgba(255, 75, 75, 0.1); }
    .game-card.final { border-left-color: #28a745; }
    .team-name { font-weight: 800; font-size: 0.95rem; color: #f8fafc; }
    .team-score { font-family: 'Monaco', monospace; font-size: 1.1rem; font-weight: bold; background: #000; padding: 2px 8px; border-radius: 4px; margin: 0 5px; color: #fbbf24; }
    .game-status { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1px; margin-left: 10px; padding: 2px 6px; border-radius: 4px; background: rgba(255,255,255,0.1); }
    .live-dot { height: 8px; width: 8px; background-color: #ff4b4b; border-radius: 50%; display: inline-block; margin-right: 5px; animation: blink 1s infinite; }
    @keyframes blink { 0% {opacity: 1;} 50% {opacity: 0.3;} 100% {opacity: 1;} }
    @keyframes marquee { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }
    .main-title { text-align: center; color: #1f77b4; font-size: 2.5rem; font-weight: bold; margin-bottom: 10px; }
    .sub-title { text-align: center; color: #333; margin-top: 20px; font-weight: bold; font-size: 1.5rem; }
    table { width: 100%; border-collapse: collapse; border-radius: 8px; overflow: hidden; }
    th { background-color: #1f77b4; color: white; padding: 12px; text-align: center !important; }
    td { padding: 10px; text-align: center !important; border-bottom: 1px solid #eee; font-size: 1rem; }
    .bonus-card { background-color: #eef6fb; border: 1px solid #b6d4fe; border-radius: 10px; padding: 15px; margin-bottom: 20px; display: flex; align-items: center; gap: 20px; min-height: 85px; }
    .bonus-label { color: #084298; font-weight: bold; font-size: 0.75rem; text-transform: uppercase; display: block; }
    .bonus-value { font-size: 1.2rem; font-weight: bold; color: #333; }
    .bonus-icon { font-size: 2.2rem; min-width: 40px; text-align: center; }
    .rules-section { background-color: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 5px solid #1f77b4; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 3. FONCTION SCORES NHL
def get_nhl_ticker():
    try:
        url = "https://api-web.nhle.com/v1/score/now"
        data = requests.get(url, timeout=5).json()
        games = data.get('games', [])
        if not games: return '<div class="game-card">🏒 Aucun match aujourd\'hui</div>'
        t_html = ""
        for g in games:
            away, home = g['awayTeam']['abbrev'], g['homeTeam']['abbrev']
            ascor, hscor = g['awayTeam'].get('score', 0), g['homeTeam'].get('score', 0)
            status, c_class, s_text = g['gameState'], "game-card", '<span class="game-status">À VENIR</span>'
            if status in ["OFF", "FINAL"]:
                c_class += " final"; s_text = '<span class="game-status">FIN</span>'
            elif status in ["LIVE", "CRIT"]:
                c_class += " live"; p = g.get('periodDescriptor', {}).get('number', 1)
                s_text = f'<span class="game-status"><span class="live-dot"></span>P{p}</span>'
            t_html += f'<div class="{c_class}"><span class="team-name">{away}</span><span class="team-score">{ascor}</span><span style="color:#64748b;">vs</span><span class="team-score">{hscor}</span><span class="team-name">{home}</span>{s_text}</div>'
        return t_html + t_html
    except: return '<div class="game-card">⚠️ Scores NHL indisponibles</div>'

st.markdown(f'<div class="nhl-ticker"><div class="ticker-content">{get_nhl_ticker()}</div></div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">🏆 Pool de Hockey 2026</div>', unsafe_allow_html=True)

# 4. DONNÉES
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
                mr = int(res['Victoires A'] + res['Victoires B'])
                if c == str(vr).strip():
                    pts_s += 2
                    try:
                        if int(pred['#Match']) == mr: pts_s += bon_m.get(mr, 0)
                    except: pass
                elif str(pred['#Match']) == "7" and mr == 7: pts_s += 1
            if pts_s > 0: stt = "✅"
            total += pts_s
        details.append({"Statut": stt, "Série": s, "Choix": c, "Points": int(pts_s)})
    return int(total), details

# 6. INTERFACE
if 'Nom' in df_part.columns:
    participants = df_part['Nom'].dropna().unique()
    scores_finaux = []
    tous_details = {}
    for n in participants:
        pts, det = calculer_tout(n)
        scores_finaux.append({"Participant": n, "Points": pts})
        tous_details[n] = det

    st.markdown('<div class="sub-title">📊 Classement Général</div>', unsafe_allow_html=True)
    df_rank = pd.DataFrame(scores_finaux).sort_values("Points", ascending=False)
    df_rank.insert(0, "Rang", range(1, len(df_rank) + 1))
    c1, c2, c3 = st.columns([1, 4, 1])
    with c2: st.markdown(f'<div style="display:flex;justify-content:center;">{df_rank.to_html(index=False)}</div>', unsafe_allow_html=True)

    st.write("---")
    with st.expander("🔍 Pourquoi ce score ? (Détails par série)"):
        for n in participants:
            st.subheader(f"Joueur : {n}")
            st.write(pd.DataFrame(tous_details[n]).to_html(index=False, escape=False), unsafe_allow_html=True)

    with st.expander("📋 Voir les sélections de chaque participant"):
        ac = df_part.columns.tolist()
        cc = next((c for c in ac if any(x in c.upper() for x in ["STANLEY", "CUP", "COUPE"])), None)
        cm = next((c for c in ac if "MVP" in c.upper()), None)
        for n in participants:
            st.markdown(f"### Prédictions de **{n}**")
            ur = df_part[df_part['Nom'].astype(str).str.strip() == str(n).strip()]
            if not ur.empty:
