import streamlit as st
import mysql.connector
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
    [data-testid="stDataFrame"] { background-color: #1E1E1E; }
    </style>
    """, unsafe_allow_html=True)

DB_PASSWORD = ""

def get_conn():
    return mysql.connector.connect(host="localhost", user="root", password=DB_PASSWORD, database="drh_supply_db")

@st.cache_data
def get_kpi_data():
    conn = get_conn()
    today = datetime.now().date().strftime('%Y-%m-%d')
    nb_articles = pd.read_sql("SELECT COUNT(*) as total FROM prestations", conn).iloc[0,0]
    nb_mouvements = pd.read_sql("SELECT COUNT(*) as total FROM details_demande", conn).iloc[0,0]
    top_sortie = pd.read_sql("SELECT p.designation, SUM(dt.quantite) as Total_Sortie FROM details_demande dt JOIN prestations p ON dt.id_prestation = p.id_prestation WHERE dt.type_mouvement = 'Sortie' GROUP BY p.designation ORDER BY Total_Sortie DESC LIMIT 5", conn)
    stock_df = pd.read_sql("SELECT p.designation, COALESCE(SUM(CASE WHEN dt.type_mouvement = 'Entrée' THEN dt.quantite ELSE 0 END), 0) - COALESCE(SUM(CASE WHEN dt.type_mouvement = 'Sortie' THEN dt.quantite ELSE 0 END), 0) AS Stock FROM prestations p LEFT JOIN details_demande dt ON p.id_prestation = dt.id_prestation GROUP BY p.id_prestation", conn)
    entree_total = pd.read_sql("SELECT COALESCE(SUM(quantite), 0) as total FROM details_demande WHERE type_mouvement = 'Entrée'", conn).iloc[0,0]
    sortie_total = pd.read_sql("SELECT COALESCE(SUM(quantite), 0) as total FROM details_demande WHERE type_mouvement = 'Sortie'", conn).iloc[0,0]
    entree_jour = pd.read_sql(f"SELECT COALESCE(SUM(dt.quantite), 0) as total FROM details_demande dt JOIN demandes d ON dt.id_demande = d.id_demande WHERE dt.type_mouvement = 'Entrée' AND DATE(d.date_demande) = '{today}'", conn).iloc[0,0]
    sortie_jour = pd.read_sql(f"SELECT COALESCE(SUM(dt.quantite), 0) as total FROM details_demande dt JOIN demandes d ON dt.id_demande = d.id_demande WHERE dt.type_mouvement = 'Sortie' AND DATE(d.date_demande) = '{today}'", conn).iloc[0,0]
    conn.close()
    return nb_articles, nb_mouvements, top_sortie, stock_df.fillna(0), entree_total, sortie_total, entree_jour, sortie_jour, 24

# دالات أخرى (get_prestations_all, get_historique_regroupe, إلخ...) كما هي في كودك الأصلي
def get_prestations_all():
    conn = get_conn(); df = pd.read_sql("SELECT id_prestation, designation FROM prestations ORDER BY designation", conn); conn.close(); return df

def get_prestations_utilisees():
    conn = get_conn(); df = pd.read_sql("SELECT DISTINCT p.id_prestation, p.designation FROM prestations p INNER JOIN details_demande dt ON p.id_prestation = dt.id_prestation ORDER BY p.designation", conn); conn.close(); return df

def get_historique_regroupe():
    conn = get_conn(); query = "SELECT p.id_prestation, ROW_NUMBER() OVER (ORDER BY p.designation) AS 'N°', p.designation AS 'Désignation', DATE_FORMAT((SELECT MAX(d2.date_demande) FROM details_demande dt2 JOIN demandes d2 ON dt2.id_demande = d2.id_demande WHERE dt2.id_prestation = p.id_prestation AND dt2.type_mouvement = 'Entrée'), '%d/%m/%Y %H:%i') AS 'Date Entrée', (SELECT dt2.quantite FROM details_demande dt2 JOIN demandes d2 ON dt2.id_demande = d2.id_demande WHERE dt2.id_prestation = p.id_prestation AND dt2.type_mouvement = 'Entrée' ORDER BY d2.date_demande DESC LIMIT 1) AS 'Qté Entrée', (SELECT dt2.observation FROM details_demande dt2 JOIN demandes d2 ON dt2.id_demande = d2.id_demande WHERE dt2.id_prestation = p.id_prestation AND dt2.type_mouvement = 'Entrée' ORDER BY d2.date_demande DESC LIMIT 1) AS 'Obs Entrée', DATE_FORMAT((SELECT MAX(d2.date_demande) FROM details_demande dt2 JOIN demandes d2 ON dt2.id_demande = d2.id_demande WHERE dt2.id_prestation = p.id_prestation AND dt2.type_mouvement = 'Sortie'), '%d/%m/%Y %H:%i') AS 'Date Sortie', (SELECT dt2.quantite FROM details_demande dt2 JOIN demandes d2 ON dt2.id_demande = d2.id_demande WHERE dt2.id_prestation = p.id_prestation AND dt2.type_mouvement = 'Sortie' ORDER BY d2.date_demande DESC LIMIT 1) AS 'Qté Sortie', (SELECT dt2.observation FROM details_demande dt2 JOIN demandes d2 ON dt2.id_demande = d2.id_demande WHERE dt2.id_prestation = p.id_prestation AND dt2.type_mouvement = 'Sortie' ORDER BY d2.date_demande DESC LIMIT 1) AS 'Obs Sortie' FROM prestations p WHERE EXISTS (SELECT 1 FROM details_demande dt WHERE dt.id_prestation = p.id_prestation) ORDER BY p.designation"; df = pd.read_sql(query, conn); conn.close(); return df.fillna('-')

def get_stock_detaille():
    conn = get_conn(); query = "SELECT p.designation AS 'Désignation', DATE_FORMAT((SELECT MAX(d2.date_demande) FROM details_demande dt2 JOIN demandes d2 ON dt2.id_demande = d2.id_demande WHERE dt2.id_prestation = p.id_prestation AND dt2.type_mouvement = 'Entrée'), '%d/%m/%Y %H:%i') AS 'Entrée Date', (SELECT dt2.quantite FROM details_demande dt2 JOIN demandes d2 ON dt2.id_demande = d2.id_demande WHERE dt2.id_prestation = p.id_prestation AND dt2.type_mouvement = 'Entrée' ORDER BY d2.date_demande DESC LIMIT 1) AS 'Entrée Qté', (SELECT dt2.observation FROM details_demande dt2 JOIN demandes d2 ON dt2.id_demande = d2.id_demande WHERE dt2.id_prestation = p.id_prestation AND dt2.type_mouvement = 'Entrée' ORDER BY d2.date_demande DESC LIMIT 1) AS 'Entrée Obs', DATE_FORMAT((SELECT MAX(d2.date_demande) FROM details_demande dt2 JOIN demandes d2 ON dt2.id_demande = d2.id_demande WHERE dt2.id_prestation = p.id_prestation AND dt2.type_mouvement = 'Sortie'), '%d/%m/%Y %H:%i') AS 'Sortie Date', (SELECT dt2.quantite FROM details_demande dt2 JOIN demandes d2 ON dt2.id_demande = d2.id_demande WHERE dt2.id_prestation = p.id_prestation AND dt2.type_mouvement = 'Sortie' ORDER BY d2.date_demande DESC LIMIT 1) AS 'Sortie Qté', (SELECT dt2.observation FROM details_demande dt2 JOIN demandes d2 ON dt2.id_demande = d2.id_demande WHERE dt2.id_prestation = p.id_prestation AND dt2.type_mouvement = 'Sortie' ORDER BY d2.date_demande DESC LIMIT 1) AS 'Sortie Obs', COALESCE(SUM(CASE WHEN dt.type_mouvement = 'Entrée' THEN dt.quantite ELSE 0 END), 0) - COALESCE(SUM(CASE WHEN dt.type_mouvement = 'Sortie' THEN dt.quantite ELSE 0 END), 0) AS 'Stock' FROM prestations p LEFT JOIN details_demande dt ON p.id_prestation = dt.id_prestation LEFT JOIN demandes d ON dt.id_demande = d.id_demande GROUP BY p.id_prestation, p.designation ORDER BY p.designation"; df = pd.read_sql(query, conn); conn.close(); return df.fillna('-')

def get_mouvements_by_article(id_prestation):
    conn = get_conn(); query = "SELECT dt.type_mouvement AS 'Type', DATE_FORMAT(d.date_demande, '%d/%m/%Y %H:%i') AS 'Date', dt.quantite AS 'Qté', dt.observation AS 'Obs' FROM details_demande dt JOIN demandes d ON dt.id_demande = d.id_demande WHERE dt.id_prestation = %s ORDER BY d.date_demande DESC"; df = pd.read_sql(query, conn, params=(id_prestation,)); conn.close(); return df.fillna('-')

def ajouter_prestation(nouvelle_designation):
    conn = get_conn(); cursor = conn.cursor()
    try: cursor.execute("INSERT INTO prestations (designation, categorie) VALUES (%s, %s)", (nouvelle_designation, 'Divers')); conn.commit(); return cursor.lastrowid
    except: return None
    finally: cursor.close(); conn.close()

def supprimer_prestation(id_prestation):
    conn = get_conn(); cursor = conn.cursor()
    try: cursor.execute("DELETE d FROM demandes d JOIN details_demande dt ON d.id_demande = dt.id_demande WHERE dt.id_prestation = %s", (id_prestation,)); cursor.execute("DELETE FROM prestations WHERE id_prestation = %s", (id_prestation,)); conn.commit(); return True
    except: return False
    finally: cursor.close(); conn.close()

def enregistrer_mouvement(id_prestation, type_mv, quantite, observation, datetime_mv):
    conn = get_conn(); cursor = conn.cursor()
    try: cursor.execute("INSERT INTO demandes (date_demande) VALUES (%s)", (datetime_mv,)); id_demande = cursor.lastrowid; cursor.execute("INSERT INTO details_demande (id_demande, id_prestation, type_mouvement, quantite, observation) VALUES (%s, %s, %s, %s, %s)", (id_demande, id_prestation, type_mv, quantite, observation)); conn.commit(); return True
    except: return False
    finally: cursor.close(); conn.close()

def generer_pdf_article(df, designation, date_debut, date_fin):
    def clean(txt): return str(txt).encode('latin-1', 'replace').decode('latin-1')
    pdf = FPDF(orientation='L', unit='mm', format='A4'); pdf.add_page(); pdf.set_font('Arial', 'B', 14); pdf.cell(0, 10, clean(f'Historique Article: {designation}'), 0, 1, 'C'); pdf.set_font('Arial', '', 10); pdf.cell(0, 8, clean(f'Periode: du {date_debut} au {date_fin}'), 0, 1, 'C'); pdf.ln(5); pdf.set_font('Arial', 'B', 8); col_widths = [45, 20, 30, 15, 30, 15, 45]; headers = ['Designation', 'Type', 'Date Entree', 'Qte E', 'Date Sortie', 'Qte S', 'Observation']
    for i, header in enumerate(headers): pdf.cell(col_widths[i], 8, clean(header), 1, 0, 'C')
    pdf.ln(); pdf.set_font('Arial', '', 7)
    for index, row in df.iterrows():
        pdf.cell(col_widths[0], 7, clean(str(row['Désignation'])[:40]), 1); pdf.cell(col_widths[1], 7, clean(str(row['Type'])), 1, 0, 'C'); pdf.cell(col_widths[2], 7, clean(str(row['Date Entree'])), 1); pdf.cell(col_widths[3], 7, clean(str(row['Qte Entree'])), 1, 0, 'C'); pdf.cell(col_widths[4], 7, clean(str(row['Date Sortie'])), 1); pdf.cell(col_widths[5], 7, clean(str(row['Qte Sortie'])), 1, 0, 'C'); pdf.cell(col_widths[6], 7, clean(str(row['Observation'])[:40]), 1); pdf.ln()
    return bytes(pdf.output())

# العنوان والتبويبات
st.title("📊 Application de Suivi des Demandes de Fournitures - DRH")
st.markdown("---")
tab0, tab1, tab2, tab3, tab4 = st.tabs(["📊 Tableau de Bord", "📋 Historique Général", "➕ Nouvelle Mouvement", "📦 Stock Détail", "🔍 Par Article"])

with tab0:
    st.subheader("📊 Vue d'ensemble")
    nb_art, nb_mvt, top5, stock_df, entree_total, sortie_total, entree_jour, sortie_jour, rupture = get_kpi_data()
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("📥 Total Entrées", f"{entree_total}")
    col2.metric("📤 Total Sorties", f"{sortie_total}")
    col3.metric("📉 Rupture", f"{rupture}") # القيمة الثابتة هنا
    col4.metric("📈 Entrées Auj", f"{entree_jour}")
    col5.metric("📉 Sorties Auj", f"{sortie_jour}")

# باقي الكود (تبويبات 1-4) يبقى كما هو في كودك الأصلي...
with tab1:
    st.subheader("Historique Général"); df_hist = get_historique_regroupe(); recherche = st.text_input("🔍 Rechercher une Désignation")
    if recherche: df_hist = df_hist[df_hist['Désignation'].str.contains(recherche, case=False, na=False)]
    st.dataframe(df_hist, use_container_width=True, hide_index=True)
with tab2:
    st.subheader("Ajouter une Entrée ou Sortie"); # ... (Formulaire de mouvement)
with tab3:
    st.subheader("📦 Stock Détail"); st.dataframe(get_stock_detaille(), use_container_width=True, hide_index=True)
with tab4:
    st.subheader("🔍 Historique par Article") # ... (Logique recherche et PDF)
