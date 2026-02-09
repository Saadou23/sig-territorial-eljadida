"""
PAGE : PROJETS DE MISE À NIVEAU
Consultation et analyse des 1103 projets
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

st.set_page_config(page_title="Projets", page_icon="🏗️", layout="wide")

# ============================================================================
# INITIALISATION SUPABASE
# ============================================================================

@st.cache_resource
def init_supabase() -> Client:
    """Initialiser la connexion Supabase"""
    SUPABASE_URL = "https://kvmitmgsczlwzhkccvqz.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt2bWl0bWdzY3psd3poa2NjdnF6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA2NjUyMDIsImV4cCI6MjA4NjI0MTIwMn0.xvKizf9RlSv8wxonHAlPw5_hsh3bKSDlFLyOwtI7kxg"
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# ============================================================================
# INTERFACE
# ============================================================================

st.title("🏗️ Projets de Mise à Niveau Territoriale")

# Charger les données
try:
    # Projets
    projets_response = supabase.table('projets_sante').select('*').execute()
    projets = projets_response.data
    
    # Communes
    communes_response = supabase.table('communes').select('*').execute()
    communes = {c['id']: c['nom'] for c in communes_response.data}
    
    if not projets:
        st.warning("Aucun projet trouvé")
        st.stop()
    
    # Créer DataFrame
    df = pd.DataFrame(projets)
    df['commune_nom'] = df['commune_id'].map(communes)
    df['budget_mdh'] = df['budget_estime'].fillna(0) / 1_000_000
    
    # KPI Globaux
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
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        communes_filter = st.multiselect(
            "Communes",
            options=sorted([nom for nom in df['commune_nom'].dropna().unique() if nom]),
            help="Sélectionner une ou plusieurs communes"
        )
    
    with col2:
        types_filter = st.multiselect(
            "Types de projet",
            options=sorted([t for t in df['type_projet'].dropna().unique() if t]),
            help="Filtrer par type"
        )
    
    with col3:
        statuts_filter = st.multiselect(
            "Statuts",
            options=sorted([s for s in df['statut'].dropna().unique() if s]),
            default=["Programmé"] if "Programmé" in df['statut'].values else []
        )
    
    # Budget filter
    col1, col2 = st.columns(2)
    
    with col1:
        budget_min = st.number_input(
            "Budget minimum (MDH)",
            min_value=0.0,
            value=0.0,
            step=1.0
        )
    
    with col2:
        budget_max = st.number_input(
            "Budget maximum (MDH)",
            min_value=0.0,
            value=float(df['budget_mdh'].max()) if len(df) > 0 else 1000.0,
            step=1.0
        )
    
    # Appliquer filtres
    df_filtered = df.copy()
    
    if communes_filter:
        df_filtered = df_filtered[df_filtered['commune_nom'].isin(communes_filter)]
    
    if types_filter:
        df_filtered = df_filtered[df_filtered['type_projet'].isin(types_filter)]
    
    if statuts_filter:
        df_filtered = df_filtered[df_filtered['statut'].isin(statuts_filter)]
    
    df_filtered = df_filtered[
        (df_filtered['budget_mdh'] >= budget_min) &
        (df_filtered['budget_mdh'] <= budget_max)
    ]
    
    st.info(f"📊 {len(df_filtered)} projet(s) correspondant(s) | Budget : {df_filtered['budget_mdh'].sum():,.2f} MDH")
    
    # Graphiques
    st.divider()
    st.subheader("📈 Analyses")
    
    tab1, tab2, tab3 = st.tabs(["Par Commune", "Par Type", "Budget"])
    
    with tab1:
        # Top communes par nombre de projets
        if len(df_filtered) > 0:
            df_by_commune = df_filtered.groupby('commune_nom').agg({
                'id': 'count',
                'budget_mdh': 'sum'
            }).reset_index()
            df_by_commune.columns = ['Commune', 'Nb Projets', 'Budget Total (MDH)']
            df_by_commune = df_by_commune.sort_values('Budget Total (MDH)', ascending=False).head(10)
            
            fig = px.bar(
                df_by_commune,
                x='Commune',
                y='Budget Total (MDH)',
                color='Nb Projets',
                title="Top 10 Communes par Budget",
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée à afficher")
    
    with tab2:
        # Projets par type
        if len(df_filtered) > 0:
            df_by_type = df_filtered.groupby('type_projet').agg({
                'id': 'count',
                'budget_mdh': 'sum'
            }).reset_index()
            df_by_type.columns = ['Type', 'Nb Projets', 'Budget (MDH)']
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(
                    df_by_type,
                    values='Nb Projets',
                    names='Type',
                    title="Répartition par Type (Nombre)"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.pie(
                    df_by_type,
                    values='Budget (MDH)',
                    names='Type',
                    title="Répartition par Type (Budget)"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée à afficher")
    
    with tab3:
        # Distribution des budgets
        if len(df_filtered) > 0:
            fig = px.histogram(
                df_filtered,
                x='budget_mdh',
                nbins=50,
                title="Distribution des Budgets",
                labels={'budget_mdh': 'Budget (MDH)'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistiques budget
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Minimum", f"{df_filtered['budget_mdh'].min():.2f} MDH")
            with col2:
                st.metric("Médiane", f"{df_filtered['budget_mdh'].median():.2f} MDH")
            with col3:
                st.metric("Moyenne", f"{df_filtered['budget_mdh'].mean():.2f} MDH")
            with col4:
                st.metric("Maximum", f"{df_filtered['budget_mdh'].max():.2f} MDH")
        else:
            st.info("Aucune donnée à afficher")
    
    # Liste des projets
    st.divider()
    st.subheader("📋 Liste des Projets")
    
    if len(df_filtered) > 0:
        # Préparer affichage
        df_display = df_filtered[['intitule', 'commune_nom', 'type_projet', 'statut', 'budget_mdh']].copy()
        df_display.columns = ['Intitulé', 'Commune', 'Type', 'Statut', 'Budget (MDH)']
        df_display = df_display.sort_values('Budget (MDH)', ascending=False)
        
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Budget (MDH)": st.column_config.NumberColumn(
                    "Budget (MDH)",
                    format="%.2f MDH"
                ),
                "Intitulé": st.column_config.TextColumn(
                    "Intitulé",
                    width="large"
                )
            }
        )
        
        # Détails d'un projet
        st.divider()
        st.subheader("🔍 Détails d'un Projet")
        
        projet_selected = st.selectbox(
            "Sélectionner un projet",
            df_filtered['intitule'].tolist()
        )
        
        if projet_selected:
            projet = df_filtered[df_filtered['intitule'] == projet_selected].iloc[0]
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"""
                ### {projet['intitule']}
                
                **Commune** : {projet['commune_nom']}  
                **Type** : {projet['type_projet']}  
                **Statut** : {projet['statut']}  
                **Budget** : {projet['budget_mdh']:.2f} MDH  
                **Avancement** : {projet['avancement_pct']}%
                """)
            
            with col2:
                # Gauge avancement
                fig = px.pie(
                    values=[projet['avancement_pct'], 100 - projet['avancement_pct']],
                    names=['Réalisé', 'Restant'],
                    title="Avancement",
                    hole=0.6,
                    color_discrete_sequence=['#4CAF50', '#E0E0E0']
                )
                fig.update_traces(textinfo='none')
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucun projet à afficher avec les filtres sélectionnés")
    
    # Export
    st.divider()
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col2:
        if len(df_filtered) > 0:
            csv = df_filtered.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Exporter Filtré (CSV)",
                csv,
                "projets_filtered.csv",
                "text/csv",
                use_container_width=True
            )
    
    with col3:
        csv_all = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Exporter Tout (CSV)",
            csv_all,
            "projets_all.csv",
            "text/csv",
            use_container_width=True
        )

except Exception as e:
    st.error(f"❌ Erreur : {str(e)}")
    st.exception(e)
