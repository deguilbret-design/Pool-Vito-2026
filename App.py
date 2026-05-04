import streamlit as st
import pandas as pd
import requests

# 1. CONFIGURATION ET STYLES
st.set_page_config(page_title="Pool Vito 2026", layout="wide")

st.markdown("""
<style>
    .main-title { font-size: 2.2rem; font-weight: 800; color: #1e293b; text-align: center; margin-bottom: 0; }
    .sub-title { font-size: 1.5rem; font-weight: 700; color: #334155; margin-top: 20px; border-bottom: 2px solid #e2e8f0; }
    .nhl-ticker-wrap { background: #0f172a; color: white; padding: 10px 0; overflow: hidden; margin-bottom: 20px; border-radius: 8px; }
    .ticker { display: flex; white-space: nowrap; animation: marquee 30s linear infinite; }
    @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .rules-section { background: #f8fafc; padding: 15px; border-left: 4px solid #3b82f6; border-radius: 4px; margin: 10px 0; }
    .bonus-card { background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px; text-align: center; }
    .bonus-label { font-size: 0.75rem; color: #64748b; text-transform: uppercase; }
    .bonus-value { font-size: 1.1rem; font-weight: 700; color: #1e293b; }
    .table-container table { width: 100%; border-collapse: collapse; }
    .table-container th { background: #3b82f6; color: white; padding: 8px; }
    .table-container td { border-bottom: 1px solid #e2e8f0; padding: 8px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# 2. CHARGEMENT DES DONNÉES
SHEET_ID = "1W4N32Z8z4iS6o8qP8Z_0pZ9p8Z4iS6o8qP8Z_0pZ9p" # Remplace par ton ID réel
def load_data(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    return pd.read_csv(url)

try:
    df_part = load_data("Participants")
    df_pred = load_data("Prédictions")
    df_res = load_data("Résultats")
    
    # Nettoyage automatique des types (Règle le bug du .0)
    df_pred['#Match'] = pd.to_numeric(df_pred['#Match'], errors='coerce').fillna(0)
    df_res['Victoires A'] = pd.to_numeric(df_res['Victoires A'], errors='coerce').fillna(0)
    df_res['Victoires B'] = pd.to_numeric(df_res['Victoires B'], errors='coerce').fillna(0)
except:
    st.error("Lien Google Sheets inaccessible."); st.stop()

# 3. FONCTIONS UTILES
def get_nhl_ticker():
    try:
        r = requests.get("https://api-web.nhle.com/v1/score/now").json()
        games = r.get('games', [])
        if not games: return "Aucun match en cours"
        return "  |  ".join([f"{g['awayTeam']['abbrev']} {g['awayScore']} - {g['homeScore']} {g['homeTeam']['abbrev']} ({g['gameState']})" for g in games])
    except: return "NHL Ticker indisponible"

# 4. LOGIQUE DE CALCUL (CORRIGÉE)
def calculer_tout(nom):
    tot, det = 0, []
    p_preds = df_pred[df_pred['Nom'].astype(str).str.strip() == str(nom).strip()]
    pts_r = {"1/8": 1, "1/4": 2, "1/2": 3, "Finale": 4}
    bon_m = {4: 4, 5: 3, 6: 2, 7: 1}

    for _, prd in p_preds.iterrows():
        s, c, r = str(prd['Série/Équipes']).strip(), str(prd['Team Win']).strip(), str(prd['Ronde']).strip()
        m_r = df_res[df_res['Série/Équipes'].astype(str).str.strip() == s]
        pts_s = 0
        
        if not m_r.empty:
            res = m_r.iloc[0]
            eA, eB = str(res['Équipe A']).strip(), str(res['Équipe B']).strip()
            
            # Points par victoire en cours de série
            v = res['Victoires A'] if c == eA else (res['Victoires B'] if c == eB else 0)
            pts_s += (v * pts_r.get(r, 1))

            # Bonus de fin de série
            if str(res['Fini']).upper() == "OUI":
                vr = res['Équipe A'] if res['Victoires A'] > res['Victoires B'] else res['Équipe B']
                mr = int(res['Victoires A'] + res['Victoires B'])
                prd_m = int(float(prd['#Match']))
                
                # Cas A : Le participant a choisi le bon vainqueur
                if c == str(vr).strip():
                    pts_s += 2
                    if prd_m == mr:
                        pts_s += bon_m.get(mr, 0)
                
                # Cas B : Règle spéciale Match 7 (Point de consolation si perdu)
                elif prd_m == 7 and mr == 7:
                    pts_s += 1
            
            tot += pts_s
        det.append({"Statut": "✅" if pts_s > 0 else "❌", "Série": s, "Choix": c, "Points": int(pts_s)})

    return int(tot), det

# 5. INTERFACE
st.markdown(f'<div class="nhl-ticker-wrap"><div class="ticker">{get_nhl_ticker()}</div></div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">🏆 Pool de Hockey 2026</div>', unsafe_allow_html=True)

# Calcul des scores
scores = []
for n in df_part['Nom'].unique():
    t, _ = calculer_tout(n)
    scores.append({"Nom": n, "Points": t})

tab1, tab2 = st.tabs(["📊 Classement", "🔍 Analyse"])

with tab1:
    st.markdown('<div class="sub-title">📊 Classement Général</div>', unsafe_allow_html=True)
    # BLOC DES PRIX
    st.markdown('<div style="text-align:center; margin-bottom:15px;"><span style="background:#f1f5f9; padding:5px 15px; border-radius:20px; font-size:0.85rem; color:#475569; border:1px solid #cbd5e1;">💰 <b>Positions gagnantes :</b> 🥇 1er : 100$ &nbsp;|&nbsp; 🥈 2e : 20$</span></div>', unsafe_allow_html=True)
    
    df_rank = pd.DataFrame(scores).sort_values("Points", ascending=False)
    df_rank.insert(0, "Rang", range(1, len(df_rank) + 1))
    st.markdown(f'<div class="table-container">{df_rank.to_html(index=False)}</div>', unsafe_allow_html=True)

with tab2:
    user = st.selectbox("Sélectionnez un participant :", df_part['Nom'].unique())
    total, details = calculer_tout(user)
    st.metric("Score Total", f"{total} pts")
    st.table(pd.DataFrame(details))

# 6. RÈGLEMENTS (FIN DU SCRIPT)
with st.expander("📜 Règlement Officiel"):
    st.markdown('<div class="rules-section"><b>1. Pointage Évolutif</b></div>', unsafe_allow_html=True)
    t = '<div class="table-container"><table><tr><th>Ronde</th><th>Victoire</th><th>Boni Série</th></tr>'
    t += '<tr><td>1/8 de finale</td><td>1 pt</td><td>+2 pts</td></tr>'
    t += '<tr><td>1/4 de finale</td><td>2 pts</td><td>+2 pts</td></tr>'
    t += '<tr><td>1/2 finale</td><td>3 pts</td><td>+2 pts</td></tr>'
    t += '<tr><td>Finale</td><td>4 pts</td><td>+2 pts</td></tr></table></div>'
    st.markdown(t, unsafe_allow_html=True)

    st.markdown('<div class="rules-section" style="margin-top:15px;"><b>2. Bonus de Précision (# matchs)</b></div>', unsafe_allow_html=True)
    b = '<div style="display:flex; flex-wrap:wrap; gap:10px;">'
    b += '<div class="bonus-card" style="flex:1; min-width:80px;"><div><div class="bonus-label">En 4</div><div class="bonus-value">+4</div></div></div>'
    b += '<div class="bonus-card" style="flex:1; min-width:80px;"><div><div class="bonus-label">En 5</div><div class="bonus-value">+3</div></div></div>'
    b += '<div class="bonus-card" style="flex:1; min-width:80px;"><div><div class="bonus-label">En 6</div><div class="bonus-value">+2</div></div></div>'
    b += '<div class="bonus-card" style="flex:1; min-width:80px;"><div><div class="bonus-label">En 7</div><div class="bonus-value">+1</div></div></div></div>'
    st.markdown(b, unsafe_allow_html=True)
    st.markdown('<p style="font-size:0.8rem; color:#64748b; margin-top:5px;"><i>*Exception Match 7 : Le point est accordé même si votre équipe perd la série.</i></p>', unsafe_allow_html=True)
