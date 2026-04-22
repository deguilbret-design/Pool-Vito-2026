import streamlit as st
import pandas as pd
import urllib.parse
import requests

# 1. CONFIGURATION
st.set_page_config(page_title="Pool de Hockey 2026", layout="wide")

# 2. DESIGN & STYLE CSS (Intégration du PDF et ergonomie)
st.markdown("""
    <style>
    .nhl-ticker-wrap {
        width: 100%; overflow: hidden; background: #0b0f19;
        border-bottom: 2px solid #1f77b4; margin: -50px -50px 30px -50px;
        padding: 10px 0; box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    .ticker { display: flex; width: max-content; animation: ticker 15s linear infinite; }
    @keyframes ticker { 
        0% { transform: translate3d(0, 0, 0); } 100% { transform: translate3d(-50%, 0, 0); } 
    }
    .game-card {
        flex-shrink: 0; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 6px; margin-right: 20px; padding: 5px 15px; display: flex; align-items: center; gap: 10px; min-width: 230px;
    }
    .game-card.live { border-color: #ff4b4b; background: rgba(255, 75, 75, 0.1); }
    .team { font-weight: 700; font-size: 0.9rem; color: #fff; width: 40px; text-align: center; }
    .score { background: #1e293b; color: #fbbf24; font-weight: 900; padding: 2px 8px; border-radius: 4px; min-width: 25px; text-align: center; }
    .status-badge { font-size: 0.6rem; font-weight: bold; padding: 2px 5px; border-radius: 3px; background: rgba(255,255,255,0.1); color: #94a3b8; }
    .live-dot { height: 6px; width: 6px; background: #ff4b4b; border-radius: 50%; display: inline-block; animation: blink 1s infinite; }
    @keyframes blink { 0% {opacity: 1;} 50% {opacity: 0.2;} 100% {opacity: 1;} }
    .main-title { text-align: center; color: #1f77b4; font-size: 2.2rem; font-weight: 800; margin-bottom: 5px; }
    .sub-title { text-align: center; color: #333; margin-top: 15px; font-weight: 700; font-size: 1.4rem; margin-bottom: 20px; }
    .table-container { display: flex; justify-content: center; width: 100%; }
    table { width: auto !important; margin: auto; border-radius: 10px; overflow: hidden; border-collapse: collapse; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    th { background: #1f77b4; color: white; padding: 12px 25px; text-align: center !important; text-transform: uppercase; font-size: 0.85rem; }
    td { padding: 12px 25px; border-bottom: 1px solid #eee; text-align: center !important; font-weight: 600; }
    .bonus-card { background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; display: flex; align-items: center; gap: 15px; margin-bottom: 15px; }
    .bonus-label { color: #64748b; font-size: 0.7rem; font-weight: bold; text-transform: uppercase; }
    .bonus-value { color: #0f172a; font-size: 1.1rem; font-weight: 700; }
    .rules-section { background: #f8fafc; padding: 20px; border-left: 5px solid #1f77b4; border-radius: 8px; margin-bottom: 20px; }
    .rules-title { color: #1f77b4; font-weight: 800; font-size: 1.1rem; margin-bottom: 10px; display: flex; align-items: center; gap: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 3. RÉCUPÉRATION SCORES NHL
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
            cards += f'<div class="{css}"><span class="team">{away}</span><span class="score">{ascor}</span>VS<span class="score">{hscor}</span><span class="team">{home}</span>{badge}</div>'
        return cards + cards
    except: return '<div class="game-card">⚠️ Données NHL indisponibles</div>'

st.markdown(f'<div class="nhl-ticker-wrap"><div class="ticker">{get_nhl_ticker()}</div></div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">🏆 Pool de Hockey 2026</div>', unsafe_allow_html=True)

# 4. CHARGEMENT DES DONNÉES
SID = "1j4g-7V5cLo9WcHNj_T063-rD1rvUKrn11VoRi3TdXww"
def load_data(sn):
    u = f"https://docs.google.com/spreadsheets/d/{SID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sn)}"
    df = pd.read_csv(u); df.columns = df.columns.str.strip(); return df

try:
    df_p, df_pr, df_r = load_data("Participants"), load_data("Prédictions"), load_data("Résultats")
    df_r['Victoires A'] = pd.to_numeric(df_r['Victoires A'], errors='coerce').fillna(0)
    df_r['Victoires B'] = pd.to_numeric(df_r['Victoires B'], errors='coerce').fillna(0)
except Exception as e:
    st.error(f"Erreur : {e}"); st.stop()

# 5. LOGIQUE DE CALCUL
def calc(n):
    t, d = 0, []
    sub = df_pr[df_pr['Nom'].astype(str).str.strip() == str(n).strip()]
    r_pts, b_pts = {"1/8": 1, "1/4": 2, "1/2": 3, "Finale": 4}, {4: 4, 5: 3, 6: 2, 7: 1}
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

# 6. INTERFACE
if 'Nom' in df_p.columns:
    users = df_p['Nom'].dropna().unique()
    scores, details = [], {}
    for n in users:
        p, d = calc(n); scores.append({"Participant": n, "Points": p}); details[n] = d
    
    st.markdown('<div class="sub-title">📊 Classement Général</div>', unsafe_allow_html=True)
    rk = pd.DataFrame(scores).sort_values("Points", ascending=False)
    rk.insert(0, "Rang", range(1, len(rk) + 1))
    st.markdown(f'<div class="table-container">{rk.to_html(index=False)}</div>', unsafe_allow_html=True)

    st.write("---")
    with st.expander("🔍 Analyse des points"):
        for n in users:
            st.subheader(f"Joueur : {n}")
            st.write(pd.DataFrame(details[n]).to_html(index=False), unsafe_allow_html=True)

    with st.expander("📋 Sélections des participants"):
        ac = df_p.columns.tolist()
        cc_n = next((c for c in ac if any(x in c.upper() for x in ["STANLEY", "CUP", "COUPE"])), None)
        mv_n = next((c for c in ac if "MVP" in c.upper()), None)
        for n in users:
            st.markdown(f"### **{n}**")
            ur = df_p[df_p['Nom'].astype(str).str.strip() == str(n).strip()]
            if not ur.empty:
                c1, c2 = st.columns(2)
                if cc_n: c1.markdown(f'<div class="bonus-card">🏆 <div><div class="bonus-label">Stanley Cup</div><div class="bonus-value">{ur[cc_n].iloc[0]}</div></div></div>', unsafe_allow_html=True)
                if mv_n: c2.markdown(f'<div class="bonus-card">🎖️ <div><div class="bonus-label">MVP</div><div class="bonus-value">{ur[mv_n].iloc[0]}</div></div></div>', unsafe_allow_html=True)
            p_p = df_pr[df_pr['Nom'].astype(str).str.strip() == str(n).strip()]
            md = p_p[p_p['Série/Équipes'].notna()]
            if not md.empty: st.write(md[['Ronde', 'Série/Équipes', 'Team Win', '#Match']].to_html(index=False), unsafe_allow_html=True)
            st.write("<hr>", unsafe_allow_html=True)

    with st.expander("📜 Règlement"):
        # Section 1 & 2 : Structure et Pointage
        st.markdown("""
        <div class="rules-section">
            <div class="rules-title">🏒 1. Structure & Pointage Évolutif</div>
            Format éliminatoire (1/8, 1/4, 1/2 et Finale). Les points par victoire augmentent à chaque ronde :
            <div class="table-container" style="margin-top:15px;">
                <table>
                    <tr><th>Ronde</th><th>Pts / Victoire</th><th>Boni Série</th></tr>
                    <tr><td>1/8 de finale</td><td>1 pt</td><td>+2 pts</td></tr>
                    <tr><td>1/4 de finale</td><td>2 pts</td><td>+2 pts</td></tr>
                    <tr><td>1/2 finale</td><td>3 pts</td><td>+2 pts</td></tr>
                    <tr><td>Finale</td><td>4 pts</td><td>+2 pts</td></tr>
                </table>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Section 3 : Bonus Précision
        st.markdown("""
        <div class="rules-section">
            <div class="rules-title">🎯 2. Bonus de Précision (# Matchs)</div>
            Si ton équipe gagne dans le nombre exact de matchs prédits :
            <div style="display:flex; flex-wrap:wrap; gap:10px; margin-top:10px;">
                <div class="bonus-card" style="flex:1; min-width:100px; margin-bottom:0;">
                    <div><div class="bonus-label">En 4</div><div class="bonus-value">+4 pts</div></div>
                </div>
                <div class="bonus-card" style="flex:1; min-width:100px; margin-bottom:0;">
                    <div><div class="bonus-label">En 5</div><div class="bonus-value">+3 pts</div></div>
                </div>
                <div class="bonus-card" style="flex:1; min-width:100px; margin-bottom:0;">
                    <div><div class="bonus-label">En 6</div><div class="bonus-value">+2 pts</div></div>
                </div>
