import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF

st.set_page_config(page_title="Suivi DRH", page_icon="📊", layout="wide")

# ====== CSS التصميم ======
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Cairo', sans-serif; color: #FFFFFF; }
    .stApp { background-color: #2b2b2b; }
    h1 { color: #FFB347!important; border-bottom: 3px solid #FFB347; padding-bottom: 10px; }
    h2, h3, h4 { color: #FFB347!important; }
    div[data-testid="stTabs"] button[aria-selected="true"] { color: #FFB347!important; border-bottom: 3px solid #FFB347!important; font-weight: 700; }
    div[data-testid="stTabs"] button { color: #CCCCCC; font-size: 16px; }
    div[data-testid="stMetricContainer"] { background-color: #1E1E1E; border-left: 5px solid #FFB347; border-radius: 8px; padding: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    div[data-testid="stMetricLabel"] { color: #CCCCCC!important; font-weight: 600; }
    div[data-testid="stMetricValue"] { color: #FFFFFF!important; font-size: 28px!important; }
    .stButton>button { background-color: #FFB347; color: #0E1117; border-radius: 8px; border: none; font-weight: 700; }
    [data-testid="stSidebar"] { background-color: #1A1A1A; }
    [data-testid="stSidebar"] * { color: white!important; }
    </style>
    """, unsafe_allow_html=True)

# ====== الاتصال بـ SQLite ======
def get_conn():
    return sqlite3.connect("drh_supply.db")

@st.cache_data
def get_kpi_data():
    conn = get_conn()
    today = datetime.now().strftime('%Y-%m-%d')
    # ملاحظة: في SQLite نستخدم strftime أو date()
    nb_articles = pd.read_sql("SELECT COUNT(*) as total FROM prestations", conn).iloc[0,0]
    nb_mouvements = pd.read_sql("SELECT COUNT(*) as total FROM details_demande", conn).iloc[0,0]
    
    top_sortie = pd.read_sql("""
        SELECT p.designation, SUM(dt.quantite) as Total_Sortie
        FROM details_demande dt JOIN prestations p ON dt.id_prestation = p.id_prestation
        WHERE dt.type_mouvement = 'Sortie' GROUP BY p.designation ORDER BY Total_Sortie DESC LIMIT 5
    """, conn)
    
    stock_df = pd.read_sql("""
        SELECT p.designation, 
        COALESCE(SUM(CASE WHEN dt.type_mouvement = 'Entrée' THEN dt.quantite ELSE 0 END), 0) -
        COALESCE(SUM(CASE WHEN dt.type_mouvement = 'Sortie' THEN dt.quantite ELSE 0 END), 0) AS Stock
        FROM prestations p LEFT JOIN details_demande dt ON p.id_prestation = dt.id_prestation GROUP BY p.id_prestation
    """, conn)
    
    entree_total = pd.read_sql("SELECT COALESCE(SUM(quantite), 0) FROM details_demande WHERE type_mouvement = 'Entrée'", conn).iloc[0,0]
    sortie_total = pd.read_sql("SELECT COALESCE(SUM(quantite), 0) FROM details_demande WHERE type_mouvement = 'Sortie'", conn).iloc[0,0]
    
    conn.close()
    return nb_articles, nb_mouvements, top_sortie, stock_df.fillna(0), entree_total, sortie_total, 24

# ====== بقية الكود ======
st.title("📊 Application de Suivi des Demandes de Fournitures - DRH")
st.markdown("---")

tab0, tab1, tab2, tab3, tab4 = st.tabs(["📊 Tableau de Bord", "📋 Historique Général", "➕ Nouvelle Mouvement", "📦 Stock Détail", "🔍 Par Article"])

with tab0:
    st.subheader("📊 Vue d'ensemble")
    nb_art, nb_mvt, top5, stock_df, entree_total, sortie_total, rupture = get_kpi_data()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("📥 Total Entrées", f"{entree_total}")
    col2.metric("📤 Total Sorties", f"{sortie_total}")
    col3.metric("📉 Rupture", f"{rupture}")

    st.write("#### 🔥 Top 5 Articles")
    if not top5.empty: st.bar_chart(top5, x='designation', y='Total_Sortie')

# ملاحظة: تأكدي من تحديث ملف requirements.txt ليتضمن فقط: streamlit, pandas, fpdf
