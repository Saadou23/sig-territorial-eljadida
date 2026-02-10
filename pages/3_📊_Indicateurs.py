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
PAGE : INDICATEURS SECTORIELS
Consultation du référentiel des 125 indicateurs
"""

import pandas as pd
from supabase import create_client, Client

st.set_page_config(page_title="Indicateurs", page_icon="📊", layout="wide")

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

st.title("📊 Indicateurs Sectoriels")

# Charger référentiel
try:
    response = supabase.table('referentiel_indicateurs').select('*').execute()
    indicateurs = response.data
    
    if not indicateurs:
        st.warning("Aucun indicateur trouvé")
        st.stop()
    
    df = pd.DataFrame(indicateurs)
    
    # KPI
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📋 Total Indicateurs", len(df))
    
    with col2:
        nb_axes = df['axe'].nunique()
        st.metric("🎯 Axes Sectoriels", nb_axes)
    
    with col3:
        # Compter les valeurs saisies (requête sur table indicateurs_communes)
        try:
            valeurs_response = supabase.table('indicateurs_communes').select('id').execute()
            nb_valeurs = len(valeurs_response.data)
            st.metric("✍️ Valeurs Saisies", nb_valeurs)
        except:
            st.metric("✍️ Valeurs Saisies", "0")
    
    st.divider()
    
    # Répartition par axe
    st.subheader("🎯 Répartition par Axe")
    
    df_by_axe = df.groupby('axe').size().reset_index(name='Nombre')
    df_by_axe = df_by_axe.sort_values('Nombre', ascending=False)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Graphique
        import plotly.express as px
        fig = px.bar(
            df_by_axe,
            x='axe',
            y='Nombre',
            title="Nombre d'Indicateurs par Axe",
            color='Nombre',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        # Tableau
        st.dataframe(
            df_by_axe,
            width='stretch',
            hide_index=True,
            column_config={
                "axe": "Axe",
                "Nombre": st.column_config.NumberColumn(
                    "Nombre d'indicateurs",
                    format="%d"
                )
            }
        )
    
    st.divider()
    
    # Filtres et recherche
    st.subheader("🔍 Explorer les Indicateurs")
    
    col1, col2 = st.columns(2)
    
    with col1:
        axe_filter = st.selectbox(
            "Filtrer par Axe",
            ["Tous"] + sorted(df['axe'].dropna().unique().tolist())
        )
    
    with col2:
        search = st.text_input("🔍 Rechercher", placeholder="Nom de l'indicateur...")
    
    # Appliquer filtres
    df_filtered = df.copy()
    
    if axe_filter != "Tous":
        df_filtered = df_filtered[df_filtered['axe'] == axe_filter]
    
    if search:
        df_filtered = df_filtered[
            df_filtered['libelle'].str.contains(search, case=False, na=False) |
            df_filtered['description'].str.contains(search, case=False, na=False)
        ]
    
    st.info(f"📊 {len(df_filtered)} indicateur(s) affiché(s)")
    
    # Tableau des indicateurs
    st.subheader("📋 Liste des Indicateurs")
    
    # Colonnes disponibles
    colonnes_affichage = ['code', 'libelle', 'axe', 'unite', 'frequence_maj']
    df_display = df_filtered[colonnes_affichage].copy()
    df_display.columns = ['Code', 'Indicateur', 'Axe', 'Unité', 'Fréquence MAJ']
    
    st.dataframe(
        df_display,
        width='stretch',
        hide_index=True,
        column_config={
            "Indicateur": st.column_config.TextColumn(
                "Indicateur",
                width="large"
            )
        }
    )
    
    # Détails d'un indicateur
    st.divider()
    st.subheader("🔍 Détails d'un Indicateur")
    
    indicateur_selected = st.selectbox(
        "Sélectionner un indicateur",
        df_filtered['libelle'].tolist()
    )
    
    if indicateur_selected:
        indicateur = df_filtered[df_filtered['libelle'] == indicateur_selected].iloc[0]
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"""
            ### {indicateur['libelle']}
            
            **Code** : `{indicateur['code']}`  
            **Axe** : {indicateur['axe']}  
            **Unité** : {indicateur.get('unite', 'N/A')}  
            **Fréquence de mise à jour** : {indicateur.get('frequence_maj', 'N/A')}
            
            **Description** :  
            {indicateur.get('description', 'Aucune description disponible')}
            """)
        
        with col2:
            st.info("""
            ### 📝 Saisie des valeurs
            
            La saisie des valeurs pour cet indicateur se fait via le module **"Saisie Indicateurs"** (en développement).
            
            Pour chaque commune, vous pourrez saisir :
            - La valeur de l'indicateur
            - L'année de référence
            - La source des données
            - Des commentaires
            """)
            
            # Vérifier si des valeurs existent
            try:
                valeurs_response = supabase.table('indicateurs_communes')\
                    .select('*')\
                    .eq('code_indicateur', indicateur['code'])\
                    .execute()
                
                nb_valeurs = len(valeurs_response.data)
                
                if nb_valeurs > 0:
                    st.success(f"✅ {nb_valeurs} valeur(s) saisie(s)")
                else:
                    st.warning("⚠️ Aucune valeur saisie")
            except:
                st.info("ℹ️ Données non disponibles")
    
    # Statistiques de saisie par axe
    st.divider()
    st.subheader("📈 État de Saisie par Axe")
    
    try:
        # Charger toutes les valeurs saisies
        valeurs_response = supabase.table('indicateurs_communes').select('code_indicateur').execute()
        valeurs_saisies = pd.DataFrame(valeurs_response.data)
        
        if len(valeurs_saisies) > 0:
            # Joindre avec référentiel pour avoir les axes
            df_saisie = df.merge(
                valeurs_saisies.groupby('code_indicateur').size().reset_index(name='nb_saisies'),
                left_on='code',
                right_on='code_indicateur',
                how='left'
            )
            df_saisie['nb_saisies'] = df_saisie['nb_saisies'].fillna(0)
            
            # Grouper par axe
            df_saisie_axe = df_saisie.groupby('axe').agg({
                'code': 'count',
                'nb_saisies': 'sum'
            }).reset_index()
            df_saisie_axe.columns = ['Axe', 'Nb Indicateurs', 'Nb Valeurs Saisies']
            df_saisie_axe['Taux Remplissage (%)'] = (
                (df_saisie_axe['Nb Valeurs Saisies'] / (df_saisie_axe['Nb Indicateurs'] * 29)) * 100
            ).round(1)
            
            st.dataframe(
                df_saisie_axe,
                width='stretch',
                hide_index=True,
                column_config={
                    "Taux Remplissage (%)": st.column_config.ProgressColumn(
                        "Taux Remplissage",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100
                    )
                }
            )
        else:
            st.info("ℹ️ Aucune valeur saisie pour le moment")
    
    except Exception as e:
        st.warning(f"Impossible de charger l'état de saisie : {str(e)}")
    
    # Export
    st.divider()
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col2:
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Exporter Filtré (CSV)",
            csv,
            "indicateurs_filtered.csv",
            "text/csv",
            use_container_width=True
        )
    
    with col3:
        csv_all = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Exporter Tout (CSV)",
            csv_all,
            "indicateurs_all.csv",
            "text/csv",
            use_container_width=True
        )

except Exception as e:
    st.error(f"❌ Erreur : {str(e)}")
    st.exception(e)
