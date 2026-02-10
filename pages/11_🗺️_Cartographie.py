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
import folium
from folium import plugins
from streamlit_folium import st_folium
from supabase import create_client, Client

st.set_page_config(page_title="Cartographie", page_icon="🗺️", layout="wide")

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
def load_carte_communes():
    """Charger les données pour la carte des communes"""
    try:
        response = supabase.table('v_carte_communes').select('*').execute()
        return pd.DataFrame(response.data)
    except:
        # Fallback si la vue n'existe pas encore
        communes = supabase.table('communes').select('*').execute()
        df = pd.DataFrame(communes.data)
        # Ajouter des stats basiques
        if not df.empty:
            projets = supabase.table('projets_sante').select('commune_id, budget_estime').execute()
            if projets.data:
                df_projets = pd.DataFrame(projets.data)
                stats = df_projets.groupby('commune_id').agg({
                    'budget_estime': ['count', 'sum']
                }).reset_index()
                stats.columns = ['id', 'nb_projets', 'budget_total']
                df = df.merge(stats, on='id', how='left')
                df['nb_projets'] = df['nb_projets'].fillna(0).astype(int)
                df['budget_mdh'] = df['budget_total'].fillna(0) / 1_000_000
            else:
                df['nb_projets'] = 0
                df['budget_mdh'] = 0.0
        return df

@st.cache_data(ttl=600)
def load_carte_projets():
    """Charger les données pour la carte des projets"""
    try:
        response = supabase.table('v_carte_projets').select('*').execute()
        return pd.DataFrame(response.data)
    except:
        # Fallback
        projets = supabase.table('projets_sante').select('*, communes(nom, latitude, longitude)').execute()
        data = []
        for p in projets.data:
            if p.get('communes') and p['communes'].get('latitude'):
                data.append({
                    'id': p['id'],
                    'intitule': p['intitule'],
                    'type_projet': p.get('type_projet', 'N/A'),
                    'statut': p.get('statut', 'N/A'),
                    'budget_mdh': (p.get('budget_estime', 0) or 0) / 1_000_000,
                    'avancement_pct': p.get('avancement_pct', 0),
                    'commune_nom': p['communes']['nom'],
                    'latitude': p['communes']['latitude'],
                    'longitude': p['communes']['longitude']
                })
        return pd.DataFrame(data)

# ============================================================================
# FONCTIONS CARTOGRAPHIE
# ============================================================================

def creer_carte_base():
    """Créer la carte de base centrée sur El Jadida"""
    carte = folium.Map(
        location=[33.2316, -8.5007],  # El Jadida
        zoom_start=10,
        tiles='OpenStreetMap'
    )
    
    # Ajouter contrôle de couches
    folium.LayerControl().add_to(carte)
    
    return carte

def ajouter_marqueurs_communes(carte, df_communes):
    """Ajouter les marqueurs pour les communes"""
    
    # Groupe pour les communes
    groupe_communes = folium.FeatureGroup(name='Communes', show=True)
    
    for _, row in df_communes.iterrows():
        if pd.notna(row['latitude']) and pd.notna(row['longitude']):
            
            # Couleur selon le milieu
            couleur = '#1976D2' if row['milieu'] == 'Urbain' else '#4CAF50'
            
            # Popup avec infos
            popup_html = f"""
            <div style="font-family: Arial; width: 250px;">
                <h4 style="color: {couleur}; margin: 0;">{row['nom']}</h4>
                <hr style="margin: 5px 0;">
                <p style="margin: 5px 0;">
                    <b>Type :</b> {row['milieu']}<br>
                    <b>Projets :</b> {int(row.get('nb_projets', 0))}<br>
                    <b>Budget :</b> {row.get('budget_mdh', 0):.2f} MDH<br>
                    <b>Indicateurs :</b> {int(row.get('nb_indicateurs_saisis', 0))}
                </p>
            </div>
            """
            
            # Marqueur
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=8 if row['milieu'] == 'Urbain' else 6,
                popup=folium.Popup(popup_html, max_width=300),
                color=couleur,
                fill=True,
                fillColor=couleur,
                fillOpacity=0.7,
                weight=2
            ).add_to(groupe_communes)
            
            # Label avec le nom
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                icon=folium.DivIcon(html=f"""
                    <div style="font-size: 10px; color: black; font-weight: bold; 
                                background-color: white; padding: 2px 4px; 
                                border-radius: 3px; border: 1px solid {couleur};">
                        {row['nom']}
                    </div>
                """)
            ).add_to(groupe_communes)
    
    groupe_communes.add_to(carte)
    return carte

def ajouter_marqueurs_projets(carte, df_projets, filtre_type=None, filtre_statut=None):
    """Ajouter les marqueurs pour les projets"""
    
    # Filtrer
    df_filtered = df_projets.copy()
    if filtre_type:
        df_filtered = df_filtered[df_filtered['type_projet'].isin(filtre_type)]
    if filtre_statut:
        df_filtered = df_filtered[df_filtered['statut'].isin(filtre_statut)]
    
    # Groupe pour les projets
    groupe_projets = folium.FeatureGroup(name=f'Projets ({len(df_filtered)})', show=False)
    
    # Couleurs par statut
    couleurs_statut = {
        'En cours': '#FF9800',
        'Terminé': '#4CAF50',
        'Planifié': '#2196F3',
        'En attente': '#9E9E9E'
    }
    
    for _, row in df_filtered.iterrows():
        if pd.notna(row['latitude']) and pd.notna(row['longitude']):
            
            couleur = couleurs_statut.get(row['statut'], '#757575')
            
            # Popup
            popup_html = f"""
            <div style="font-family: Arial; width: 300px;">
                <h4 style="color: {couleur}; margin: 0;">{row['intitule'][:50]}...</h4>
                <hr style="margin: 5px 0;">
                <p style="margin: 5px 0;">
                    <b>Commune :</b> {row['commune_nom']}<br>
                    <b>Type :</b> {row['type_projet']}<br>
                    <b>Statut :</b> {row['statut']}<br>
                    <b>Budget :</b> {row['budget_mdh']:.2f} MDH<br>
                    <b>Avancement :</b> {row.get('avancement_pct', 0):.0f}%
                </p>
            </div>
            """
            
            # Icône selon le type
            icon_map = {
                'Infrastructure': 'road',
                'Santé': 'hospital',
                'Éducation': 'graduation-cap',
                'Eau': 'tint',
                'Électricité': 'bolt',
                'Sport': 'futbol'
            }
            icon = icon_map.get(row['type_projet'], 'map-marker')
            
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=folium.Popup(popup_html, max_width=350),
                icon=folium.Icon(color='orange' if row['statut'] == 'En cours' else 'green', 
                               icon=icon, prefix='fa'),
                tooltip=row['intitule'][:30]
            ).add_to(groupe_projets)
    
    groupe_projets.add_to(carte)
    return carte

def ajouter_heatmap_budget(carte, df_communes):
    """Ajouter une heatmap des budgets"""
    
    # Données pour heatmap
    heat_data = []
    for _, row in df_communes.iterrows():
        if pd.notna(row['latitude']) and pd.notna(row['longitude']) and row.get('budget_mdh', 0) > 0:
            # Intensité basée sur le budget (normalisée)
            intensite = min(row['budget_mdh'] / 100, 10)  # Max 10
            heat_data.append([row['latitude'], row['longitude'], intensite])
    
    if heat_data:
        plugins.HeatMap(
            heat_data,
            name='Heatmap Budget',
            min_opacity=0.3,
            max_zoom=13,
            radius=25,
            blur=15,
            show=False
        ).add_to(carte)
    
    return carte

# ============================================================================
# INTERFACE
# ============================================================================

st.title("🗺️ Cartographie Interactive")

# Charger les données
with st.spinner("Chargement des données cartographiques..."):
    df_communes = load_carte_communes()
    df_projets = load_carte_projets()

if df_communes.empty:
    st.error("❌ Aucune commune avec coordonnées GPS")
    st.info("Veuillez exécuter le script SQL : 12_ajout_coordonnees_gps.sql")
    st.stop()

# Statistiques
col1, col2, col3, col4 = st.columns(4)

with col1:
    nb_communes_gps = len(df_communes[df_communes['latitude'].notna()])
    st.metric("📍 Communes Géolocalisées", nb_communes_gps)

with col2:
    st.metric("🏗️ Projets sur Carte", len(df_projets))

with col3:
    budget_total = df_communes['budget_mdh'].sum()
    st.metric("💰 Budget Total", f"{budget_total:,.0f} MDH")

with col4:
    st.metric("📊 Couches Disponibles", "4")

st.divider()

# Onglets
tab1, tab2, tab3 = st.tabs(["🏘️ Vue Communes", "🏗️ Vue Projets", "🔥 Heatmap Budget"])

# ============================================================================
# TAB 1 : VUE COMMUNES
# ============================================================================

with tab1:
    st.subheader("Carte des Communes")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("### Légende")
        st.markdown("🔵 **Urbain** : Communes urbaines")
        st.markdown("🟢 **Rural** : Communes rurales")
        
        st.divider()
        
        # Filtres
        milieu_filter = st.multiselect(
            "Type de commune",
            options=df_communes['milieu'].unique(),
            default=df_communes['milieu'].unique()
        )
        
        # Appliquer filtre
        df_communes_filtered = df_communes[df_communes['milieu'].isin(milieu_filter)]
        
        st.info(f"📊 {len(df_communes_filtered)} commune(s)")
        
        # Tableau récap
        st.markdown("### Top 5 Communes")
        top_communes = df_communes_filtered.nlargest(5, 'budget_mdh')[['nom', 'nb_projets', 'budget_mdh']]
        st.dataframe(
            top_communes,
            hide_index=True,
            column_config={
                'nom': 'Commune',
                'nb_projets': st.column_config.NumberColumn('Projets', format='%d'),
                'budget_mdh': st.column_config.NumberColumn('Budget (MDH)', format='%.1f')
            }
        )
    
    with col2:
        # Créer la carte
        carte = creer_carte_base()
        carte = ajouter_marqueurs_communes(carte, df_communes_filtered)
        carte = ajouter_heatmap_budget(carte, df_communes_filtered)
        
        # Afficher avec clé unique
        st_folium(carte, width=None, height=600, key="map_communes", returned_objects=[])

# ============================================================================
# TAB 2 : VUE PROJETS
# ============================================================================

with tab2:
    st.subheader("Carte des Projets")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("### Filtres")
        
        # Filtre type
        types_projet = df_projets['type_projet'].unique().tolist()
        type_filter = st.multiselect(
            "Type de projet",
            options=types_projet,
            default=types_projet
        )
        
        # Filtre statut
        statuts = df_projets['statut'].unique().tolist()
        statut_filter = st.multiselect(
            "Statut",
            options=statuts,
            default=statuts
        )
        
        # Budget
        budget_min = st.number_input(
            "Budget min (MDH)",
            min_value=0.0,
            value=0.0,
            step=0.1
        )
        
        # Appliquer filtres
        df_projets_filtered = df_projets[
            (df_projets['type_projet'].isin(type_filter)) &
            (df_projets['statut'].isin(statut_filter)) &
            (df_projets['budget_mdh'] >= budget_min)
        ]
        
        st.info(f"🏗️ {len(df_projets_filtered)} projet(s)")
        
        # Stats
        st.markdown("### Statistiques")
        st.metric("Budget Filtré", f"{df_projets_filtered['budget_mdh'].sum():.0f} MDH")
        st.metric("Budget Moyen", f"{df_projets_filtered['budget_mdh'].mean():.2f} MDH")
    
    with col2:
        # Créer la carte
        carte = creer_carte_base()
        carte = ajouter_marqueurs_communes(carte, df_communes)
        carte = ajouter_marqueurs_projets(carte, df_projets_filtered, type_filter, statut_filter)
        
        # Afficher avec clé unique
        st_folium(carte, width=None, height=600, key="map_projets", returned_objects=[])

# ============================================================================
# TAB 3 : HEATMAP BUDGET
# ============================================================================

with tab3:
    st.subheader("Carte de Chaleur - Concentration Budgétaire")
    
    st.info("""
    Cette carte visualise la **concentration des budgets** par zone géographique.
    Les zones rouges indiquent une forte concentration de projets et de budget.
    """)
    
    # Créer la carte
    carte = creer_carte_base()
    carte = ajouter_marqueurs_communes(carte, df_communes)
    carte = ajouter_heatmap_budget(carte, df_communes)
    
    # Afficher avec clé unique
    st_folium(carte, width=None, height=600, key="map_heatmap", returned_objects=[])
    
    # Légende
    st.markdown("### Interprétation")
    st.markdown("🔴 **Rouge** : Forte concentration budgétaire")
    st.markdown("🟡 **Jaune** : Concentration moyenne")
    st.markdown("🔵 **Bleu** : Faible concentration")

# Export
st.divider()

col1, col2, col3 = st.columns(3)

with col2:
    if st.button("📥 Exporter Données GPS (CSV)", use_container_width=True):
        csv = df_communes.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Télécharger",
            csv,
            "communes_gps.csv",
            "text/csv",
            use_container_width=True
        )

# Rafraîchir
if st.button("🔄 Actualiser"):
    st.cache_data.clear()
    st.rerun()
