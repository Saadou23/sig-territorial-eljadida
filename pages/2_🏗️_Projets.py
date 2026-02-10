"""
PAGE PROJETS - Version simplifiee testee
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

st.set_page_config(page_title="Projets", page_icon="🏗️", layout="wide")

# Supabase
@st.cache_resource
def init_supabase():
    SUPABASE_URL = "https://kvmitmgsczlwzhkccvqz.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt2bWl0bWdzY3psd3poa2NjdnF6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA2NjUyMDIsImV4cCI6MjA4NjI0MTIwMn0.xvKizf9RlSv8wxonHAlPw5_hsh3bKSDlFLyOwtI7kxg"
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

st.title("🏗️ Projets de Mise à Niveau Territoriale")

# Charger les données
try:
    projets_response = supabase.table('projets_sante').select('*').execute()
    projets = projets_response.data
    
    communes_response = supabase.table('communes').select('*').execute()
    communes = {c['id']: c['nom'] for c in communes_response.data}
    
    if not projets:
        st.warning("⚠️ Aucun projet trouvé")
        st.info("Veuillez importer les projets via le script SQL 06_import_projets_CORRIGES.sql")
        st.stop()
    
    df = pd.DataFrame(projets)
    df['commune_nom'] = df['commune_id'].map(communes)
    df['budget_mdh'] = df['budget_estime'].fillna(0) / 1000000
    
    # KPI
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🏗️ Total Projets", len(df))
    
    with col2:
        budget_total = df['budget_mdh'].sum()
        st.metric("💰 Budget Total", f"{budget_total:,.0f} MDH")
    
    with col3:
        budget_moyen = df['budget_mdh'].mean()
        st.metric("📊 Budget Moyen", f"{budget_moyen:,.1f} MDH")
    
    with col4:
        nb_communes = df['commune_id'].nunique()
        st.metric("🏘️ Communes", f"{nb_communes}/{len(communes)}")
    
    st.divider()
    
    # Filtres
    st.subheader("🔍 Filtres")
    
    col1, col2 = st.columns(2)
    
    with col1:
        communes_filter = st.multiselect(
            "Communes",
            options=sorted([nom for nom in df['commune_nom'].dropna().unique() if nom])
        )
    
    with col2:
        types_filter = st.multiselect(
            "Types de projet",
            options=sorted([t for t in df['type_projet'].dropna().unique() if t])
        )
    
    # Appliquer filtres
    df_filtered = df.copy()
    
    if communes_filter:
        df_filtered = df_filtered[df_filtered['commune_nom'].isin(communes_filter)]
    
    if types_filter:
        df_filtered = df_filtered[df_filtered['type_projet'].isin(types_filter)]
    
    st.info(f"📊 {len(df_filtered)} projet(s) | Budget : {df_filtered['budget_mdh'].sum():,.2f} MDH")
    
    # Graphiques
    st.divider()
    st.subheader("📈 Analyses")
    
    tab1, tab2 = st.tabs(["Par Commune", "Par Type"])
    
    with tab1:
        if len(df_filtered) > 0:
            df_by_commune = df_filtered.groupby('commune_nom').agg({
                'id': 'count',
                'budget_mdh': 'sum'
            }).reset_index()
            df_by_commune.columns = ['Commune', 'Nb Projets', 'Budget (MDH)']
            df_by_commune = df_by_commune.sort_values('Budget (MDH)', ascending=False).head(10)
            
            fig = px.bar(
                df_by_commune,
                x='Commune',
                y='Budget (MDH)',
                color='Nb Projets',
                title="Top 10 Communes par Budget"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        if len(df_filtered) > 0:
            df_by_type = df_filtered.groupby('type_projet').agg({
                'id': 'count',
                'budget_mdh': 'sum'
            }).reset_index()
            df_by_type.columns = ['Type', 'Nb Projets', 'Budget (MDH)']
            
            fig = px.pie(
                df_by_type,
                values='Nb Projets',
                names='Type',
                title="Répartition par Type"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Liste
    st.divider()
    st.subheader("📋 Liste des Projets")
    
    if len(df_filtered) > 0:
        df_display = df_filtered[['intitule', 'commune_nom', 'type_projet', 'budget_mdh']].copy()
        df_display.columns = ['Intitulé', 'Commune', 'Type', 'Budget (MDH)']
        df_display = df_display.sort_values('Budget (MDH)', ascending=False)
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Export
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Exporter CSV",
            csv,
            "projets.csv",
            "text/csv"
        )

except Exception as e:
    st.error(f"❌ Erreur : {str(e)}")
    st.exception(e)
