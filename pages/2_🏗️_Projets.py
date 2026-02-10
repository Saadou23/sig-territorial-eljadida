"""
PAGE PROJETS - Version optimisee avec pagination
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import time

st.set_page_config(page_title="Projets", page_icon="🏗️", layout="wide")

# ============================================================================
# SUPABASE
# ============================================================================

@st.cache_resource
def init_supabase():
    SUPABASE_URL = "https://kvmitmgsczlwzhkccvqz.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt2bWl0bWdzY3psd3poa2NjdnF6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA2NjUyMDIsImV4cCI6MjA4NjI0MTIwMn0.xvKizf9RlSv8wxonHAlPw5_hsh3bKSDlFLyOwtI7kxg"
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# ============================================================================
# FONCTIONS DE CHARGEMENT
# ============================================================================

@st.cache_data(ttl=300)
def load_communes():
    """Charger la liste des communes"""
    try:
        response = supabase.table('communes').select('id, nom').execute()
        return {c['id']: c['nom'] for c in response.data}
    except Exception as e:
        st.error(f"Erreur chargement communes : {str(e)}")
        return {}

@st.cache_data(ttl=300)
def load_projets_summary():
    """Charger un résumé des projets (sans tout charger)"""
    try:
        # Charger seulement les colonnes nécessaires
        response = supabase.table('projets_sante')\
            .select('id, commune_id, intitule, type_projet, statut, budget_estime')\
            .limit(1000)\
            .execute()
        
        return response.data
    except Exception as e:
        st.error(f"Erreur chargement projets : {str(e)}")
        return []

@st.cache_data(ttl=300)
def get_stats():
    """Récupérer les statistiques via une requête agrégée"""
    try:
        # Compter les projets
        response = supabase.table('projets_sante').select('id', count='exact').execute()
        nb_projets = response.count if hasattr(response, 'count') else len(response.data)
        
        # Récupérer tous les projets pour stats (optimisé)
        response = supabase.table('projets_sante')\
            .select('budget_estime, commune_id')\
            .execute()
        
        df = pd.DataFrame(response.data)
        
        budget_total = df['budget_estime'].fillna(0).sum() / 1_000_000
        nb_communes = df['commune_id'].nunique()
        
        return {
            'nb_projets': nb_projets,
            'budget_total': budget_total,
            'nb_communes': nb_communes
        }
    except Exception as e:
        return {
            'nb_projets': 0,
            'budget_total': 0,
            'nb_communes': 0
        }

# ============================================================================
# INTERFACE
# ============================================================================

st.title("🏗️ Projets de Mise à Niveau Territoriale")

# Charger les données
with st.spinner("Chargement des données..."):
    communes = load_communes()
    
    if not communes:
        st.error("❌ Impossible de charger les communes")
        st.stop()
    
    # Charger les stats
    stats = get_stats()
    
    if stats['nb_projets'] == 0:
        st.warning("⚠️ Aucun projet trouvé")
        st.info("Veuillez importer les projets via le script SQL 06_import_projets_CORRIGES.sql")
        st.stop()
    
    # Charger les projets
    projets = load_projets_summary()
    
    if not projets:
        st.error("❌ Erreur lors du chargement des projets")
        st.stop()

# Créer DataFrame
df = pd.DataFrame(projets)
df['commune_nom'] = df['commune_id'].map(communes)
df['budget_mdh'] = df['budget_estime'].fillna(0) / 1_000_000

# KPI
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🏗️ Total Projets", f"{stats['nb_projets']:,}")

with col2:
    st.metric("💰 Budget Total", f"{stats['budget_total']:,.0f} MDH")

with col3:
    budget_moyen = stats['budget_total'] / stats['nb_projets'] if stats['nb_projets'] > 0 else 0
    st.metric("📊 Budget Moyen", f"{budget_moyen:,.1f} MDH")

with col4:
    st.metric("🏘️ Communes", f"{stats['nb_communes']}/{len(communes)}")

st.divider()

# Filtres
st.subheader("🔍 Filtres")

col1, col2 = st.columns(2)

with col1:
    communes_list = sorted([nom for nom in df['commune_nom'].dropna().unique() if nom])
    communes_filter = st.multiselect(
        "Communes",
        options=communes_list,
        help="Sélectionner une ou plusieurs communes"
    )

with col2:
    types_list = sorted([t for t in df['type_projet'].dropna().unique() if t])
    types_filter = st.multiselect(
        "Types de projet",
        options=types_list,
        help="Filtrer par type"
    )

# Appliquer filtres
df_filtered = df.copy()

if communes_filter:
    df_filtered = df_filtered[df_filtered['commune_nom'].isin(communes_filter)]

if types_filter:
    df_filtered = df_filtered[df_filtered['type_projet'].isin(types_filter)]

st.info(f"📊 {len(df_filtered)} projet(s) | Budget : {df_filtered['budget_mdh'].sum():,.2f} MDH")

# Graphiques
if len(df_filtered) > 0:
    st.divider()
    st.subheader("📈 Analyses")
    
    tab1, tab2 = st.tabs(["Par Commune", "Par Type"])
    
    with tab1:
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
            title="Top 10 Communes par Budget",
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
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

# Liste des projets avec pagination
st.divider()
st.subheader("📋 Liste des Projets")

if len(df_filtered) > 0:
    # Pagination
    items_per_page = 50
    total_pages = (len(df_filtered) - 1) // items_per_page + 1
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        page = st.selectbox(
            f"Page (Total : {len(df_filtered)} projets)",
            range(1, total_pages + 1),
            format_func=lambda x: f"Page {x}/{total_pages}"
        )
    
    # Afficher la page
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(df_filtered))
    
    df_page = df_filtered.iloc[start_idx:end_idx]
    
    df_display = df_page[['intitule', 'commune_nom', 'type_projet', 'statut', 'budget_mdh']].copy()
    df_display.columns = ['Intitulé', 'Commune', 'Type', 'Statut', 'Budget (MDH)']
    df_display = df_display.sort_values('Budget (MDH)', ascending=False)
    
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Budget (MDH)": st.column_config.NumberColumn(
                "Budget (MDH)",
                format="%.2f"
            ),
            "Intitulé": st.column_config.TextColumn(
                "Intitulé",
                width="large"
            )
        }
    )
    
    st.caption(f"Affichage de {start_idx + 1} à {end_idx} sur {len(df_filtered)} projets")
    
    # Export
    st.divider()
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col2:
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
else:
    st.info("Aucun projet ne correspond aux filtres sélectionnés")

# Bouton rafraîchir
st.divider()
if st.button("🔄 Actualiser les données", type="secondary"):
    st.cache_data.clear()
    st.rerun()
