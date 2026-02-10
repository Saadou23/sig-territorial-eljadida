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
from supabase import create_client

st.set_page_config(page_title="Cartographie", page_icon="🗺️", layout="wide")

# Supabase
@st.cache_resource
def init_supabase():
    SUPABASE_URL = "https://kvmitmgsczlwzhkccvqz.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt2bWl0bWdzY3psd3poa2NjdnF6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA2NjUyMDIsImV4cCI6MjA4NjI0MTIwMn0.xvKizf9RlSv8wxonHAlPw5_hsh3bKSDlFLyOwtI7kxg"
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

st.title("🗺️ Cartographie Interactive")

st.warning("⚠️ Module en cours d'installation")

st.info("""
### Prérequis manquants

Pour activer la cartographie interactive, veuillez :

1. **Exécuter le script SQL** : `12_ajout_coordonnees_gps_FIXED.sql` dans Supabase
   - Cela ajoutera les colonnes `latitude`, `longitude` et `milieu` à la table `communes`
   
2. **Vérifier l'installation** :
   ```sql
   SELECT nom, latitude, longitude, milieu 
   FROM communes 
   LIMIT 5;
   ```
   
3. **Attendez** que je finalise le module cartographique

### Problèmes détectés

D'après les logs, la colonne `milieu` n'existe pas encore dans votre table `communes`.

**Action requise** : Exécutez le script SQL fourni dans Supabase.
""")

# Vérifier si les colonnes existent
try:
    test = supabase.table('communes').select('latitude, longitude, milieu').limit(1).execute()
    if test.data:
        st.success("✅ Colonnes GPS détectées ! Le module sera bientôt disponible.")
    else:
        st.error("❌ Les colonnes GPS n'existent pas encore")
except Exception as e:
    st.error(f"❌ Erreur : {str(e)}")
    st.code("""
    Veuillez exécuter ce script SQL dans Supabase :
    
    ALTER TABLE communes 
    ADD COLUMN IF NOT EXISTS latitude DECIMAL(10, 8),
    ADD COLUMN IF NOT EXISTS longitude DECIMAL(10, 8),
    ADD COLUMN IF NOT EXISTS milieu TEXT;
    """)

st.divider()

st.markdown("### 📊 Statistiques des communes")

# Afficher les communes sans erreur
communes = supabase.table('communes').select('*').execute()
df = pd.DataFrame(communes.data)

if not df.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("🏘️ Total Communes", len(df))
    
    with col2:
        # Vérifier si milieu existe
        if 'milieu' in df.columns:
            urbain = len(df[df['milieu'] == 'Urbain'])
            st.metric("🏙️ Urbaines", urbain)
        else:
            st.metric("🏙️ Urbaines", "N/A")
    
    st.dataframe(df[['nom']].head(10), use_container_width=True)
else:
    st.warning("Aucune commune trouvée")
