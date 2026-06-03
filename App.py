import streamlit as st
import pandas as pd
import urllib.parse
import requests

# 1. CONFIGURATION
st.set_page_config(page_title="Pool de Hockey 2026", layout="wide")

# 2. DESIGN PRO & FIXES VISUELS
st.markdown("""
    <style>
    .nhl-ticker-wrap {
        width: 100%; overflow: hidden; background: #0b0f19;
        border-bottom: 2px solid #1f77b4; margin: -50px -50px 30px -50px;
        padding: 10px 0; box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    .ticker { 
        display: flex; width: max-content; 
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
    .live-dot { height: 6px; width: 6px; background: #ff4b4b; border-radius: 50%; display: inline-block; animation: blink 1s infinite; }
    @keyframes blink { 0% {opacity: 1;} 50% {opacity: 0.2;} 100% {opacity: 1;} }

    .main-title { text-align: center; color: #1f77b4; font-size: 2.2rem; font-weight: 800; margin-bottom: 5px; }
    .sub-title { text-align: center; color: #333; margin-top: 15px; font-weight: 700; font-size: 1.4rem; margin-bottom: 20px; }

    .table-container { display: flex; justify-content: center; width: 100%; }
    table { 
        width: auto !important;
        margin-left: auto; margin-right: auto;
        border-radius: 10px; overflow: hidden; border-collapse: collapse; 
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    th { background: #1f77b4; color: white; padding: 12px 25px; font-size: 0.9rem; text-transform: uppercase; text-align: center !important; }
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
        return cards + cards
    except: return '<div class="game-card">⚠️ Données NHL indisponibles</div>'

st.markdown(f'<div class="nhl-ticker-wrap"><div class="ticker">{get_nhl_ticker()}</div></div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">🏆 Pool de Hockey 2026</div>', unsafe_allow_html=True)

# 4. CHARGEMENT DES DONNÉES
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

# 5. LOGIQUE DE CALCUL
def calculer_tout(nom):
    tot, det = 0, []
    p_preds = df_pred[df_pred['Nom'].astype(str).str.strip() == str(nom).strip()]
    pts_r = {"1/8": 1, "1/4": 2, "1/2": 3, "1/1": 4}
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
                vr = str(res['Équipe A'] if res['Victoires A'] > res['Victoires B'] else res['Équipe B']).strip()
                mr = int(res['Victoires A'] + res['Victoires B'])
                
                # A. Calcul pour le vainqueur de la série
                if c == vr:
                    pts_s += 2
                    try:
                        if int(float(prd['#Match'])) == mr:
                            pts_s += bon_m.get(mr, 0)
                    except: pass
                # B. Consolation Match 7 (pour le perdant)
                else:
                    try:
                        if int(float(prd['#Match'])) == 7 and mr == 7:
                            pts_s += 1
                    except: pass
            
            if pts_s > 0: stt = "✅"
            tot += pts_s
        det.append({"Statut": stt, "Série": s, "Choix": c, "Points": int(pts_s)})
    
    # C. Boni Parcours Champion (depuis Participants)
    p_row = df_part[df_part['Nom'].astype(str).str.strip() == str(nom).strip()]
    if not p_row.empty:
        ac = df_part.columns.tolist()
        cc_col = next((c for c in ac if any(x in c.upper() for x in ["STANLEY", "COUPE"])), None)
        if cc_col:
            mon_champ = str(p_row[cc_col].iloc[0]).strip()
            for _, res in df_res.iterrows():
                if str(res['Fini']).upper() == "OUI":
                    gagnant = str(res['Équipe A'] if res['Victoires A'] > res['Victoires B'] else res['Équipe B']).strip()
                    if gagnant == mon_champ:
                        info = df_pred[df_pred['Série/Équipes'] == res['Série/Équipes']]
                        if not info.empty:
                            ronde = str(info['Ronde'].iloc[0]).strip()
                            bonus = 4 if ronde == "Finale" else 2
                            tot += bonus
                            det.append({"Statut": "🏆", "Série": f"Boni {ronde}", "Choix": mon_champ, "Points": bonus})
                            
    return int(tot), det

# 6. INTERFACE
if 'Nom' in df_part.columns:
    participants = df_part['Nom'].dropna().unique()
    scores, details_p = [], {}
    for n in participants:
        p, d = calculer_tout(n); scores.append({"Participant": n, "Points": p}); details_p[n] = d
    
    st.markdown('<div class="sub-title">📊 Classement Général</div>', unsafe_allow_html=True)
    
    # BLOC DES PRIX
    st.markdown('<div style="text-align:center; margin-bottom:15px;"><span style="background:#f1f5f9; padding:5px 15px; border-radius:20px; font-size:0.85rem; color:#475569; border:1px solid #cbd5e1;">💰 <b>Positions gagnantes :</b> 🥇 1er : 100$ &nbsp;|&nbsp; 🥈 2e : 20$</span></div>', unsafe_allow_html=True)
    
    df_rank = pd.DataFrame(scores).sort_values("Points", ascending=False)
    df_rank.insert(0, "Rang", range(1, len(df_rank) + 1))
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

    with st.expander("📜 Règlement Officiel"):
        st.markdown('<div class="rules-section"><b>1. Pointage Évolutif</b><br>Les points par victoire augmentent à chaque ronde :</div>', unsafe_allow_html=True)
        html_table = '<div class="table-container"><table><tr><th>Ronde</th><th>Victoire</th><th>Boni Série</th></tr>'
        html_table += '<tr><td>1/8 de finale</td><td>1 pt</td><td>+2 pts</td></tr>'
        html_table += '<tr><td>1/4 de finale</td><td>2 pts</td><td>+2 pts</td></tr>'
        html_table += '<tr><td>1/2 finale</td><td>3 pts</td><td>+2 pts</td></tr>'
        html_table += '<tr><td>Finale</td><td>4 pts</td><td>+2 pts</td></tr></table></div>'
        st.markdown(html_table, unsafe_allow_html=True)

        st.markdown('<div class="rules-section" style="margin-top:20px;"><b>2. Bonus de Précision (# de matchs)</b></div>', unsafe_allow_html=True)
        bonus_cards = '<div style="display:flex; flex-wrap:wrap; gap:10px; margin-top:10px;">'
        bonus_cards += '<div class="bonus-card" style="flex:1; min-width:100px;"><div><div class="bonus-label">En 4</div><div class="bonus-value">+4 pts</div></div></div>'
        bonus_cards += '<div class="bonus-card" style="flex:1; min-width:100px;"><div><div class="bonus-label">En 5</div><div class="bonus-value">+3 pts</div></div></div>'
        bonus_cards += '<div class="bonus-card" style="flex:1; min-width:100px;"><div><div class="bonus-label">En 6</div><div class="bonus-value">+2 pts</div></div></div>'
        bonus_cards += '<div class="bonus-card" style="flex:1; min-width:100px;"><div><div class="bonus-label">En 7</div><div class="bonus-value">+1 pt</div></div></div></div>'
        st.markdown(bonus_cards, unsafe_allow_html=True)
        st.markdown('<p style="font-size:0.85rem; color:#64748b; margin-left:5px;"><i>*Exception Match 7 : Le point est accordé même si votre équipe perd la série.</i></p>', unsafe_allow_html=True)

        st.markdown('<div class="rules-section" style="margin-top:20px;"><b>3. Bonus Équipe Championne et MVP</b></div>', unsafe_allow_html=True)
        st.markdown('• <b>Parcours Champion :</b> R1 (+2), R2 (+2), R3 (+2), Victoire Finale (+4)<br>• <b>Trophée MVP :</b> +10 pts si ton choix remporte le Conn Smythe.', unsafe_allow_html=True)
