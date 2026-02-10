"""
PAGE : SUIVI DE LA SAISIE
Tableau de bord de suivi global de la saisie des indicateurs
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

st.set_page_config(page_title="Suivi Saisie", page_icon="📈", layout="wide")

# ============================================================================
# INITIALISATION SUPABASE
# ============================================================================

@st.cache_resource
def init_supabase() -> Client:
    SUPABASE_URL = "https://kvmitmgsczlwzhkccvqz.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt2bWl0bWdzY3psd3poa2NjdnF6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA2NjUyMDIsImV4cCI6MjA4NjI0MTIwMn0.xvKizf9RlSv8wxonHAlPw5_hsh3bKSDlFLyOwtI7kxg"
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# ============================================================================
# CONFIGURATION
# ============================================================================

NB_INDICATEURS_PAR_AXE = {
    'Eau': 10,
    'Santé': 16,
    'Éducation': 36,
    'Emploi': 51
}

NB_COMMUNES = 29

# ============================================================================
# FONCTIONS
# ============================================================================

@st.cache_data(ttl=60)
def get_stats_globales():
    """Récupérer les statistiques globales de saisie"""
    try:
        response = supabase.table('indicateurs_communes').select('*').execute()
        return pd.DataFrame(response.data)
    except:
        return pd.DataFrame()

def get_communes():
    try:
        response = supabase.table('communes').select('id, nom').order('nom').execute()
        return pd.DataFrame(response.data)
    except:
        return pd.DataFrame()

# ============================================================================
# INTERFACE
# ============================================================================

st.title("📈 Suivi de la Saisie des Indicateurs")
st.markdown("Tableau de bord de progression de la saisie par axe, commune et année")

# Charger les données
df_saisies = get_stats_globales()
df_communes = get_communes()

if df_saisies.empty:
    st.warning("⚠️ Aucune donnée saisie pour le moment")
    st.info("""
    ### 🚀 Pour commencer la saisie :
    
    Utilisez les pages suivantes dans le menu latéral :
    - 💧 **Saisie Eau** (10 indicateurs)
    - 🏥 **Saisie Santé** (16 indicateurs)
    - 🎓 **Saisie Éducation** (36 indicateurs)
    - 💼 **Saisie Emploi** (51 indicateurs)
    """)
    st.stop()

# KPI Globaux
st.subheader("📊 Vue d'Ensemble")

total_theorique = sum(NB_INDICATEURS_PAR_AXE.values()) * NB_COMMUNES
total_saisi = len(df_saisies)
taux_global = (total_saisi / total_theorique) * 100 if total_theorique > 0 else 0

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📝 Valeurs Saisies", f"{total_saisi:,}")

with col2:
    st.metric("🎯 Objectif Total", f"{total_theorique:,}")

with col3:
    st.metric("📈 Taux de Remplissage", f"{taux_global:.1f}%")

with col4:
    nb_communes_actives = df_saisies['commune_id'].nunique()
    st.metric("🏘️ Communes Actives", f"{nb_communes_actives}/{NB_COMMUNES}")

st.divider()

# Progression par axe
st.subheader("📊 Progression par Axe Sectoriel")

df_by_axe = df_saisies.groupby('axe').size().reset_index(name='nb_saisies')

# Calculer les objectifs
objectifs = []
for axe in NB_INDICATEURS_PAR_AXE.keys():
    nb_saisi = df_by_axe[df_by_axe['axe'] == axe]['nb_saisies'].values
    nb_saisi = nb_saisi[0] if len(nb_saisi) > 0 else 0
    objectif = NB_INDICATEURS_PAR_AXE[axe] * NB_COMMUNES
    taux = (nb_saisi / objectif * 100) if objectif > 0 else 0
    
    objectifs.append({
        'Axe': axe,
        'Saisies': nb_saisi,
        'Objectif': objectif,
        'Taux (%)': round(taux, 1)
    })

df_objectifs = pd.DataFrame(objectifs)

col1, col2 = st.columns([2, 1])

with col1:
    fig = px.bar(
        df_objectifs,
        x='Axe',
        y=['Saisies', 'Objectif'],
        title="Saisies vs Objectifs par Axe",
        barmode='group',
        color_discrete_sequence=['#4CAF50', '#E0E0E0']
    )
    st.plotly_chart(fig, width='stretch')

with col2:
    st.dataframe(
        df_objectifs,
        width='stretch',
        hide_index=True,
        column_config={
            "Taux (%)": st.column_config.ProgressColumn(
                "Taux",
                format="%.1f%%",
                min_value=0,
                max_value=100
            )
        }
    )

st.divider()

# Progression par commune
st.subheader("🏘️ Progression par Commune")

# Filtres
col1, col2 = st.columns(2)

with col1:
    axe_filtre = st.selectbox(
        "Filtrer par axe",
        ["Tous"] + list(NB_INDICATEURS_PAR_AXE.keys())
    )

with col2:
    annee_filtre = st.selectbox(
        "Filtrer par année",
        ["Toutes"] + sorted(df_saisies['annee'].unique().tolist(), reverse=True)
    )

# Appliquer filtres
df_filtered = df_saisies.copy()

if axe_filtre != "Tous":
    df_filtered = df_filtered[df_filtered['axe'] == axe_filtre]

if annee_filtre != "Toutes":
    df_filtered = df_filtered[df_filtered['annee'] == annee_filtre]

# Grouper par commune
df_by_commune = df_filtered.groupby('commune_id').size().reset_index(name='nb_indicateurs')

# Joindre avec noms communes
df_by_commune = df_by_commune.merge(df_communes, left_on='commune_id', right_on='id', how='left')

# Calculer objectif par commune
if axe_filtre == "Tous":
    objectif_commune = sum(NB_INDICATEURS_PAR_AXE.values())
else:
    objectif_commune = NB_INDICATEURS_PAR_AXE[axe_filtre]

df_by_commune['taux'] = (df_by_commune['nb_indicateurs'] / objectif_commune * 100).round(1)
df_by_commune = df_by_commune.sort_values('taux', ascending=False)

# Top 10 communes
col1, col2 = st.columns([2, 1])

with col1:
    fig = px.bar(
        df_by_commune.head(10),
        x='nom',
        y='nb_indicateurs',
        title="Top 10 Communes (nb indicateurs saisis)",
        color='taux',
        color_continuous_scale='RdYlGn'
    )
    st.plotly_chart(fig, width='stretch')

with col2:
    st.dataframe(
        df_by_commune[['nom', 'nb_indicateurs', 'taux']].head(10),
        width='stretch',
        hide_index=True,
        column_config={
            "nom": "Commune",
            "nb_indicateurs": "Indicateurs",
            "taux": st.column_config.ProgressColumn(
                "Taux (%)",
                format="%.1f%%",
                min_value=0,
                max_value=100
            )
        }
    )

# Tableau complet
st.divider()
st.subheader("📋 Tableau Détaillé")

with st.expander("Voir toutes les communes"):
    st.dataframe(
        df_by_commune[['nom', 'nb_indicateurs', 'taux']],
        width='stretch',
        hide_index=True,
        column_config={
            "nom": "Commune",
            "nb_indicateurs": "Nb Indicateurs",
            "taux": st.column_config.ProgressColumn(
                "Taux (%)",
                format="%.1f%%",
                min_value=0,
                max_value=100
            )
        }
    )

# Timeline
st.divider()
st.subheader("📅 Évolution Temporelle")

df_timeline = df_saisies.groupby(['date_collecte', 'axe']).size().reset_index(name='nb_saisies')
df_timeline['date_collecte'] = pd.to_datetime(df_timeline['date_collecte'])
df_timeline = df_timeline.sort_values('date_collecte')

fig = px.line(
    df_timeline,
    x='date_collecte',
    y='nb_saisies',
    color='axe',
    title="Évolution du nombre de saisies par jour",
    labels={'date_collecte': 'Date', 'nb_saisies': 'Nombre de saisies'}
)
st.plotly_chart(fig, width='stretch')

# Export
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    csv_communes = df_by_commune.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Export Communes (CSV)",
        csv_communes,
        "suivi_communes.csv",
        "text/csv"
    )

with col2:
    csv_axes = df_objectifs.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Export Axes (CSV)",
        csv_axes,
        "suivi_axes.csv",
        "text/csv"
    )

with col3:
    csv_complet = df_saisies.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Export Complet (CSV)",
        csv_complet,
        "donnees_completes.csv",
        "text/csv"
    )

# Actions recommandées
st.divider()
st.subheader("💡 Actions Recommandées")

# Communes sans saisie
communes_sans_saisie = set(df_communes['nom']) - set(df_by_commune['nom'])

if communes_sans_saisie:
    st.warning(f"⚠️ **{len(communes_sans_saisie)} commune(s) sans aucune saisie** : {', '.join(sorted(list(communes_sans_saisie))[:5])}...")

# Axes peu remplis
axes_faibles = df_objectifs[df_objectifs['Taux (%)'] < 20]
if not axes_faibles.empty:
    st.info(f"ℹ️ **Axes nécessitant attention** : {', '.join(axes_faibles['Axe'].tolist())}")

# Bouton rafraîchir
if st.button("🔄 Actualiser les Données", type="primary"):
    st.cache_data.clear()
    st.rerun()
