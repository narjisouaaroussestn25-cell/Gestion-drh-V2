import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import os

st.set_page_config(page_title="Suivi DRH", page_icon="📊", layout="wide")

# ====== الاتصال بقاعدة البيانات SQLite ======
# هاد الكود كيقلب على ملف drh_supply.db في نفس المجلد
def get_conn():
    return sqlite3.connect("drh_supply.db")

# ====== التصميم (CSS) ======
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    h1 { color: #FFFFFF!important; border-bottom: 3px solid #C8A25A; padding-bottom: 10px; }
    div[data-testid="stMetricValue"] { color: #FFFFFF!important; font-size: 24px!important; }
    .stButton>button { background-color: #C8A25A; color: #0E1117; font-weight: 700; border-radius: 8px; }
    </style>
    """, unsafe_html=True)

# ====== الدوال الأساسية (معدلة لـ SQLite) ======
@st.cache_data
def get_kpi_data():
    conn = get_conn()
    nb_articles = pd.read_sql("SELECT COUNT(*) FROM prestations", conn).iloc[0,0]
    entree_total = pd.read_sql("SELECT COALESCE(SUM(quantite), 0) FROM details_demande WHERE type_mouvement = 'Entrée'", conn).iloc[0,0]
    sortie_total = pd.read_sql("SELECT COALESCE(SUM(quantite), 0) FROM details_demande WHERE type_mouvement = 'Sortie'", conn).iloc[0,0]
    conn.close()
    return nb_articles, entree_total, sortie_total

# ====== الواجهة ======
st.title("📊 Application de Suivi DRH")
nb_art, entree, sortie = get_kpi_data()

col1, col2, col3 = st.columns(3)
col1.metric("Articles", nb_art)
col2.metric("Total Entrées", entree)
col3.metric("Total Sorties", sortie)

st.info("تم تحديث الكود للعمل بنظام SQLite. تأكدي من رفع ملف drh_supply.db مع الكود في GitHub.")²    
