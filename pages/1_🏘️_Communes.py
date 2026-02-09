"""
PAGE : COMMUNES
Consultation et gestion des 29 communes d'El Jadida
"""

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Communes", page_icon="🏘️", layout="wide")

# ============================================================================
# RÉCUPÉRATION DE SUPABASE
# ============================================================================

if 'supabase' not in st.session_state:
    st.error("❌ Erreur : Connexion Supabase non initialisée")
    st.stop()

supabase = st.session_state.supabase

# ============================================================================
# INTERFACE
# ============================================================================

st.title("🏘️ Communes d'El Jadida")

# Charger les communes
try:
    response = supabase.table('communes').select('*').execute()
    communes = response.data
    
    if not communes:
        st.warning("Aucune commune trouvée dans la base de données")
        st.stop()
    
    df = pd.DataFrame(communes)
    
    # Statistiques
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📍 Total Communes", len(df))
    
    with col2:
        pop_total = df['population'].sum() if 'population' in df.columns else 0
        st.metric("👥 Population", f"{pop_total:,}")
    
    with col3:
        superficie_total = df['superficie_km2'].sum() if 'superficie_km2' in df.columns else 0
        st.metric("📏 Superficie", f"{superficie_total:.1f} km²")
    
    with col4:
        st.metric("🏛️ Cercle", "El Jadida")
    
    st.divider()
    
    # Filtres
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search = st.text_input("🔍 Rechercher une commune", placeholder="Nom de la commune...")
    
    with col2:
        sort_by = st.selectbox("Trier par", ["Nom (A-Z)", "Code", "Population"])
    
    # Filtrer
    if search:
        df_filtered = df[df['nom'].str.contains(search, case=False, na=False)]
    else:
        df_filtered = df
    
    # Trier
    if sort_by == "Nom (A-Z)":
        df_filtered = df_filtered.sort_values('nom')
    elif sort_by == "Code":
        df_filtered = df_filtered.sort_values('code_commune')
    elif sort_by == "Population":
        df_filtered = df_filtered.sort_values('population', ascending=False)
    
    st.info(f"📊 {len(df_filtered)} commune(s) affichée(s)")
    
    # Tableau
    st.subheader("📋 Liste des communes")
    
    # Préparer l'affichage
    df_display = df_filtered[['code_commune', 'nom', 'cercle', 'population']].copy()
    df_display.columns = ['Code', 'Nom', 'Cercle', 'Population']
    
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Population": st.column_config.NumberColumn(
                "Population",
                format="%d hab."
            )
        }
    )
    
    # Détails par commune
    st.divider()
    st.subheader("🔍 Détails d'une commune")
    
    selected_commune = st.selectbox(
        "Sélectionner une commune",
        df_filtered['nom'].tolist()
    )
    
    if selected_commune:
        commune_data = df_filtered[df_filtered['nom'] == selected_commune].iloc[0]
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown(f"""
            ### {commune_data['nom']}
            
            **Code** : {commune_data['code_commune']}  
            **Cercle** : {commune_data.get('cercle', 'N/A')}  
            **Caïdat** : {commune_data.get('caidat', 'N/A')}  
            **Population** : {commune_data.get('population', 0):,} habitants  
            **Superficie** : {commune_data.get('superficie_km2', 0):.2f} km²
            """)
        
        with col2:
            # Charger les projets de cette commune
            try:
                commune_id = commune_data['id']
                projets_response = supabase.table('projets_sante')\
                    .select('*')\
                    .eq('commune_id', commune_id)\
                    .execute()
                
                nb_projets = len(projets_response.data)
                budget_total = sum([p.get('budget_estime', 0) or 0 for p in projets_response.data])
                
                st.markdown(f"""
                ### 📊 Projets associés
                
                **Nombre de projets** : {nb_projets}  
                **Budget total** : {budget_total/1_000_000:,.2f} MDH
                """)
                
                if nb_projets > 0:
                    with st.expander(f"Voir les {nb_projets} projet(s)"):
                        df_projets = pd.DataFrame(projets_response.data)
                        for idx, projet in df_projets.iterrows():
                            st.markdown(f"""
                            **{idx+1}. {projet.get('intitule', 'Sans titre')}**
                            - Budget : {(projet.get('budget_estime', 0) or 0)/1_000_000:.2f} MDH
                            - Statut : {projet.get('statut', 'N/A')}
                            - Type : {projet.get('type_projet', 'N/A')}
                            """)
                            st.divider()
                
            except Exception as e:
                st.error(f"Erreur chargement projets : {str(e)}")
    
    # Export
    st.divider()
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Exporter CSV",
            csv,
            "communes_el_jadida.csv",
            "text/csv",
            use_container_width=True
        )

except Exception as e:
    st.error(f"❌ Erreur lors du chargement des données : {str(e)}")
    st.exception(e)

