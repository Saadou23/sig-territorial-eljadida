# ============================================================================
# ⚠️ PROTECTION AUTHENTIFICATION
# ============================================================================
import streamlit as st
if 'user_profile' not in st.session_state or not st.session_state.user_profile:
    st.error("🔒 Accès Refusé")
    st.warning("Vous devez vous connecter pour accéder à cette page.")
    st.info("Retournez à la page d'accueil pour vous connecter.")
    st.stop()
profile = st.session_state.user_profile
# ============================================================================

import pandas as pd
import plotly.express as px
from supabase import create_client, Client

st.set_page_config(page_title="Communes", page_icon="🏘️", layout="wide")

@st.cache_resource
def init_supabase():
    SUPABASE_URL = "https://kvmitmgsczlwzhkccvqz.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt2bWl0bWdzY3psd3poa2NjdnF6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA2NjUyMDIsImV4cCI6MjA4NjI0MTIwMn0.xvKizf9RlSv8wxonHAlPw5_hsh3bKSDlFLyOwtI7kxg"
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

st.title("🏘️ Communes de la Province d'El Jadida")

@st.cache_data(ttl=600)
def load_data():
    communes = supabase.table('communes').select('*').execute()
    projets = supabase.table('projets_sante').select('commune_id, budget_estime').execute()
    return communes.data, projets.data

communes, projets = load_data()

if not communes:
    st.warning("Aucune commune trouvée")
    st.stop()

df = pd.DataFrame(communes)

# Stats projets
df_projets = pd.DataFrame(projets)
if not df_projets.empty:
    stats = df_projets.groupby('commune_id').agg({'budget_estime': ['count', 'sum']}).reset_index()
    stats.columns = ['id', 'nb_projets', 'budget_total']
    df = df.merge(stats, on='id', how='left')
    df['nb_projets'] = df['nb_projets'].fillna(0).astype(int)
    df['budget_mdh'] = df['budget_total'].fillna(0) / 1_000_000
else:
    df['nb_projets'] = 0
    df['budget_mdh'] = 0.0

# KPI
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🏘️ Total Communes", len(df))
with col2:
    st.metric("🏙️ Urbaines", len(df[df['milieu'] == 'Urbain']))
with col3:
    st.metric("🌾 Rurales", len(df[df['milieu'] == 'Rural']))
with col4:
    st.metric("💰 Budget Total", f"{df['budget_mdh'].sum():,.0f} MDH")

st.divider()

# Filtres
col1, col2 = st.columns(2)
with col1:
    milieu_filter = st.selectbox("Type", ["Tous", "Urbain", "Rural"])
with col2:
    search = st.text_input("🔍 Rechercher", placeholder="Nom de commune...")

df_filtered = df.copy()
if milieu_filter != "Tous":
    df_filtered = df_filtered[df_filtered['milieu'] == milieu_filter]
if search:
    df_filtered = df_filtered[df_filtered['nom'].str.contains(search, case=False, na=False)]

st.info(f"📊 {len(df_filtered)} commune(s)")

# Graphique
st.subheader("📈 Top 10 Communes par Budget")
df_top = df_filtered.nlargest(10, 'budget_mdh')
fig = px.bar(df_top, x='nom', y='budget_mdh', color='nb_projets', title="Budget par Commune")
st.plotly_chart(fig, use_container_width=True)

# Liste
st.divider()
st.subheader("📋 Liste des Communes")
df_display = df_filtered[['nom', 'milieu', 'nb_projets', 'budget_mdh']].copy()
df_display.columns = ['Commune', 'Type', 'Projets', 'Budget (MDH)']
st.dataframe(df_display.sort_values('Budget (MDH)', ascending=False), use_container_width=True, hide_index=True)

csv = df_filtered.to_csv(index=False).encode('utf-8')
st.download_button("📥 Exporter CSV", csv, "communes.csv", "text/csv")
