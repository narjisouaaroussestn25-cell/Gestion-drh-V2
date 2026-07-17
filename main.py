import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF

st.set_page_config(page_title="Suivi DRH", page_icon="📊", layout="wide")

# ====== التصميم (نفسه بدون تغيير) ======
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
    .stButton>button { background-color: #FFB347; color: #0E1117; border-radius: 8px; font-weight: 700; }
    [data-testid="stSidebar"] { background-color: #1A1A1A; }
    [data-testid="stDataFrame"] { background-color: #1E1E1E; }
    </style>
    """, unsafe_allow_html=True)

def get_conn():
    return sqlite3.connect("drh_supply.db")

@st.cache_data
def get_kpi_data():
    conn = get_conn()
    today = datetime.now().date().strftime('%Y-%m-%d')
    # جلب البيانات
    nb_articles = pd.read_sql("SELECT COUNT(*) as total FROM prestations", conn).iloc[0,0]
    entree_total = pd.read_sql("SELECT COALESCE(SUM(quantite), 0) as total FROM details_demande WHERE type_mouvement = 'Entrée'", conn).iloc[0,0]
    sortie_total = pd.read_sql("SELECT COALESCE(SUM(quantite), 0) as total FROM details_demande WHERE type_mouvement = 'Sortie'", conn).iloc[0,0]
    # تم تثبيت الرقم 24 كما طلبتِ ليظهر في الـ Rupture
    rupture_count = 24 
    conn.close()
    return nb_articles, entree_total, sortie_total, rupture_count

# ====== بقية الوظائف (تم تحويل استعلامات MySQL إلى SQLite) ======
def get_prestations_all():
    conn = get_conn()
    df = pd.read_sql("SELECT id_prestation, designation FROM prestations ORDER BY designation", conn)
    conn.close()
    return df

# ... (باقي الوظائف من كودك الأصلي مع استبدال %s بـ ? لـ SQLite)

# ====== الواجهة الرئيسية ======
st.title("📊 Application de Suivi des Demandes de Fournitures - DRH")

with st.sidebar:
    st.markdown("### ⚠️ Zone Dangereuse")
    if st.button("🚨 Réinitialiser la base"): 
        st.warning("تم الحذف.") # أضيفي منطق الحذف هنا حسب احتياجك

st.markdown("---")
tab0, tab1, tab2, tab3, tab4 = st.tabs(["📊 Tableau de Bord", "📋 Historique Général", "➕ Nouvelle Mouvement", "📦 Stock Détail", "🔍 Par Article"])

with tab0:
    st.subheader("📊 Vue d'ensemble")
    nb_art, ent_t, sor_t, rupt = get_kpi_data()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📥 Total Entrées", f"{ent_t}")
    col2.metric("📤 Total Sorties", f"{sor_t}")
    col3.metric("📉 Rupture", f"{rupt}") # سيظهر هنا الرقم 24
    col4.metric("📦 Articles", f"{nb_art}")
