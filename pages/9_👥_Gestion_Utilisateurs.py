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
PAGE : GESTION DES UTILISATEURS (Admin uniquement)
Création, modification et gestion des comptes utilisateurs
"""

import pandas as pd
from datetime import datetime
from supabase import create_client, Client

st.set_page_config(page_title="Gestion Utilisateurs", page_icon="👥", layout="wide")

# ============================================================================
# INITIALISATION
# ============================================================================

@st.cache_resource
def init_supabase() -> Client:
    SUPABASE_URL = "https://kvmitmgsczlwzhkccvqz.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt2bWl0bWdzY3psd3poa2NjdnF6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA2NjUyMDIsImV4cCI6MjA4NjI0MTIwMn0.xvKizf9RlSv8wxonHAlPw5_hsh3bKSDlFLyOwtI7kxg"
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# ============================================================================
# VÉRIFICATION DES PERMISSIONS
# ============================================================================

# Vérifier que l'utilisateur est Admin
if 'user_profile' not in st.session_state or not st.session_state.user_profile:
    st.error("❌ Vous devez être connecté pour accéder à cette page")
    st.stop()

if st.session_state.user_profile['role'] != 'Admin':
    st.error("❌ Cette page est réservée aux Administrateurs")
    st.info("Vous n'avez pas les permissions nécessaires pour gérer les utilisateurs")
    st.stop()

# ============================================================================
# FONCTIONS
# ============================================================================

def get_all_users():
    """Récupérer tous les utilisateurs"""
    try:
        response = supabase.table('user_profiles')\
            .select('*, communes(nom)')\
            .order('date_creation', desc=True)\
            .execute()
        return response.data
    except:
        return []

def get_communes():
    """Récupérer la liste des communes"""
    try:
        response = supabase.table('communes').select('id, nom').order('nom').execute()
        return {c['nom']: c['id'] for c in response.data}
    except:
        return {}

def create_user(email, password, nom_complet, role, commune_id=None, secteur='Tous'):
    """Créer un nouvel utilisateur"""
    try:
        # Créer le compte Auth
        response = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True
        })
        
        if response.user:
            # Créer le profil
            supabase.table('user_profiles').insert({
                'id': response.user.id,
                'email': email,
                'nom_complet': nom_complet,
                'role': role,
                'commune_id': commune_id,
                'secteur': secteur,
                'actif': True,
                'created_by': st.session_state.user.id
            }).execute()
            
            return True, f"✅ Utilisateur {email} créé"
        
        return False, "Erreur création compte"
    
    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg.lower():
            return False, "❌ Cet email est déjà utilisé"
        return False, f"❌ Erreur : {error_msg}"

def toggle_user_status(user_id, current_status):
    """Activer/Désactiver un utilisateur"""
    try:
        new_status = not current_status
        supabase.table('user_profiles')\
            .update({'actif': new_status})\
            .eq('id', user_id)\
            .execute()
        return True
    except:
        return False

def delete_user(user_id):
    """Supprimer un utilisateur"""
    try:
        # Supprimer le profil (cascade sur auth.users via FK)
        supabase.table('user_profiles').delete().eq('id', user_id).execute()
        return True
    except:
        return False

# ============================================================================
# INTERFACE
# ============================================================================

st.title("👥 Gestion des Utilisateurs")
st.markdown("Administration des comptes et permissions")

# Tabs
tab1, tab2, tab3 = st.tabs(["📋 Liste des Utilisateurs", "➕ Créer un Utilisateur", "📊 Statistiques"])

# ============================================================================
# TAB 1 : LISTE DES UTILISATEURS
# ============================================================================

with tab1:
    st.subheader("📋 Utilisateurs Enregistrés")
    
    users = get_all_users()
    
    if not users:
        st.info("Aucun utilisateur trouvé")
    else:
        # Filtres
        col1, col2, col3 = st.columns(3)
        
        with col1:
            role_filter = st.selectbox("Filtrer par rôle", ["Tous", "Admin", "Expert", "Agent"])
        
        with col2:
            statut_filter = st.selectbox("Statut", ["Tous", "Actifs", "Inactifs"])
        
        with col3:
            search = st.text_input("🔍 Rechercher", placeholder="Nom ou email...")
        
        # Appliquer filtres
        df_users = pd.DataFrame(users)
        
        if role_filter != "Tous":
            df_users = df_users[df_users['role'] == role_filter]
        
        if statut_filter == "Actifs":
            df_users = df_users[df_users['actif'] == True]
        elif statut_filter == "Inactifs":
            df_users = df_users[df_users['actif'] == False]
        
        if search:
            df_users = df_users[
                df_users['nom_complet'].str.contains(search, case=False, na=False) |
                df_users['email'].str.contains(search, case=False, na=False)
            ]
        
        st.info(f"📊 {len(df_users)} utilisateur(s) affiché(s)")
        
        # Afficher les utilisateurs
        for idx, user in df_users.iterrows():
            with st.expander(
                f"{'🟢' if user['actif'] else '🔴'} {user['nom_complet']} ({user['role']})",
                expanded=False
            ):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.markdown(f"""
                    **Email** : {user['email']}  
                    **Rôle** : {user['role']}  
                    **Secteur** : {user.get('secteur', 'N/A')}  
                    **Commune** : {user['communes']['nom'] if user.get('communes') else 'Toutes'}
                    """)
                
                with col2:
                    st.markdown(f"""
                    **Statut** : {'🟢 Actif' if user['actif'] else '🔴 Inactif'}  
                    **Créé le** : {user.get('date_creation', 'N/A')[:10]}  
                    **Dernière connexion** : {user.get('derniere_connexion', 'Jamais')[:16] if user.get('derniere_connexion') else 'Jamais'}
                    """)
                
                with col3:
                    # Actions
                    if user['id'] != st.session_state.user.id:  # Pas pour soi-même
                        if st.button(
                            "🔄 Désactiver" if user['actif'] else "✅ Activer",
                            key=f"toggle_{user['id']}",
                            use_container_width=True
                        ):
                            if toggle_user_status(user['id'], user['actif']):
                                st.success("Statut modifié")
                                st.rerun()
                        
                        if st.button(
                            "🗑️ Supprimer",
                            key=f"delete_{user['id']}",
                            use_container_width=True
                        ):
                            if delete_user(user['id']):
                                st.success("Utilisateur supprimé")
                                st.rerun()
                    else:
                        st.info("(Vous)")

# ============================================================================
# TAB 2 : CRÉER UN UTILISATEUR
# ============================================================================

with tab2:
    st.subheader("➕ Créer un Nouvel Utilisateur")
    
    with st.form("create_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            email = st.text_input(
                "Email *",
                placeholder="utilisateur@example.com"
            )
            
            nom_complet = st.text_input(
                "Nom Complet *",
                placeholder="Prénom NOM"
            )
            
            role = st.selectbox(
                "Rôle *",
                ["Agent", "Expert", "Admin"],
                help="Agent = Saisie pour une commune | Expert = Consultation/Validation | Admin = Gestion complète"
            )
        
        with col2:
            password = st.text_input(
                "Mot de passe *",
                type="password",
                placeholder="Min. 6 caractères"
            )
            
            password_confirm = st.text_input(
                "Confirmer mot de passe *",
                type="password"
            )
            
            secteur = st.selectbox(
                "Secteur",
                ["Tous", "Eau", "Santé", "Éducation", "Emploi"]
            )
        
        # Sélection commune (si Agent)
        commune_id = None
        if role == "Agent":
            st.warning("⚠️ Un Agent doit être assigné à une commune")
            communes = get_communes()
            commune_selected = st.selectbox(
                "Commune *",
                list(communes.keys())
            )
            commune_id = communes[commune_selected]
        
        submitted = st.form_submit_button("✅ Créer l'Utilisateur", type="primary", use_container_width=True)
        
        if submitted:
            # Validations
            if not email or not nom_complet or not password:
                st.error("❌ Tous les champs marqués * sont obligatoires")
            elif password != password_confirm:
                st.error("❌ Les mots de passe ne correspondent pas")
            elif len(password) < 6:
                st.error("❌ Le mot de passe doit contenir au moins 6 caractères")
            elif role == "Agent" and not commune_id:
                st.error("❌ Veuillez sélectionner une commune pour l'Agent")
            else:
                with st.spinner("Création en cours..."):
                    success, message = create_user(
                        email, password, nom_complet, role, commune_id, secteur
                    )
                    
                    if success:
                        st.success(message)
                        st.balloons()
                        
                        # Afficher les identifiants
                        st.info(f"""
                        **Identifiants à communiquer :**
                        - Email : {email}
                        - Mot de passe : {password}
                        - Rôle : {role}
                        """)
                    else:
                        st.error(message)

# ============================================================================
# TAB 3 : STATISTIQUES
# ============================================================================

with tab3:
    st.subheader("📊 Statistiques Utilisateurs")
    
    users = get_all_users()
    
    if users:
        df = pd.DataFrame(users)
        
        # KPI
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👥 Total Utilisateurs", len(df))
        
        with col2:
            nb_actifs = len(df[df['actif'] == True])
            st.metric("🟢 Actifs", nb_actifs)
        
        with col3:
            nb_admins = len(df[df['role'] == 'Admin'])
            st.metric("🔑 Admins", nb_admins)
        
        with col4:
            nb_agents = len(df[df['role'] == 'Agent'])
            st.metric("✍️ Agents", nb_agents)
        
        st.divider()
        
        # Graphiques
        col1, col2 = st.columns(2)
        
        with col1:
            # Par rôle
            st.markdown("### Répartition par Rôle")
            role_counts = df['role'].value_counts()
            st.bar_chart(role_counts)
        
        with col2:
            # Par statut
            st.markdown("### Répartition par Statut")
            statut_counts = df['actif'].value_counts()
            st.bar_chart(statut_counts)
        
        # Tableau récapitulatif
        st.divider()
        st.markdown("### 📋 Récapitulatif par Rôle")
        
        summary = df.groupby('role').agg({
            'id': 'count',
            'actif': 'sum'
        }).reset_index()
        summary.columns = ['Rôle', 'Total', 'Actifs']
        
        st.dataframe(summary, width='stretch', hide_index=True)

# Export
st.divider()

if users:
    csv = pd.DataFrame(users).to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Exporter la Liste (CSV)",
        csv,
        "utilisateurs.csv",
        "text/csv"
    )
