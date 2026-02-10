"""
PAGE PROJETS - Version DEBUG sans cache
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

st.set_page_config(page_title="Projets", page_icon="🏗️", layout="wide")

# ============================================================================
# SUPABASE (SANS CACHE)
# ============================================================================

def init_supabase():
    SUPABASE_URL = "https://kvmitmgsczlwzhkccvqz.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt2bWl0bWdzY3psd3poa2NjdnF6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA2NjUyMDIsImV4cCI6MjA4NjI0MTIwMn0.xvKizf9RlSv8wxonHAlPw5_hsh3bKSDlFLyOwtI7kxg"
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

st.title("🏗️ Projets de Mise à Niveau Territoriale")

# ============================================================================
# CHARGEMENT SANS CACHE
# ============================================================================

st.info("🔍 Mode DEBUG activé - Chargement direct sans cache")

try:
    # 1. Charger les communes
    st.write("**Étape 1 : Chargement des communes...**")
    communes_response = supabase.table('communes').select('id, nom').execute()
    communes = {c['id']: c['nom'] for c in communes_response.data}
    st.success(f"✅ {len(communes)} communes chargées")
    
    # 2. Compter les projets
    st.write("**Étape 2 : Comptage des projets...**")
    count_response = supabase.table('projets_sante').select('id', count='exact').execute()
    
    # DEBUG : Afficher la réponse brute
    with st.expander("🔍 Réponse brute de Supabase"):
        st.write("Response object:", count_response)
        st.write("Data:", count_response.data)
        st.write("Count:", getattr(count_response, 'count', 'N/A'))
    
    nb_projets = len(count_response.data)
    st.success(f"✅ {nb_projets} projets trouvés")
    
    if nb_projets == 0:
        st.error("❌ Aucun projet dans la table projets_sante")
        st.info("Vérifiez avec cette requête SQL : `SELECT COUNT(*) FROM projets_sante;`")
        st.stop()
    
    # 3. Charger les projets (limité à 100 pour debug)
    st.write("**Étape 3 : Chargement des projets (100 premiers)...**")
    projets_response = supabase.table('projets_sante')\
        .select('id, commune_id, intitule, type_projet, statut, budget_estime')\
        .limit(100)\
        .execute()
    
    projets = projets_response.data
    st.success(f"✅ {len(projets)} projets chargés")
    
    # 4. Créer DataFrame
    df = pd.DataFrame(projets)
    df['commune_nom'] = df['commune_id'].map(communes)
    df['budget_mdh'] = df['budget_estime'].fillna(0) / 1_000_000
    
    # Afficher les données brutes
    with st.expander("🔍 Aperçu des données"):
        st.write("**Colonnes disponibles :**", df.columns.tolist())
        st.write("**3 premiers projets :**")
        st.dataframe(df.head(3))
    
    # KPI
    st.divider()
    st.subheader("📊 Statistiques")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🏗️ Projets (échantillon)", len(df))
        st.caption(f"Total en base : {nb_projets}")
    
    with col2:
        budget_total = df['budget_mdh'].sum()
        st.metric("💰 Budget (échantillon)", f"{budget_total:.0f} MDH")
    
    with col3:
        nb_communes_avec_projets = df['commune_id'].nunique()
        st.metric("🏘️ Communes", f"{nb_communes_avec_projets}/{len(communes)}")
    
    # Liste simple
    st.divider()
    st.subheader("📋 Liste des Projets (100 premiers)")
    
    df_display = df[['intitule', 'commune_nom', 'type_projet', 'budget_mdh']].copy()
    df_display.columns = ['Intitulé', 'Commune', 'Type', 'Budget (MDH)']
    
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True
    )
    
    # Graphique simple
    st.divider()
    st.subheader("📈 Top 10 Communes (échantillon)")
    
    df_by_commune = df.groupby('commune_nom').agg({
        'id': 'count',
        'budget_mdh': 'sum'
    }).reset_index()
    df_by_commune.columns = ['Commune', 'Nb Projets', 'Budget (MDH)']
    df_by_commune = df_by_commune.sort_values('Budget (MDH)', ascending=False).head(10)
    
    fig = px.bar(
        df_by_commune,
        x='Commune',
        y='Budget (MDH)',
        color='Nb Projets',
        title="Top 10 Communes"
    )
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"❌ ERREUR : {str(e)}")
    st.write("**Type d'erreur :**", type(e).__name__)
    st.write("**Message complet :**")
    st.exception(e)
    
    st.divider()
    st.warning("**Que faire ?**")
    st.write("""
    1. Vérifiez que le script SQL a bien été exécuté
    2. Exécutez cette requête dans Supabase :
```sql
       SELECT COUNT(*) FROM projets_sante;
       SELECT * FROM projets_sante LIMIT 3;
```
    3. Si vous voyez des projets en SQL mais pas ici, c'est un problème de permissions RLS
    """)
