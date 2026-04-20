import streamlit as st
import pandas as pd
import urllib.parse

# 1. CONFIGURATION ET STYLE
st.set_page_config(page_title="Pool de Hockey 2026", layout="wide")

st.markdown("""
    <style>
    .main-title { text-align: center; color: #1f77b4; font-size: 2.2rem; font-weight: bold; margin-bottom: 20px; }
    .sub-title { text-align: center; color: #333; margin-top: 20px; font-weight: bold; }
    
    /* Style pour les Tableaux */
    .classement-container { display: flex; justify-content: center; margin-bottom: 30px; }
    table { width: 100%; border-collapse: collapse; border-radius: 8px; overflow: hidden; font-family: sans-serif; }
    th { background-color: #1f77b4; color: white; padding: 12px; text-align: center !important; }
    td { padding: 10px; text-align: center !important; border-bottom: 1px solid #eee; }
    tr:hover { background-color: #f9f9f9; }
    
    /* Cartes de Bonus (Champion/MVP) */
    .bonus-card { 
        background-color: #eef6fb; 
        border: 1px solid #b6d4fe; 
        border-radius: 10px; 
        padding: 15px; 
        margin-bottom: 20px; 
        display: flex; 
        align-items: center; 
        justify-content: flex-start;
        gap: 20px;
        min-height: 80px;
    }
    .bonus-label { color: #084298; font-weight: bold; font-size: 0.75rem; text-transform: uppercase; display: block; margin-bottom: 2px; }
    .bonus-value { font-size: 1.25rem; font-weight: bold; color: #333; line-height: 1.2; }
    .bonus-icon { font-size: 2.2rem; min-width: 40px; text-align: center; }
    
    /* Section Règlement */
    .rules-section { background-color: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 5px solid #1f77b4; margin-bottom: 20px; }
    .rules-section h4 { color: #1f77b4; margin-top: 0; border-bottom: 1px solid #ddd; padding-bottom: 5px; }
    .rules-table { width: auto !important; margin: 10px 0; }
    .rules-table th { background-color: #444 !important; font-size: 0.9rem; padding: 8px; }
    
    .stExpander { border: 1px solid #ddd !important; border-radius: 8px !important; margin-bottom: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title">🏆 Pool de Hockey 2026</div>', unsafe_allow_html=True)

# --- CONNEXION DONNÉES ---
SHEET_ID = "1j4g-7V5cLo9WcHNj_T063-rD1rvUKrn11VoRi3TdXww"

def load_data(sheet_name):
    sheet_name_encoded = urllib.parse.quote(sheet_name)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name_encoded}"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    return df

try:
    df_part = load_data("Participants")
    df_pred = load_data("Prédictions")
    df_res = load_data("Résultats")
    df_res['Victoires A'] = pd.to_numeric(df_res['Victoires A'], errors='coerce').fillna(0)
    df_res['Victoires B'] = pd.to_numeric(df_res['Victoires B'], errors='coerce').fillna(0)
except Exception as e:
    st.error(f"Erreur de lecture des données : {e}")
    st.stop()

# --- LOGIQUE DE CALCUL ---
def calculer_tout(nom):
    total_points = 0
    liste_details = []
    p_preds = df_pred[df_pred['Nom'].astype(str).str.strip() == str(nom).strip()]
    pts_ronde = {"1/8": 1, "1/4": 2, "1/2": 3, "Finale": 4}
    bonus_matchs_dict = {4: 4, 5: 3, 6: 2, 7: 1}

    for _, pred in p_preds.iterrows():
        serie = str(pred['Série/Équipes']).strip()
        choix = str(pred['Team Win']).strip()
        ronde = str(pred['Ronde']).strip()
        match_res = df_res[df_res['Série/Équipes'].astype(str).str.strip() == serie]
        pts_serie, statut = 0, "❌"
        
        if not match_res.empty:
            res = match_res.iloc[0]
            eqA, eqB = str(res['Équipe A']).strip(), str(res['Équipe B']).strip()
            vics = res['Victoires A'] if choix == eqA else (res['Victoires B'] if choix == eqB else 0)
            pts_serie += (vics * pts_ronde.get(ronde, 1))
            
            if str(res['Fini']).upper() == "OUI":
                v_reel = res['Équipe A'] if res['Victoires A'] > res['Victoires B'] else res['Équipe B']
                m_reel = int(res['Victoires A'] + res['Victoires B'])
                if choix == str(v_reel).strip():
                    pts_serie += 2
                    if int(pred['#Match']) == m_reel:
                        pts_serie += bonus_matchs_dict.get(m_reel, 0)
                elif str(pred['#Match']) == "7" and m_reel == 7:
                    pts_serie += 1
            if pts_serie > 0: statut = "✅"
            total_points += pts_serie

        liste_details.append({"Statut": statut, "Série": serie, "Choix": choix, "Points": int(pts_serie)})
    return int(total_points), liste_details

# --- AFFICHAGE ---
if 'Nom' in df_part.columns:
    participants = df_part['Nom'].dropna().unique()
    scores_finaux = []
    tous_details = {}

    for nom in participants:
        pts, details = calculer_tout(nom)
        scores_finaux.append({"Participant": nom, "Points": pts})
        tous_details[nom] = details

    # 1. CLASSEMENT
    df_rank = pd.DataFrame(scores_finaux).sort_values("Points", ascending=False)
    df_rank.insert(0, "Rang", range(1, len(df_rank) + 1))
    st.markdown('<div class="sub-title">📊 Classement Général</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2: st.markdown(f'<div class="classement-container">{df_rank.to_html(index=False)}</div>', unsafe_allow_html=True)

    st.write("---")

    # 2. ANALYSE DES POINTS
    with st.expander("🔍 Pourquoi ce score ? (Détails par série)"):
        for nom in participants:
            st.subheader(f"Joueur : {nom}")
            st.write(pd.DataFrame(tous_details[nom]).to_html(index=False, escape=False), unsafe_allow_html=True)
            st.write("<br>", unsafe_allow_html=True)

    # 3. SÉLECTIONS (CHAMPION & MVP)
    with st.expander("📋 Voir les sélections de chaque participant"):
        all_cols_part = df_part.columns.tolist()
        col_champ = next((c for c in all_cols_part if any(x in c.upper() for x in ["STANLEY", "CUP", "COUPE", "CHAMP"])), None)
        col_mvp = next((c for c in all_cols_part if "MVP" in c.upper()), None)

        for nom in participants:
            st.markdown(f"### Prédictions de **{nom}**")
            user_row = df_part[df_part['Nom'].astype(str).str.strip() == str(nom).strip()]
            if not user_row.empty:
                ca, cb = st.columns(2)
                if col_champ:
                    val = user_row[col_champ].iloc[0]
                    ca.markdown(f'<div class="bonus-card"><span class="bonus-icon">🏆</span><div><span class="bonus-label">Champion Choisi</span><span class="bonus-value">{val}</span></div></div>', unsafe_allow_html=True)
                if col_mvp:
                    val = user_row[col_mvp].iloc[0]
                    cb.markdown(f'<div class="bonus-card"><span class="bonus-icon">🎖️</span><div><span class="bonus-label">MVP Choisi</span><span class="bonus-value">{val}</span></div></div>', unsafe_allow_html=True)
            
            p_preds = df_pred[df_pred['Nom'].astype(str).str.strip() == str(nom).strip()]
            match_data = p_preds[p_preds['Série/Équipes'].notna()]
            if not match_data.empty:
                cols_to_show = [c for c in ['Ronde', 'Série/Équipes', 'Team Win', '#Match'] if c in match_data.columns]
                st.write(match_data[cols_to_show].to_html(index=False), unsafe_allow_html=True)
            st.write("<hr>", unsafe_allow_html=True)

    # 4. RÈGLEMENT COMPLET
    with st.expander("📜 Règlement officiel - Pool de Hockey 2026"):
        st.markdown("""
        <div class="rules-section">
            <h4>1. Structure du Pool</h4>
            <ul>
                <li><b>Nombre de participants :</b> 3 au départ (avec possibilité d'expansion).</li>
                <li><b>Format :</b> Éliminatoire (1/8, 1/4, 1/2 et Finale).</li>
                <li><b>Prise de décision :</b>
                    <ul>
                        <li><b>Choix Initiaux (Fixes) :</b> Gagnant de la Coupe Stanley et Joueur MVP (Conn Smythe).</li>
                        <li><b>Choix par Ronde :</b> Avant chaque ronde, prédiction du vainqueur de chaque série et du nombre de matchs (4 à 7).</li>
                    </ul>
                </li>
            </ul>
        </div>
        
        <div class="rules-section">
            <h4>2. Système de Pointage des Matchs</h4>
            <p>Le nombre de points accordés pour chaque victoire de l'équipe sélectionnée augmente à chaque ronde :</p>
            <table class="rules-table">
                <tr><th>Ronde</th><th>Points / Victoire</th><th>Bonus Gagnant Série</th></tr>
                <tr><td>1/8 de finale</td><td>1 pt</td><td>+2 pts</td></tr>
                <tr><td>1/4 de finale</td><td>2 pts</td><td>+2 pts</td></tr>
                <tr><td>1/2 finale</td><td>3 pts</td><td>+2 pts</td></tr>
                <tr><td>Finale</td><td>4 pts</td><td>+2 pts</td></tr>
            </table>
        </div>

        <div class="rules-section">
            <h4>3. Bonus de Précision (Nombre de matchs)</h4>
            <p>Si tu prédis le bon nombre de matchs ET que ton équipe gagne :</p>
            <ul>
                <li><b>En 4 matchs :</b> +4 pts bonis</li>
                <li><b>En 5 matchs :</b> +3 pts bonis</li>
                <li><b>En 6 matchs :</b> +2 pts bonis</li>
                <li><b>En 7 matchs :</b> +1 pt boni</li>
            </ul>
            <p><i><b>L'exception "Match 7" :</b> Tu reçois le 1 pt boni si la série se rend en 7 matchs, même si l'équipe que tu avais choisie finit par perdre la série.</i></p>
        </div>

        <div class="rules-section">
            <h4>4. Bonus de Performance Globale</h4>
            <ul>
                <li><b>Parcours de ton Champion (max 10 pts) :</b>
                    <ul>
                        <li>Passe la ronde 1 : +2 pts</li>
                        <li>Passe la ronde 2 : +2 pts</li>
                        <li>Passe la ronde 3 : +2 pts</li>
                        <li>Remporte la finale : +4 pts</li>
                    </ul>
                </li>
                <li><b>Trophée MVP :</b> +10 pts si ton choix initial remporte le titre de joueur le plus utile des séries.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
