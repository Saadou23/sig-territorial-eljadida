"""
APPLICATION WEB - SYSTÈME D'INFORMATION TERRITORIAL
Point d'entrée principal de l'application Streamlit
"""

import streamlit as st
from supabase import create_client, Client
import os

# ============================================================================
# CONFIGURATION DE LA PAGE
# ============================================================================

st.set_page_config(
    page_title="SIG Territorial - El Jadida",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CONNEXION SUPABASE
# ============================================================================

@st.cache_resource
def init_supabase() -> Client:
    """Initialiser la connexion Supabase"""
    SUPABASE_URL = "https://kvmitmgsczlwzhkccvqz.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt2bWl0bWdzY3psd3poa2NjdnF6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzg5NTU1ODksImV4cCI6MjA1NDUzMTU4OX0.cC_W-hhNKAv1HbERN4zafg_8lI5Emr8"
    
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialiser Supabase
supabase = init_supabase()

# Stocker dans session state pour accès global
if 'supabase' not in st.session_state:
    st.session_state.supabase = supabase

# ============================================================================
# AUTHENTIFICATION SIMPLIFIÉE (VERSION DEMO)
# ============================================================================

def check_auth():
    """Vérifier si l'utilisateur est authentifié (mode démo)"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_role = None
        st.session_state.user_name = None

def login_demo():
    """Connexion simplifiée pour démo"""
    st.title("🔐 Connexion - SIG Territorial")
    
    st.info("👋 Version démo - Sélectionnez votre rôle")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        role = st.selectbox(
            "Rôle",
            ["Admin", "Expert Sectoriel", "Agent Terrain", "Lecteur"],
            help="Sélectionnez votre rôle pour tester l'application"
        )
        
        nom = st.text_input("Nom", "Utilisateur Démo")
        
        if st.button("Se connecter", type="primary", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.user_role = role
            st.session_state.user_name = nom
            st.rerun()
    
    with col2:
        st.markdown("""
        ### 📋 Rôles disponibles
        
        **Admin** 🔑
        - Accès complet à toutes les fonctionnalités
        - Gestion des utilisateurs
        - Dashboards analytics
        - Export des données
        
        **Expert Sectoriel** 📊
        - Validation des données sectorielles
        - Consultation des indicateurs
        - Export de rapports
        
        **Agent Terrain** ✍️
        - Saisie des données
        - Mise à jour des établissements
        - Consultation limitée
        
        **Lecteur** 👀
        - Consultation uniquement
        - Pas de modification
        """)

# ============================================================================
# PAGE D'ACCUEIL
# ============================================================================

def show_home():
    """Afficher la page d'accueil"""
    
    # Header
    st.title("🗺️ Système d'Information Territorial")
    st.subheader("Province d'El Jadida")
    
    # Informations utilisateur
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"**Bienvenue, {st.session_state.user_name}** ({st.session_state.user_role})")
    with col3:
        if st.button("🚪 Déconnexion"):
            st.session_state.authenticated = False
            st.rerun()
    
    st.divider()
    
    # KPI globaux
    st.subheader("📊 Vue d'ensemble")
    
    # Charger les statistiques depuis Supabase
    try:
        # Communes
        communes_data = supabase.table('communes').select('*').execute()
        nb_communes = len(communes_data.data)
        
        # Projets
        projets_data = supabase.table('projets_sante').select('budget_estime').execute()
        nb_projets = len(projets_data.data)
        budget_total = sum([p.get('budget_estime', 0) or 0 for p in projets_data.data]) / 1_000_000
        
        # Indicateurs
        indicateurs_data = supabase.table('referentiel_indicateurs').select('*').execute()
        nb_indicateurs = len(indicateurs_data.data)
        
        # Affichage KPI
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🏘️ Communes", nb_communes)
        
        with col2:
            st.metric("🏗️ Projets", nb_projets)
        
        with col3:
            st.metric("💰 Budget Total", f"{budget_total:,.0f} MDH")
        
        with col4:
            st.metric("📋 Indicateurs", nb_indicateurs)
        
    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {str(e)}")
    
    st.divider()
    
    # Sections principales
    st.subheader("🎯 Modules disponibles")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 📊 Données & Indicateurs
        
        - 🏘️ **Communes** : Consultation des 29 communes
        - 🏗️ **Projets** : 1 103 projets de mise à niveau
        - 📈 **Indicateurs** : Saisie et suivi des 125 indicateurs
        
        *Utilisez le menu latéral pour naviguer*
        """)
    
    with col2:
        st.markdown("""
        ### 🗺️ Cartographie (Bientôt)
        
        - Visualisation géographique
        - Heatmaps par indicateur
        - Couverture territoriale
        
        *En développement - Phase 5*
        """)
    
    with col3:
        st.markdown("""
        ### 🎯 Aide à la Décision (Bientôt)
        
        - Scoring multicritères
        - Simulation budgétaire
        - Prédictions ML
        
        *En développement - Phase 5*
        """)
    
    # Guide rapide
    st.divider()
    st.subheader("🚀 Démarrage rapide")
    
    with st.expander("📖 Comment utiliser cette application ?"):
        st.markdown("""
        **1. Navigation** 👈
        - Utilisez le **menu latéral** (à gauche) pour accéder aux différentes pages
        - Chaque page correspond à un module fonctionnel
        
        **2. Consultation des données** 📊
        - **Communes** : Liste complète avec informations détaillées
        - **Projets** : Visualisation, filtrage, export
        - **Indicateurs** : Consultation par axe sectoriel
        
        **3. Saisie des données** ✍️ (Agent/Expert)
        - Formulaires guidés pour chaque secteur
        - Validation automatique
        - Sauvegarde en temps réel
        
        **4. Dashboards** 📈 (Admin/Expert)
        - Vues analytiques
        - Graphiques interactifs
        - Export PDF
        
        **Besoin d'aide ?** Contactez l'administrateur système.
        """)

# ============================================================================
# LOGIQUE PRINCIPALE
# ============================================================================

def main():
    """Point d'entrée principal"""
    
    check_auth()
    
    if not st.session_state.authenticated:
        login_demo()
    else:
        show_home()

if __name__ == "__main__":
    main()
