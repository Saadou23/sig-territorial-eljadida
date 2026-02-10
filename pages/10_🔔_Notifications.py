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
PAGE : NOTIFICATIONS ET ALERTES
Affichage des notifications de retard de saisie
"""

import pandas as pd
from datetime import datetime
from supabase import create_client, Client

st.set_page_config(page_title="Notifications", page_icon="🔔", layout="wide")

# ============================================================================
# INITIALISATION
# ============================================================================

@st.cache_resource
def init_supabase() -> Client:
    SUPABASE_URL = "https://kvmitmgsczlwzhkccvqz.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt2bWl0bWdzY3psd3poa2NjdnF6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA2NjUyMDIsImV4cCI6MjA4NjI0MTIwMn0.xvKizf9RlSv8wxonHAlPw5_hsh3bKSDlFLyOwtI7kxg"
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Vérifier authentification
if 'user_profile' not in st.session_state or not st.session_state.user_profile:
    st.error("❌ Vous devez être connecté pour accéder à cette page")
    st.stop()

profile = st.session_state.user_profile

# ============================================================================
# FONCTIONS
# ============================================================================

def get_mes_notifications():
    """Récupérer les notifications de l'utilisateur"""
    try:
        response = supabase.table('notifications')\
            .select('*')\
            .eq('user_id', st.session_state.user.id)\
            .order('created_at', desc=True)\
            .execute()
        return response.data
    except:
        return []

def marquer_comme_lue(notif_id):
    """Marquer une notification comme lue"""
    try:
        supabase.table('notifications')\
            .update({'statut': 'lue'})\
            .eq('id', notif_id)\
            .execute()
        return True
    except:
        return False

def get_dashboard_retards():
    """Récupérer le dashboard des retards (Admin uniquement)"""
    try:
        response = supabase.rpc('v_dashboard_retards').execute()
        return response.data
    except:
        # Fallback si la vue n'est pas accessible via RPC
        try:
            response = supabase.table('v_dashboard_retards').select('*').execute()
            return response.data
        except:
            return []

def executer_generation_notifications():
    """Exécuter la génération des notifications (Admin uniquement)"""
    try:
        response = supabase.rpc('generer_notifications_retard').execute()
        return response.data if response.data else 0
    except Exception as e:
        st.error(f"Erreur : {str(e)}")
        return 0

# ============================================================================
# INTERFACE
# ============================================================================

st.title("🔔 Notifications et Alertes")

# Tabs selon le rôle
if profile['role'] == 'Admin':
    tab1, tab2, tab3 = st.tabs(["📬 Mes Notifications", "📊 Dashboard Retards", "⚙️ Gestion"])
else:
    tab1, tab2 = st.tabs(["📬 Mes Notifications", "📊 Mes Retards"])

# ============================================================================
# TAB 1 : MES NOTIFICATIONS
# ============================================================================

with tab1:
    st.subheader("📬 Mes Notifications")
    
    notifications = get_mes_notifications()
    
    if not notifications:
        st.info("✅ Aucune notification")
    else:
        # Compteurs
        col1, col2, col3 = st.columns(3)
        
        non_lues = len([n for n in notifications if n['statut'] == 'non_lue'])
        urgentes = len([n for n in notifications if n['priorite'] == 'urgente'])
        
        with col1:
            st.metric("📨 Total", len(notifications))
        with col2:
            st.metric("🆕 Non lues", non_lues)
        with col3:
            st.metric("🚨 Urgentes", urgentes)
        
        st.divider()
        
        # Afficher les notifications
        for notif in notifications:
            priorite_icon = {
                'basse': '📗',
                'normale': '📘',
                'haute': '📙',
                'urgente': '📕'
            }.get(notif['priorite'], '📘')
            
            statut_icon = {
                'non_lue': '🆕',
                'lue': '✅',
                'traitee': '✔️'
            }.get(notif['statut'], '')
            
            with st.expander(
                f"{priorite_icon} {statut_icon} {notif['titre']} - {notif['created_at'][:10]}",
                expanded=(notif['statut'] == 'non_lue')
            ):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Message :** {notif['message']}")
                    
                    if notif.get('secteur'):
                        st.caption(f"🎯 Secteur : {notif['secteur']}")
                    
                    if notif.get('metadata'):
                        with st.expander("Détails"):
                            st.json(notif['metadata'])
                
                with col2:
                    st.write(f"**Priorité :** {notif['priorite'].upper()}")
                    st.write(f"**Statut :** {notif['statut']}")
                    
                    if notif['statut'] == 'non_lue':
                        if st.button("✅ Marquer comme lue", key=f"read_{notif['id']}"):
                            if marquer_comme_lue(notif['id']):
                                st.success("✅ Notification marquée comme lue")
                                st.rerun()

# ============================================================================
# TAB 2 : DASHBOARD RETARDS / MES RETARDS
# ============================================================================

if profile['role'] == 'Admin':
    with tab2:
        st.subheader("📊 Dashboard des Retards de Saisie")
        
        try:
            # Charger via la vue
            response = supabase.table('v_dashboard_retards').select('*').execute()
            df = pd.DataFrame(response.data)
            
            if not df.empty:
                # KPI
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_jamais = df['nb_jamais_saisi'].sum()
                    st.metric("❌ Jamais Saisis", total_jamais)
                
                with col2:
                    total_retard = df['nb_en_retard'].sum()
                    st.metric("🚨 En Retard", total_retard)
                
                with col3:
                    total_bientot = df['nb_bientot_echeance'].sum()
                    st.metric("⚠️ Échéance Proche", total_bientot)
                
                with col4:
                    total_ajour = df['nb_a_jour'].sum()
                    st.metric("✅ À Jour", total_ajour)
                
                st.divider()
                
                # Tableau par secteur
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "secteur": "Secteur",
                        "nb_jamais_saisi": st.column_config.NumberColumn("❌ Jamais Saisi"),
                        "nb_en_retard": st.column_config.NumberColumn("🚨 En Retard"),
                        "nb_bientot_echeance": st.column_config.NumberColumn("⚠️ Bientôt"),
                        "nb_a_jour": st.column_config.NumberColumn("✅ À Jour"),
                        "total_indicateurs": st.column_config.NumberColumn("📊 Total")
                    }
                )
            else:
                st.info("Aucune donnée de retard disponible")
        
        except Exception as e:
            st.error(f"Erreur chargement : {str(e)}")

else:
    # Pour Agent Sectoriel : afficher ses retards
    with tab2:
        st.subheader("📊 Mes Retards de Saisie")
        
        try:
            # Charger les retards pour son secteur
            response = supabase.table('v_retards_saisie')\
                .select('*')\
                .eq('axe', profile['secteur'])\
                .in_('statut', ['en_retard', 'bientot_echeance', 'jamais_saisi'])\
                .execute()
            
            df = pd.DataFrame(response.data)
            
            if not df.empty:
                # Filtres
                statut_filter = st.multiselect(
                    "Statut",
                    options=df['statut'].unique(),
                    default=df['statut'].unique()
                )
                
                df_filtered = df[df['statut'].isin(statut_filter)]
                
                st.info(f"📊 {len(df_filtered)} indicateur(s) nécessitant une attention")
                
                # Tableau
                st.dataframe(
                    df_filtered[['commune_nom', 'indicateur_libelle', 'statut', 'jours_depuis_maj', 'jours_restants']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "commune_nom": "Commune",
                        "indicateur_libelle": "Indicateur",
                        "statut": st.column_config.TextColumn("Statut"),
                        "jours_depuis_maj": "Jours depuis MAJ",
                        "jours_restants": "Jours restants"
                    }
                )
            else:
                st.success("✅ Aucun retard ! Toutes vos saisies sont à jour.")
        
        except Exception as e:
            st.error(f"Erreur : {str(e)}")

# ============================================================================
# TAB 3 : GESTION (ADMIN UNIQUEMENT)
# ============================================================================

if profile['role'] == 'Admin':
    with tab3:
        st.subheader("⚙️ Gestion des Notifications")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔄 Génération Manuelle")
            
            if st.button("🚀 Générer les Notifications", type="primary"):
                with st.spinner("Génération en cours..."):
                    nb_notifs = executer_generation_notifications()
                    st.success(f"✅ {nb_notifs} notification(s) générée(s)")
        
        with col2:
            st.markdown("### 📧 Envoi d'Emails")
            
            st.info("""
            Les emails sont envoyés automatiquement pour les notifications 
            de priorité **haute** et **urgente**.
            
            Configuration requise dans Supabase Edge Functions.
            """)
        
        st.divider()
        
        st.markdown("### ⚙️ Configuration des Fréquences")
        
        try:
            response = supabase.table('config_frequences_maj').select('*').limit(10).execute()
            df_config = pd.DataFrame(response.data)
            
            if not df_config.empty:
                st.dataframe(
                    df_config[['code_indicateur', 'frequence_jours', 'delai_alerte_jours', 'actif']],
                    use_container_width=True,
                    hide_index=True
                )
        except:
            st.warning("Configuration non disponible")

# Bouton rafraîchir
st.divider()
if st.button("🔄 Actualiser"):
    st.rerun()
