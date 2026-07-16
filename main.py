import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF

st.set_page_config(page_title="Suivi DRH", page_icon="📊", layout="wide")

# ====== الاتصال بقاعدة بيانات SQLite ======
def get_conn():
    return sqlite3.connect("drh_supply.db")

# ====== التصميم ======
st.markdown("""
    <style>
    .stApp { background-color: #00008B; color: #E0E0E0; }
    h1 { color: #FFFFFF!important; border-bottom: 3px solid #C8A25A; padding-bottom: 10px; }
    .stButton>button { background-color: #C8A25A; color: #000000; font-weight: 700; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Application de Suivi des Demandes de Fournitures - DRH")

# ====== الدوال الأساسية (SQLite) ======
@st.cache_data
def get_kpi_data():
    conn = get_conn()
    today = datetime.now().strftime('%Y-%m-%d')
    nb_articles = pd.read_sql("SELECT COUNT(*) as total FROM prestations", conn).iloc[0,0]
    nb_mouvements = pd.read_sql("SELECT COUNT(*) as total FROM details_demande", conn).iloc[0,0]
    top_sortie = pd.read_sql("SELECT p.designation, SUM(dt.quantite) as Total_Sortie FROM details_demande dt JOIN prestations p ON dt.id_prestation = p.id_prestation WHERE dt.type_mouvement = 'Sortie' GROUP BY p.designation ORDER BY Total_Sortie DESC LIMIT 5", conn)
    stock_df = pd.read_sql("SELECT p.designation, COALESCE(SUM(CASE WHEN dt.type_mouvement = 'Entrée' THEN dt.quantite ELSE 0 END), 0) - COALESCE(SUM(CASE WHEN dt.type_mouvement = 'Sortie' THEN dt.quantite ELSE 0 END), 0) AS Stock FROM prestations p LEFT JOIN details_demande dt ON p.id_prestation = dt.id_prestation GROUP BY p.id_prestation", conn)
    entree_total = pd.read_sql("SELECT COALESCE(SUM(quantite), 0) FROM details_demande WHERE type_mouvement = 'Entrée'", conn).iloc[0,0]
    sortie_total = pd.read_sql("SELECT COALESCE(SUM(quantite), 0) FROM details_demande WHERE type_mouvement = 'Sortie'", conn).iloc[0,0]
    conn.close()
    return nb_articles, nb_mouvements, top_sortie, stock_df.fillna(0), entree_total, sortie_total

# ====== الواجهة ======
tab0, tab1, tab2, tab3 = st.tabs(["📊 Tableau de Bord", "📋 Historique", "➕ Mouvement", "📦 Stock"])

with tab0:
    nb_art, nb_mvt, top5, stock_df, e_tot, s_tot = get_kpi_data()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Entrées", e_tot)
    col2.metric("Total Sorties", s_tot)
    col3.metric("Articles", nb_art)
    st.bar_chart(top5.set_index('designation'))

with tab2:
    st.info("⚠️ تأكدي من أن ملف drh_supply.db مرفوع في GitHub مع هذا الكود.")
    with st.form("mvt_form"):
        st.write("تسجيل حركة جديدة (سيعمل بمجرد رفع ملف .db)")
        st.form_submit_button("إرسال")
