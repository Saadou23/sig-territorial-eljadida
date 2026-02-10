"""
APPLICATION WEB - SYSTÈME D'INFORMATION TERRITORIAL
Point d'entrée avec authentification Supabase
"""

import streamlit as st
from supabase import create_client, Client
import hashlib

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
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt2bWl0bWdzY3psd3poa2NjdnF6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA2NjUyMDIsImV4cCI6MjA4NjI0MTIwMn0.xvKizf9RlSv8wxonHAlPw5_hsh3bKSDlFLyOwtI7kxg"
    
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

if 'supabase' not in st.session_state:
    st.session_state.supabase = supabase

# ============================================================================
# GESTION DE L'AUTHENTIFICATION
# ============================================================================

def check_auth():
    """Initialiser les variables de session"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = None

def get_user_profile(user_id):
    """Récupérer le profil utilisateur depuis la base"""
    try:
        response = supabase.table('user_profiles')\
            .select('*, communes(nom)')\
            .eq('id', user_id)\
            .eq('actif', True)\
            .single()\
            .execute()
        return response.data
    except:
        return None

def login_user(email, password):
    """Connexion utilisateur"""
    try:
        # Authentification Supabase
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            # Récupérer le profil
            profile = get_user_profile(response.user.id)
            
            if profile:
                st.session_state.user = response.user
                st.session_state.user_profile = profile
                
                # Mettre à jour dernière connexion
                supabase.table('user_profiles')\
                    .update({'derniere_connexion': 'now()'})\
                    .eq('id', response.user.id)\
                    .execute()
                
                return True, "Connexion réussie"
            else:
                return False, "Profil utilisateur non trouvé"
        
        return False, "Identifiants incorrects"
    
    except Exception as e:
        return False, f"Erreur de connexion : {str(e)}"

def logout_user():
    """Déconnexion"""
    try:
        supabase.auth.sign_out()
    except:
        pass
    
    st.session_state.user = None
    st.session_state.user_profile = None

def register_user(email, password, nom_complet, role, commune_id=None):
    """Inscription d'un nouvel utilisateur (Admin seulement)"""
    try:
        # Vérifier que l'appelant est Admin
        if not st.session_state.user_profile or st.session_state.user_profile['role'] != 'Admin':
            return False, "Permission refusée"
        
        # Créer le compte Supabase Auth
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if response.user:
            # Créer le profil
            supabase.table('user_profiles').insert({
                'id': response.user.id,
                'email': email,
                'nom_complet': nom_complet,
                'role': role,
                'commune_id': commune_id,
                'actif': True,
                'created_by': st.session_state.user.id
            }).execute()
            
            return True, f"Utilisateur {email} créé avec succès"
        
        return False, "Erreur lors de la création"
    
    except Exception as e:
        return False, f"Erreur : {str(e)}"

# ============================================================================
# PAGE DE CONNEXION
# ============================================================================

def show_login():
    """Afficher la page de connexion"""
    
    # Logo/Header centré
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1>🗺️ SIG Territorial</h1>
            <h3>Province d'El Jadida</h3>
            <p style='color: #666;'>Système d'Information Géographique et de Gestion</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Formulaire de connexion
        with st.form("login_form"):
            st.subheader("🔐 Connexion")
            
            email = st.text_input(
                "Email",
                placeholder="votre.email@example.com",
                key="login_email"
            )
            
            password = st.text_input(
                "Mot de passe",
                type="password",
                placeholder="••••••••",
                key="login_password"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                submit = st.form_submit_button(
                    "Se connecter",
                    type="primary",
                    use_container_width=True
                )
            
            with col2:
                forgot = st.form_submit_button(
                    "Mot de passe oublié ?",
                    use_container_width=True
                )
        
        if submit:
            if email and password:
                with st.spinner("Connexion en cours..."):
                    success, message = login_user(email, password)
                    
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
            else:
                st.warning("Veuillez remplir tous les champs")
        
        if forgot:
            st.info("Contactez l'administrateur pour réinitialiser votre mot de passe")
        
        # Info contact
        st.divider()
        st.markdown("""
        <div style='text-align: center; color: #666; font-size: 0.9em;'>
            <p>Besoin d'aide ? Contactez l'administrateur système</p>
            <p>📧 support@eljadida.ma | ☎️ +212 XXX XXX XXX</p>
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# PAGE D'ACCUEIL (AUTHENTIFIÉ)
# ============================================================================

def show_home():
    """Afficher la page d'accueil pour utilisateur authentifié"""
    
    profile = st.session_state.user_profile
    
    # Header avec info utilisateur
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.title("🗺️ Système d'Information Territorial")
        st.subheader("Province d'El Jadida")
    
    with col2:
        st.markdown(f"""
        **{profile['nom_complet']}**  
        *{profile['role']}*
        """)
        if profile.get('communes'):
            st.caption(f"📍 {profile['communes']['nom']}")
    
    with col3:
        if st.button("🚪 Déconnexion", use_container_width=True):
            logout_user()
            st.rerun()
    
    st.divider()
    
    # KPI globaux
    st.subheader("📊 Vue d'ensemble")
    
    try:
        # Filtrer par commune si Agent
        if profile['role'] == 'Agent' and profile.get('commune_id'):
            # Projets de la commune
            projets_data = supabase.table('projets_sante')\
                .select('budget_estime')\
                .eq('commune_id', profile['commune_id'])\
                .execute()
            
            # Indicateurs de la commune
            indicateurs_data = supabase.table('indicateurs_communes')\
                .select('id')\
                .eq('commune_id', profile['commune_id'])\
                .execute()
            
            nb_projets = len(projets_data.data)
            budget_total = sum([p.get('budget_estime', 0) or 0 for p in projets_data.data]) / 1_000_000
            nb_indicateurs = len(indicateurs_data.data)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🏘️ Ma Commune", profile['communes']['nom'])
            with col2:
                st.metric("🏗️ Projets", nb_projets)
            with col3:
                st.metric("💰 Budget", f"{budget_total:,.0f} MDH")
            with col4:
                st.metric("📊 Indicateurs Saisis", nb_indicateurs)
        
        else:
            # Vue globale pour Admin/Expert
            communes_data = supabase.table('communes').select('*').execute()
            projets_data = supabase.table('projets_sante').select('budget_estime').execute()
            indicateurs_data = supabase.table('referentiel_indicateurs').select('*').execute()
            
            nb_communes = len(communes_data.data)
            nb_projets = len(projets_data.data)
            budget_total = sum([p.get('budget_estime', 0) or 0 for p in projets_data.data]) / 1_000_000
            nb_indicateurs = len(indicateurs_data.data)
            
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
        st.error(f"Erreur chargement données : {str(e)}")
    
    st.divider()
    
    # Sections selon le rôle
    st.subheader("🎯 Mes Actions")
    
    if profile['role'] == 'Admin':
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            ### 👥 Gestion Utilisateurs
            - Créer des comptes
            - Gérer les permissions
            - Consulter l'activité
            
            *Menu → Gestion Utilisateurs*
            """)
        
        with col2:
            st.markdown("""
            ### 📊 Données & Analytics
            - Consulter toutes les données
            - Modifier les indicateurs
            - Exporter les rapports
            
            *Menu → Communes, Projets, Indicateurs*
            """)
        
        with col3:
            st.markdown("""
            ### 📈 Suivi Global
            - Progression de saisie
            - Statistiques par commune
            - Dashboards
            
            *Menu → Suivi Saisie*
            """)
    
    elif profile['role'] == 'Expert':
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 📊 Consultation
            - Voir toutes les données
            - Analyser les indicateurs
            - Exporter les rapports
            
            *Menu → Communes, Projets, Indicateurs*
            """)
        
        with col2:
            st.markdown("""
            ### ✅ Validation
            - Valider les saisies
            - Signaler les anomalies
            - Commentaires d'expert
            
            *Menu → Suivi Saisie*
            """)
    
    elif profile['role'] == 'Agent':
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            ### ✍️ Saisie des Indicateurs
            Commune : **{profile['communes']['nom']}**
            
            - 💧 Saisie Eau
            - 🏥 Saisie Santé
            - 🎓 Saisie Éducation
            - 💼 Saisie Emploi
            
            *Menu → Pages de Saisie*
            """)
        
        with col2:
            st.markdown("""
            ### 📊 Mes Données
            - Consulter mes saisies
            - Voir ma progression
            - Exporter mes données
            
            *Menu → Suivi Saisie*
            """)
    
    # Guide rapide
    st.divider()
    
    with st.expander("📖 Guide de démarrage rapide"):
        if profile['role'] == 'Admin':
            st.markdown("""
            **En tant qu'Administrateur :**
            
            1. **Créer des utilisateurs** (Menu → Gestion Utilisateurs)
            2. **Assigner les rôles** et communes aux agents
            3. **Superviser la saisie** (Menu → Suivi Saisie)
            4. **Exporter les rapports** depuis chaque page
            
            **Permissions :** Vous avez accès à toutes les fonctionnalités.
            """)
        
        elif profile['role'] == 'Expert':
            st.markdown("""
            **En tant qu'Expert Sectoriel :**
            
            1. **Consulter les données** de toutes les communes
            2. **Analyser les indicateurs** par secteur
            3. **Valider les saisies** des agents
            4. **Exporter des rapports** pour analyse
            
            **Permissions :** Consultation et validation (pas de modification).
            """)
        
        elif profile['role'] == 'Agent':
            st.markdown(f"""
            **En tant qu'Agent Terrain ({profile['communes']['nom']}) :**
            
            1. **Sélectionner un secteur** (Eau, Santé, Éducation, Emploi)
            2. **Remplir les indicateurs** pour votre commune
            3. **Enregistrer** régulièrement
            4. **Suivre votre progression** (Menu → Suivi Saisie)
            
            **Permissions :** Saisie uniquement pour {profile['communes']['nom']}.
            """)

# ============================================================================
# LOGIQUE PRINCIPALE
# ============================================================================

def main():
    """Point d'entrée principal"""
    
    check_auth()
    
    # Vérifier si utilisateur connecté
    if not st.session_state.user or not st.session_state.user_profile:
        show_login()
    else:
        show_home()

if __name__ == "__main__":
    main()
