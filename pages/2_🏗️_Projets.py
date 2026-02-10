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

"""
PAGE : PROJETS DE MISE À NIVEAU TERRITORIALE
Consultation et analyse des 987 projets
"""

import pandas as pd
import plotly.express as px
from supabase import create_client, Client

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
# CHARGEMENT DES DONNÉES
# ============================================================================

@st.cache_data(ttl=600)
def load_data():
    """Charger toutes les données nécessaires"""
    try:
        # Communes
        communes_response = supabase.table('communes').select('id, nom').execute()
        communes = {c['id']: c['nom'] for c in communes_response.data}
        
        # Projets
        projets_response = supabase.table('projets_sante')\
            .select('id, commune_id, intitule, type_projet, statut, budget_estime, avancement_pct')\
            .execute()
        
        projets = projets_response.data
        
        return communes, projets
    
    except Exception as e:
        st.error(f"Erreur de chargement : {str(e)}")
        return {}, []

# ============================================================================
# INTERFACE
# ============================================================================

st.title("🏗️ Projets de Mise à Niveau Territoriale")

# Charger les données
with st.spinner("Chargement des données..."):
    communes, projets = load_data()

if not projets:
    st.warning("⚠️ Aucun projet trouvé")
    st.stop()

# Créer DataFrame
df = pd.DataFrame(projets)
df['commune_nom'] = df['commune_id'].map(communes)
df['budget_mdh'] = df['budget_estime'].fillna(0) / 1_000_000

# KPI Globaux
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🏗️ Total Projets", f"{len(df):,}")

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
        help="Filtrer par statut"
    )

# Filtre budget
col1, col2 = st.columns(2)

with col1:
    budget_min = st.number_input(
        "Budget minimum (MDH)",
        min_value=0.0,
        value=0.0,
        step=0.1
    )

with col2:
    budget_max = st.number_input(
        "Budget maximum (MDH)",
        min_value=0.0,
        value=float(df['budget_mdh'].max()),
        step=0.1
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

st.info(f"📊 {len(df_filtered)} projet(s) | Budget : {df_filtered['budget_mdh'].sum():,.2f} MDH")

# Graphiques
if len(df_filtered) > 0:
    st.divider()
    st.subheader("📈 Analyses")
    
    tab1, tab2, tab3 = st.tabs(["Par Commune", "Par Type", "Distribution Budget"])
    
    with tab1:
        df_by_commune = df_filtered.groupby('commune_nom').agg({
            'id': 'count',
            'budget_mdh': 'sum'
        }).reset_index()
        df_by_commune.columns = ['Commune', 'Nb Projets', 'Budget (MDH)']
        df_by_commune = df_by_commune.sort_values('Budget (MDH)', ascending=False).head(15)
        
        fig = px.bar(
            df_by_commune,
            x='Commune',
            y='Budget (MDH)',
            color='Nb Projets',
            title="Top 15 Communes par Budget",
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
    
    with tab3:
        fig = px.histogram(
            df_filtered,
            x='budget_mdh',
            nbins=50,
            title="Distribution des Budgets",
            labels={'budget_mdh': 'Budget (MDH)'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Stats budget
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Min", f"{df_filtered['budget_mdh'].min():.2f} MDH")
        with col2:
            st.metric("Médiane", f"{df_filtered['budget_mdh'].median():.2f} MDH")
        with col3:
            st.metric("Moyenne", f"{df_filtered['budget_mdh'].mean():.2f} MDH")
        with col4:
            st.metric("Max", f"{df_filtered['budget_mdh'].max():.2f} MDH")

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
            f"Page ({len(df_filtered)} projets)",
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
    
    st.caption(f"Affichage {start_idx + 1} à {end_idx} sur {len(df_filtered)} projets")
    
    # Export
    st.divider()
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col2:
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Exporter Filtré",
            csv,
            "projets_filtered.csv",
            "text/csv",
            use_container_width=True
        )
    
    with col3:
        csv_all = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Exporter Tout",
            csv_all,
            "projets_all.csv",
            "text/csv",
            use_container_width=True
        )
else:
    st.info("Aucun projet ne correspond aux filtres")

# Bouton rafraîchir
st.divider()
if st.button("🔄 Actualiser les données"):
    st.cache_data.clear()
    st.rerun()
