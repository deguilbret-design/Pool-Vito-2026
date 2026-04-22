import streamlit as st
import pandas as pd
import urllib.parse
import requests
from datetime import datetime
import pytz

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="Pool de Hockey 2026", layout="wide")

# 2. DESIGN & STYLE CSS (TICKER MOBILE FIX + TABLEAU COMPACT)
st.markdown("""
    <style>
    /* BANNIÈRE NHL - FIX MOBILE INFINI */
    .nhl-ticker-wrap {
        width: 100%; overflow: hidden; background: #0b0f19;
        border-bottom: 2px solid #1f77b4; margin: -50px -50px 30px -50px;
        padding: 10px 0; box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    .ticker { 
        display: inline-flex; /* Fix pour le défilement mobile */
        white-space: nowrap;
        animation: ticker 9s linear infinite; 
    }
    @keyframes ticker { 
        0% { transform: translate3d(0, 0, 0); } 
        100% { transform: translate3d(-50%, 0, 0); } 
    }
    .game-card {
        flex-shrink: 0; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 6px; margin-right: 20px; padding: 5px 15px; display: flex; align-items: center; gap: 10px; min-width: 230px;
    }
    .game-card.live { border-color: #ff4b4b; background: rgba(255, 75, 75, 0.1); }
    .game-card.final { border-color: #28a745; }
    .team { font-weight: 700; font-size: 0.9rem; color: #fff; width: 40px; text-align: center; }
    .score { background: #1e293b; color: #fbbf24; font-weight: 900; padding: 2px 8px; border-radius: 4px; min-width: 25px; text-align: center; }
    .status-badge { font-size: 0.6rem; font-weight: bold; padding: 2px 5px; border-radius: 3px; background: rgba(255,255,255,0.1); color: #94a3b8; }
    .live-dot { height: 6px; width: 6px; background: #ff4b4b; border-radius: 50%; display: inline-block; margin-right: 5px; animation: blink 1s infinite; }
    @keyframes blink { 0% {opacity: 1;} 50% {opacity: 0.2;} 100% {opacity: 1;} }

    /* TITRES ET TIMESTAMPS */
    .main-title { text-align: center; color: #1f77b4; font-size: 2.2rem; font-weight: 800; margin-bottom: 5px; }
    .sync-time { text-align: center; color: #64748b; font-size: 0.85rem; font-style: italic; margin-bottom: 25px; }
    .sub-title { text-align: center; color: #333; margin-top: 15px; font-weight: 700; font-size: 1.4rem; margin-bottom: 20px; }

    /* TABLEAU DE CLASSEMENT COMPACT & CENTRÉ */
    .table-container { display: flex; justify-content: center; width: 100%; }
    table { 
        width: auto !important; margin: auto; 
        border-radius: 10px; overflow: hidden; border-collapse: collapse; 
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    th { background: #1f77b4; color: white; padding: 12px 25px; text-align: center !important; }
    td { padding: 12px 25px; border-bottom: 1px solid #eee; text-align: center !important; font-weight: 600; }
    
    .bonus-card { background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; display: flex; align-items: center; gap: 15px; margin-bottom: 15px; }
    .bonus-label { color: #64748b; font-size: 0.7rem; font-weight: bold; text-transform: uppercase; }
    .bonus-value { color: #0f172a; font-size: 1.1rem; font-weight: 700; }
    .rules-section { background: #f8fafc; padding: 15px; border-left: 4px solid #1f77b4; margin-bottom: 10px; border-radius: 4px; }
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
            cards += f'<div class="{css}"><span class="team">{away}</span><span class="score">{ascor}</span><span style="color:#475569;font-size:0.7rem;">VS</span><span class="score">{hscor}</span><span class="team">{home}</span>{badge}</div>'
        # Retourne les cartes doublées pour l'effet de boucle infinie
        return cards + cards
    except: return '<div class="game-card">⚠️ Données NHL indisponibles</div>'

# AFFICHAGE
st.markdown(f'<div class="nhl-ticker-wrap"><div class="ticker">{get_nhl_ticker()}</div></div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">🏆 Pool de Hockey 2026</div>', unsafe_allow_html=True)

# TIMESTAMP (QUÉBEC)
tz_qc = pytz.timezone('America/Montreal')
last_sync = datetime.now(tz_qc).strftime("%d/%m/%Y à %H:%M:%S")
st.markdown(f'<div class="sync-time">Mise à jour : {last_sync}</div>', unsafe_allow_html=True)

# 4. DATA LOADING
SID = "1j4g-7V5cLo9WcHNj_T063-rD1rvUKrn11VoRi3TdXww"
def load_data(sn):
    url = f"https://docs.google.com/spreadsheets/d/{SID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sn)}"
    df = pd.read_csv(url); df.columns = df.columns.str.strip(); return df

try:
    df_part, df_pred, df_res = load_data("Participants"), load_data("Prédictions"), load_data("Résultats")
    df_res['Victoires A'] = pd.to_numeric(df_res['Victoires A'], errors='coerce').fillna(0)
    df_res['Victoires B'] = pd.to_numeric(df_res['Victoires B'], errors='coerce').fillna(0)
except Exception as e:
    st.error(f"Erreur : {e}"); st.stop()

# 5. CALCULS
def calculer_tout(nom):
    tot, det = 0, []
    p_preds = df_pred[df_pred['Nom'].astype(str).str.strip() == str(nom).strip()]
    pts_r = {"1/8": 1, "1/4": 2, "1/2": 3, "Finale": 4}
    bon_m = {4: 4, 5: 3, 6: 2, 7: 1}
    for _, prd in p_preds.iterrows():
        s, c, r = str(prd['Série/Équipes']).strip(), str(prd['Team Win']).strip(), str(prd['Ronde']).strip()
        m_r = df_res[df_res['Série/Équipes'].astype(str).str.strip() == s]
        pts_s, stt = 0, "❌"
        if not m_r.empty:
            res = m_r.iloc[0]; eA = str(res['Équipe A']).strip(); eB = str(res['Équipe B']).strip()
            v = res['Victoires A'] if c == eA else (res['Victoires B'] if c == eB else 0)
            pts_s += (v * pts_r.get(r, 1))
            if str(res['Fini']).upper() == "OUI":
                vr = res['Équipe A'] if res['Victoires A'] > res['Victoires B'] else res['Équipe B']
                mr = int(res['Victoires A'] + res['Victoires B'])
                if c == str(vr).strip():
                    pts_s += 2
                    try:
                        if int(prd['#Match']) == mr: pts_s += bon_m.get(mr, 0)
                    except: pass
                elif str(prd['#Match']) == "7" and mr == 7: pts_s += 1
            if pts_s > 0: stt = "✅"
            tot += pts_s
        det.append({"Statut": stt, "Série": s, "Choix": c, "Points": int(pts_s)})
    return int(tot), det

# 6. UI
if 'Nom' in df_part.columns:
    participants = df_part['Nom'].dropna().unique()
    scores, details_p = [], {}
    for n in participants:
        p, d = calculer_tout(n); scores.append({"Participant": n, "Points": p}); details_p[n] = d
    
    st.markdown('<div class="sub-title">📊 Classement Général</div>', unsafe_allow_html=True)
    df_rank = pd.DataFrame(scores).sort_values("Points", ascending=False)
    df_rank.insert(0, "Rang", range(1, len(df_rank) + 1))
    
    # TABLEAU CENTRÉ ET COMPACT
    st.markdown(f'<div class="table-container">{df_rank.to_html(index=False)}</div>', unsafe_allow_html=True)

    st.write("---")
    with st.expander("🔍 Analyse des points"):
        for n in participants:
            st.subheader(f"Joueur : {n}")
            st.write(pd.DataFrame(details_p[n]).to_html(index=False), unsafe_allow_html=True)

    with st.expander("📋 Sélections des participants"):
        ac = df_part.columns.tolist()
        cc = next((c for c in ac if any(x in c.upper() for x in ["STANLEY", "CUP", "COUPE"])), None)
        cm = next((c for c in ac if "MVP" in c.upper()), None)
        for n in participants:
            st.markdown(f"### **{n}**")
            ur = df_part[df_part['Nom'].astype(str).str.strip() == str(n).strip()]
            if not ur.empty:
                c1, c2 = st.columns(2)
                if cc: c1.markdown(f'<div class="bonus-card">🏆 <div><div class="bonus-label">Stanley Cup</div><div class="bonus-value">{ur[cc].iloc[0]}</div></div></div>', unsafe_allow_html=True)
                if cm: c2.markdown(f'<div class="bonus-card">🎖️ <div><div class="bonus-label">MVP</div><div class="bonus-value">{ur[cm].iloc[0]}</div></div></div>', unsafe_allow_html=True)
            p_p = df_pred[df_pred['Nom'].astype(str).str.strip() == str(n).strip()]
            md = p_p[p_p['Série/Équipes'].notna()]
            if not md.empty: st.write(md[['Ronde', 'Série/Équipes', 'Team Win', '#Match']].to_html(index=False), unsafe_allow_html=True)
            st.write("<hr>", unsafe_allow_html=True)

    with st.expander("📜 Règlement"):
        st.markdown('<div class="rules-section">1/8 (1pt/vic), 1/4 (2pts/vic), 1/2 (3pts/vic), Finale (4pts/vic). Bonus Série (+2). Bonus Matchs: 4(+4), 5(+3), 6(+2), 7(+1). MVP (+10).</div>', unsafe_allow_html=True)
