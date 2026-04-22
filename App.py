import streamlit as st
import pandas as pd
import urllib.parse
import requests

# 1. CONFIGURATION
st.set_page_config(page_title="Pool de Hockey 2026", layout="wide")

# 2. DESIGN & STYLE CSS (DÉCOUPÉ POUR ÉVITER LES BOGUES)
st.markdown('<style>', unsafe_allow_html=True)
st.markdown('.nhl-ticker-wrap { width: 100%; overflow: hidden; background: #0b0f19; border-bottom: 2px solid #1f77b4; margin: -50px -50px 30px -50px; padding: 10px 0; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }', unsafe_allow_html=True)
st.markdown('.ticker { display: flex; width: max-content; animation: ticker 15s linear infinite; }', unsafe_allow_html=True)
st.markdown('@keyframes ticker { 0% { transform: translate3d(0, 0, 0); } 100% { transform: translate3d(-50%, 0, 0); } }', unsafe_allow_html=True)
st.markdown('.game-card { flex-shrink: 0; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 6px; margin-right: 20px; padding: 5px 15px; display: flex; align-items: center; gap: 10px; min-width: 230px; }', unsafe_allow_html=True)
st.markdown('.team { font-weight: 700; font-size: 0.9rem; color: #fff; width: 40px; text-align: center; }', unsafe_allow_html=True)
st.markdown('.score { background: #1e293b; color: #fbbf24; font-weight: 900; padding: 2px 8px; border-radius: 4px; min-width: 25px; text-align: center; }', unsafe_allow_html=True)
st.markdown('.main-title { text-align: center; color: #1f77b4; font-size: 2.2rem; font-weight: 800; margin-bottom: 5px; }', unsafe_allow_html=True)
st.markdown('.sub-title { text-align: center; color: #333; margin-top: 15px; font-weight: 700; font-size: 1.4rem; margin-bottom: 20px; }', unsafe_allow_html=True)
st.markdown('.table-container { display: flex; justify-content: center; width: 100%; }', unsafe_allow_html=True)
st.markdown('table { width: auto !important; margin: auto; border-radius: 10px; overflow: hidden; border-collapse: collapse; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }', unsafe_allow_html=True)
st.markdown('th { background: #1f77b4; color: white; padding: 12px 25px; text-align: center !important; text-transform: uppercase; font-size: 0.85rem; }', unsafe_allow_html=True)
st.markdown('td { padding: 12px 25px; border-bottom: 1px solid #eee; text-align: center !important; font-weight: 600; }', unsafe_allow_html=True)
st.markdown('.bonus-card { background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; display: flex; align-items: center; gap: 15px; margin-bottom: 15px; }', unsafe_allow_html=True)
st.markdown('.bonus-label { color: #64748b; font-size: 0.7rem; font-weight: bold; text-transform: uppercase; }', unsafe_allow_html=True)
st.markdown('.bonus-value { color: #0f172a; font-size: 1.1rem; font-weight: 700; }', unsafe_allow_html=True)
st.markdown('.rules-section { background: #f8fafc; padding: 20px; border-left: 5px solid #1f77b4; border-radius: 8px; margin-bottom: 20px; }', unsafe_allow_html=True)
st.markdown('.rules-title { color: #1f77b4; font-weight: 800; font-size: 1.1rem; margin-bottom: 10px; }', unsafe_allow_html=True)
st.markdown('</style>', unsafe_allow_html=True)

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
            status, css = g['gameState'], "game-card"
            bdg = "FINAL" if status in ["OFF", "FINAL"] else "À VENIR"
            if status in ["LIVE", "CRIT"]:
                css += " live"
                bdg = "P" + str(g.get('periodDescriptor', {}).get('number', 1))
            html += f'<div class="{css}"><span class="team">{away}</span><span class="score">{ascor}</span>VS'
            html += f'<span class="score">{hscor}</span><span class="team">{home}</span>'
            html += f'<span style="font-size:0.6rem;margin-left:5px;">{bdg}</span></div>'
        return html + html
    except: return '<div class="game-card">⚠️ NHL Indisponible</div>'

st.markdown(f'<div class="nhl-ticker-wrap"><div class="ticker">{get_nhl_ticker()}</div></div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">🏆 Vito\'s Super Hockey Pool 2026</div>', unsafe_allow_html=True)

# 4. CHARGEMENT DATA
SID = "1j4g-7V5cLo9WcHNj_T063-rD1rvUKrn11VoRi3TdXww"
def load_data(sn):
    u = f"https://docs.google.com/spreadsheets/d/{SID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sn)}"
    df = pd.read_csv(u); df.columns = df.columns.str.strip(); return df

try:
    df_p, df_pr, df_res = load_data("Participants"), load_data("Prédictions"), load_data("Résultats")
    df_res['Victoires A'] = pd.to_numeric(df_res['Victoires A'], errors='coerce').fillna(0)
    df_res['Victoires B'] = pd.to_numeric(df_res['Victoires B'], errors='coerce').fillna(0)
except Exception as e:
    st.error(f"Erreur : {e}"); st.stop()

# 5. CALCULS
def calculer_tout(nom):
    tot, det = 0, []
    sub = df_pr[df_pr['Nom'].astype(str).str.strip() == str(nom).strip()]
    r_pts, b_pts = {"1/8": 1, "1/4": 2, "1/2": 3, "Finale": 4}, {4: 4, 5: 3, 6: 2, 7: 1}
    for _, prd in sub.iterrows():
        se, ch, ro = str(prd['Série/Équipes']).strip(), str(prd['Team Win']).strip(), str(prd['Ronde']).strip()
        m = df_res[df_res['Série/Équipes'].astype(str).str.strip() == se]
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
                        if int(prd['#Match']) == mr: ps += b_pts.get(mr, 0)
                    except: pass
                elif str(prd['#Match']) == "7" and mr == 7: ps += 1
            if ps > 0: ok = "✅"
            tot += ps
        det.append({"Statut": ok, "Série": se, "Choix": ch, "Points": int(ps)})
    return int(tot), det

# 6. INTERFACE
if 'Nom' in df_p.columns:
    users = df_p['Nom'].dropna().unique()
    scores, details = [], {}
    for n in users:
        p, d = calculer_tout(n); scores.append({"Participant": n, "Points": p}); details[n] = d
    
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
        st.markdown('<div class="rules-section"><div class="rules-title">🏒 1. Pointage Évolutif</div> Les points par victoire selon la ronde actuelle :', unsafe_allow_html=True)
        t = '<table><tr><th>Ronde</th><th>Pts / Victoire</th><th>Boni</th></tr>'
        t += '<tr><td>1/8</td><td>1 pt</td><td>+2 pts</td></tr>'
        t += '<tr><td>1/4</td><td>2 pts</td><td>+2 pts</td></tr>'
        t += '<tr><td>1/2</td><td>3 pts</td><td>+2 pts</td></tr>'
        t += '<tr><td>Finale</td><td>4 pts</td><td>+2 pts</td></tr></table>'
        st.markdown(f'<div class="table-container" style="margin-top:10px;">{t}</div></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="rules-section"><div class="rules-title">🎯 2. Bonus de Précision (# Matchs)</div> Si ton équipe gagne dans le bon nombre de matchs.', unsafe_allow_html=True)
        b = '<div style="display:flex; gap:10px; flex-wrap:wrap; margin-top:10px;">'
        b += '<div class="bonus-card"><div><div class="bonus-label">En 4</div><div class="bonus-value">+4 pts</div></div></div>'
        b += '<div class="bonus-card"><div><div class="bonus-label">En 5</div><div class="bonus-value">+3 pts</div></div></div>'
        b += '<div class="bonus-card"><div><div class="bonus-label">En 6</div><div class="bonus-value">+2 pts</div></div></div>'
        b += '<div class="bonus-card"><div><div class="bonus-label">En 7</div><div class="bonus-value">+1 pt</div></div></div></div>'
        st.markdown(b, unsafe_allow_html=True)
        st.markdown('<p style="font-size:0.85rem; color:#64748b; margin-top:10px;"><i>*Exception Match 7 : Accordé même si ton équipe perd la série.</i></p></div>', unsafe_allow_html=True)

        st.markdown('<div class="rules-section"><div class="rules-title">🏆 3. Bonus Globaux</div>', unsafe_allow_html=True)
        st.markdown('• <b>Parcours Champion :</b> R1 (+2), R2 (+2), R3 (+2), Finale (+4)<br>', unsafe_allow_html=True)
        st.markdown('• <b>Trophée MVP :</b> +10 pts si ton choix remporte le Conn Smythe.</div>', unsafe_allow_html=True)
