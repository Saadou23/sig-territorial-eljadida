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
from streamlit_folium import st_folium
from supabase import create_client

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
def load_communes_gps():
    """Charger les communes avec GPS"""
    communes = supabase.table('communes').select('*').execute()
    df = pd.DataFrame(communes.data)
    
    # Vérifier les colonnes GPS
    if 'latitude' not in df.columns or 'longitude' not in df.columns:
        return None
    
    # Filtrer les communes avec GPS
    df_gps = df[df['latitude'].notna() & df['longitude'].notna()].copy()
    
    # Ajouter stats projets
    projets = supabase.table('projets_sante').select('commune_id, budget_estime').execute()
    if projets.data:
        df_projets = pd.DataFrame(projets.data)
        stats = df_projets.groupby('commune_id').agg({
            'budget_estime': ['count', 'sum']
        }).reset_index()
        stats.columns = ['id', 'nb_projets', 'budget_total']
        df_gps = df_gps.merge(stats, on='id', how='left')
        df_gps['nb_projets'] = df_gps['nb_projets'].fillna(0).astype(int)
        df_gps['budget_mdh'] = df_gps['budget_total'].fillna(0) / 1_000_000
    else:
        df_gps['nb_projets'] = 0
        df_gps['budget_mdh'] = 0.0
    
    return df_gps

# ============================================================================
# TITRE ET VERIFICATION
# ============================================================================

st.title("🗺️ Cartographie Interactive")

# Charger les données
df_communes = load_communes_gps()

if df_communes is None or df_communes.empty:
    st.error("❌ Les coordonnées GPS ne sont pas encore configurées")
    st.info("""
    ### Action requise
    
    Exécutez le script SQL `12_ajout_coordonnees_gps_FIXED.sql` dans Supabase pour ajouter :
    - Colonne `latitude`
    - Colonne `longitude`
    - Colonne `milieu`
    - Coordonnées des 29 communes
    """)
    st.stop()

# ============================================================================
# STATISTIQUES
# ============================================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📍 Communes Géolocalisées", len(df_communes))

with col2:
    if 'milieu' in df_communes.columns:
        urbain = len(df_communes[df_communes['milieu'] == 'Urbain'])
        st.metric("🏙️ Urbaines", urbain)
    else:
        st.metric("🏙️ Urbaines", "N/A")

with col3:
    if 'milieu' in df_communes.columns:
        rural = len(df_communes[df_communes['milieu'] == 'Rural'])
        st.metric("🌾 Rurales", rural)
    else:
        st.metric("🌾 Rurales", "N/A")

with col4:
    budget_total = df_communes['budget_mdh'].sum()
    st.metric("💰 Budget Total", f"{budget_total:,.0f} MDH")

st.divider()

# ============================================================================
# ONGLETS
# ============================================================================

tab1, tab2 = st.tabs(["🗺️ Carte des Communes", "📊 Données"])

# ============================================================================
# TAB 1 : CARTE
# ============================================================================

with tab1:
    st.subheader("Carte Interactive des Communes")
    
    # Filtres
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("### Filtres")
        
        if 'milieu' in df_communes.columns:
            milieu_filter = st.multiselect(
                "Type de commune",
                options=df_communes['milieu'].unique(),
                default=df_communes['milieu'].unique()
            )
            df_filtered = df_communes[df_communes['milieu'].isin(milieu_filter)]
        else:
            df_filtered = df_communes
        
        st.info(f"📊 {len(df_filtered)} commune(s)")
        
        # Top 5
        st.markdown("### Top 5 Budget")
        top5 = df_filtered.nlargest(5, 'budget_mdh')[['nom', 'budget_mdh']]
        for _, row in top5.iterrows():
            st.text(f"• {row['nom']}: {row['budget_mdh']:.1f}M")
    
    with col2:
        # Créer la carte
        centre_lat = df_filtered['latitude'].mean()
        centre_lon = df_filtered['longitude'].mean()
        
        carte = folium.Map(
            location=[centre_lat, centre_lon],
            zoom_start=10,
            tiles='OpenStreetMap'
        )
        
        # Ajouter les marqueurs
        for _, row in df_filtered.iterrows():
            # Couleur selon le milieu
            if 'milieu' in row and row['milieu'] == 'Urbain':
                couleur = 'blue'
                icone = 'building'
            else:
                couleur = 'green'
                icone = 'tree'
            
            # Popup
            popup_html = f"""
            <div style="font-family: Arial; width: 200px;">
                <h4 style="margin: 0; color: {couleur};">{row['nom']}</h4>
                <hr style="margin: 5px 0;">
                <p style="margin: 5px 0; font-size: 12px;">
                    <b>Type :</b> {row.get('milieu', 'N/A')}<br>
                    <b>Projets :</b> {int(row['nb_projets'])}<br>
                    <b>Budget :</b> {row['budget_mdh']:.2f} MDH
                </p>
            </div>
            """
            
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=row['nom'],
                icon=folium.Icon(color=couleur, icon=icone, prefix='fa')
            ).add_to(carte)
        
        # Afficher la carte avec une clé unique basée sur les filtres
        carte_key = f"carte_communes_{len(df_filtered)}_{hash(str(milieu_filter) if 'milieu' in df_communes.columns else 'all')}"
        st_folium(carte, width=None, height=600, key=carte_key, returned_objects=[])

# ============================================================================
# TAB 2 : DONNÉES
# ============================================================================

with tab2:
    st.subheader("📋 Liste des Communes")
    
    # Préparer l'affichage
    colonnes_affichage = ['nom', 'nb_projets', 'budget_mdh']
    if 'milieu' in df_communes.columns:
        colonnes_affichage.insert(1, 'milieu')
    
    df_display = df_communes[colonnes_affichage].copy()
    
    # Renommer
    rename_dict = {
        'nom': 'Commune',
        'nb_projets': 'Projets',
        'budget_mdh': 'Budget (MDH)'
    }
    if 'milieu' in df_display.columns:
        rename_dict['milieu'] = 'Type'
    
    df_display = df_display.rename(columns=rename_dict)
    
    # Afficher
    st.dataframe(
        df_display.sort_values('Budget (MDH)', ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Budget (MDH)": st.column_config.NumberColumn(format="%.2f")
        }
    )
    
    # Export
    csv = df_communes.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Exporter CSV", csv, "communes_gps.csv", "text/csv")

# Rafraîchir
if st.button("🔄 Actualiser les données"):
    st.cache_data.clear()
    st.rerun()
