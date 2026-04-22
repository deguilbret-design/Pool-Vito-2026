import streamlit as st
import pandas as pd
import urllib.parse
import requests

# 1. CONFIGURATION DE BASE
st.set_page_config(page_title="Vito's Super Hockey Pool 2026", layout="wide")

# 2. STYLE CSS (DÉCOUPÉ POUR ÉVITER LES COUPURES DE CODE)
st.markdown("<style>", unsafe_allow_html=True)
st.markdown(".nhl-ticker-wrap { width: 100%; overflow: hidden; background: #0b0f19; border-bottom: 2px solid #1f77b4; margin: -50px -50px 30px -50px; padding: 10px 0; }", unsafe_allow_html=True)
st.markdown(".ticker { display: inline-flex; width: max-content; animation: tk 15s linear infinite; }", unsafe_allow_html=True)
st.markdown("@keyframes tk { 0% { transform: translate3d(0, 0, 0); } 100% { transform: translate3d(-50%, 0, 0); } }", unsafe_allow_html=True)
st.markdown(".game-card { flex-shrink: 0; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; margin-right: 20px; padding: 5px 15px; display: flex; align-items: center; gap: 10px; min-width: 230px; }", unsafe_allow_html=True)
st.markdown(".team { font-weight: 700; font-size: 0.9rem; color: #fff; width: 40px; text-align: center; }", unsafe_allow_html=True)
st.markdown(".score { background: #1e293b; color: #fbbf24; font-weight: 900; padding: 2px 8px; border-radius: 4px; }", unsafe_allow_html=True)
st.markdown(".table-container { display: flex; justify-content: center; width: 100%; margin-bottom: 20px; }", unsafe_allow_html=True)
st.markdown("table { width: auto !important; margin: auto; border-radius: 10px; overflow: hidden; border-collapse: collapse; }", unsafe_allow_html=True)
st.markdown("th { background: #1f77b4; color: white; padding: 10px 20px; text-align: center !important; }", unsafe_allow_html=True)
st.markdown("td { padding: 10px 20px; border-bottom: 1px solid #eee; text-align: center !important; font-weight: 600; }", unsafe_allow_html=True)
st.markdown(".bonus-card { background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px; display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }", unsafe_allow_html=True)
st.markdown(".rules-box { background: #f8fafc; padding: 15px; border-left: 4px solid #1f77b4; margin-bottom: 10px; border-radius: 4px; font-size: 0.9rem; }", unsafe_allow_html=True)
st.markdown("</style>", unsafe_allow_html=True)

# 3. SCORES NHL (TICKER)
def get_scores():
    try:
        r = requests.get("https://api-web.nhle.com/v1/score/now", timeout=5).json()
        games = r.get('games', [])
        if not games: return '<div class="game-card">📅 Aucun match prévu</div>'
        html = ""
        for g in games:
            aw, hm = g['awayTeam']['abbrev'], g['homeTeam']['abbrev']
            ascor, hscor = g['awayTeam'].get('score', 0), g['homeTeam'].get('score', 0)
            stt, css = g['gameState'], "game-card"
            bdg = "FINAL" if stt in ["OFF","FINAL"] else "À VENIR"
            if stt in ["LIVE","CRIT"]:
                css += " live"; bdg = "P" + str(g.get('periodDescriptor',{}).get('number', 1))
            html += f'<div class="{css}"><span class="team">{aw}</span><span class="score">{ascor}</span>VS'
            html += f'<span class="score">{hscor}</span><span class="team">{hm}</span>'
            html += f'<span style="font-size:0.6rem;margin-left:5px;">{bdg}</span></div>'
        return html + html
    except: return '<div class="game-card">⚠️ NHL Indisponible</div>'

st.markdown(f'<div class="nhl-ticker-wrap"><div class="ticker">{get_scores()}</div></div>', unsafe_allow_html=True)
st.markdown('<h2 style="text-align:center;color:#1f77b4;margin-top:20px;">🏆 Vito\'s Super Hockey Pool 2026</h2>', unsafe_allow_html=True)

# 4. CHARGEMENT DATA
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
    r_pts, b_pts = {"1/8":1,"1/4":2,"1/2":3,"Finale":4}, {4:4, 5:3, 6:2, 7:1}
    for _, p in sub.iterrows():
        se, ch, ro = str(p['Série/Équipes']).strip(), str(p['Team Win']).strip(), str(p['Ronde']).strip()
        m = df_r[df_r['Série/Équipes'].astype(str).str.strip() == se]
        ps, ok = 0, "❌"
        if not m.empty:
            res = m.iloc[0]; eA, eB = str(res['Équipe A']).strip(), str(res['Équipe B']).strip()
            v = res['Victoires A'] if ch == eA else (res['Victoires B'] if ch == eB else 0)
            ps += (v * r_pts.get(ro, 1))
            if str(res['Fini']).upper() == "OUI":
                vr = res['Équipe A'] if res['Victoires A'] > res['Victoires B'] else res['Équipe B']
                mr = int(res['Victoires A'] + res['Victoires B'])
                if ch == str(vr).strip():
                    ps += 2
                    try: 
                        if int(p['#Match']) == mr: ps += b_pts.get(mr, 0)
                    except: pass
                elif str(p['#Match']) == "7" and mr == 7: ps += 1
            if ps > 0: ok = "✅"
            t += ps
        d.append({"Statut": ok, "Série": se, "Choix": ch, "Points": int(ps)})
    return int(t), d

# 6. UI
if 'Nom' in df_p.columns:
    users = df_p['Nom'].dropna().unique()
    sc, det = [], {}
    for u in users:
        p, d = calc(u); sc.append({"Participant": u, "Points": p}); det[u] = d
    
    st.markdown('<h3 style="text-align:center;">📊 Classement</h3>', unsafe_allow_html=True)
    rk = pd.DataFrame(sc).sort_values("Points", ascending=False)
    rk.insert(0, "Rang", range(1, len(rk) + 1))
    st.markdown(f'<div class="table-container">{rk.to_html(index=False)}</div>', unsafe_allow_html=True)
    
    with st.expander("🔍 Analyse des points"):
        for u in users:
            st.subheader(u); st.write(pd.DataFrame(det[u]).to_html(index=False), unsafe_allow_html=True)

    with st.expander("📋 Sélections"):
        cols = df_p.columns.tolist()
        cn = next((c for c in cols if any(x in c.upper() for x in ["COUPE", "STANLEY"])), None)
        mn = next((c for c in cols if "MVP" in c.upper()), None)
        for u in users:
            st.markdown(f"#### **{u}**")
            p_s = df_pr[df_pr['Nom'].astype(str).str.strip() == str(u).strip()]
            if not p_s.empty: st.write(p_s[['Ronde','Série/Équipes','Team Win','#Match']].to_html(index=False), unsafe_allow_html=True)

    with st.expander("📜 Règlement Officiel"):
        st.markdown('<div class="rules-box"><b>1. Structure :</b> Éliminatoire (1/8, 1/4, 1/2 et Finale). Choix : Vainqueur de série et nombre de matchs (4 à 7).</div>', unsafe_allow_html=True)
        st.markdown('<div class="rules-box"><b>2. Points par Victoire :</b> 1/8(1pt), 1/4(2pts), 1/2(3pts), Finale(4pts). Bonus Vainqueur Série : +2 pts.</div>', unsafe_allow_html=True)
        st.markdown('<div class="rules-box"><b>3. Bonus Précision :</b> En 4 matchs(+4), 5(+3), 6(+2), 7(+1). Exception Match 7 : +1 pt accordé si la série se rend en 7, peu importe le vainqueur.</div>', unsafe_allow_html=True)
        st.markdown('<div class="rules-box"><b>4. Bonus Globaux :</b> Parcours Champion (R1+2, R2+2, R3+2, Finale+4). MVP : +10 pts si ton choix initial gagne le Conn Smythe.</div>', unsafe_allow_html=True)
