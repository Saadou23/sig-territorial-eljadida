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
PAGE : SAISIE INDICATEURS EAU
Formulaire de saisie des 10 indicateurs du secteur Eau
"""

import pandas as pd
from datetime import datetime
from supabase import create_client, Client

st.set_page_config(page_title="Saisie Eau", page_icon="💧", layout="wide")

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
# CONFIGURATION
# ============================================================================

INDICATEURS_EAU = [
    {"code": "PRODUCTION_EAU_POTABLE_MILLION_M3", "libelle": "Production totale eau potable", "unite": "Million m³", "type": "decimal"},
    {"code": "PRODUCTION_EAU_POTABLE_SUPERFICIELLE_MILLION_M3", "libelle": "Production eau superficielle", "unite": "Million m³", "type": "decimal"},
    {"code": "PRODUCTION_EAU_POTABLE_SOUTERRAINE_MILLION_M3", "libelle": "Production eau souterraine", "unite": "Million m³", "type": "decimal"},
    {"code": "PRODUCTION_EAU_POTABLE_NON_CONVENT_MILLION_M3", "libelle": "Production eau non conventionnelle", "unite": "Million m³", "type": "decimal"},
    {"code": "BESOINS_EAU_POTABLE_MILLION_M3", "libelle": "Besoins totaux en eau potable", "unite": "Million m³", "type": "decimal"},
    {"code": "BESOINS_EAU_POTABLE_POINTE_MILLION_M3", "libelle": "Besoins eau potable (pointe)", "unite": "Million m³", "type": "decimal"},
    {"code": "NB_STEP", "libelle": "Nombre de stations d'épuration", "unite": "Nombre", "type": "integer"},
    {"code": "TAUX_EAUX_REUSEES", "libelle": "Taux des eaux usées traitées/réutilisées", "unite": "%", "type": "percentage"},
    {"code": "TAUX_BRANCHEMENT_INDIVIDUEL_EAU_POTABLE", "libelle": "Taux branchement individuel AEP", "unite": "%", "type": "percentage"},
    {"code": "TAUX_POPULATION_NON_DESSERVIE", "libelle": "Taux population non desservie", "unite": "%", "type": "percentage"},
]

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def get_communes():
    """Récupérer la liste des communes"""
    try:
        response = supabase.table('communes').select('id, nom').order('nom').execute()
        return {c['nom']: c['id'] for c in response.data}
    except:
        return {}

def get_valeurs_existantes(commune_id, annee):
    """Récupérer les valeurs déjà saisies pour une commune/année"""
    try:
        response = supabase.table('indicateurs_communes')\
            .select('*')\
            .eq('commune_id', commune_id)\
            .eq('annee', annee)\
            .eq('axe', 'Eau')\
            .execute()
        return {r['code_indicateur']: r for r in response.data}
    except:
        return {}

def sauvegarder_indicateur(commune_id, code_indicateur, valeur, unite, annee, source, commentaire):
    """Sauvegarder un indicateur"""
    try:
        # Vérifier si existe déjà
        existing = supabase.table('indicateurs_communes')\
            .select('id')\
            .eq('commune_id', commune_id)\
            .eq('code_indicateur', code_indicateur)\
            .eq('annee', annee)\
            .execute()
        
        data = {
            'commune_id': commune_id,
            'axe': 'Eau',
            'code_indicateur': code_indicateur,
            'valeur': valeur,
            'unite': unite,
            'annee': annee,
            'date_collecte': datetime.now().date().isoformat(),
            'source': source if source else None,
            'commentaire': commentaire if commentaire else None
        }
        
        if existing.data:
            # Update
            supabase.table('indicateurs_communes').update(data).eq('id', existing.data[0]['id']).execute()
            return "updated"
        else:
            # Insert
            supabase.table('indicateurs_communes').insert(data).execute()
            return "inserted"
    except Exception as e:
        st.error(f"Erreur sauvegarde : {str(e)}")
        return None

# ============================================================================
# INTERFACE
# ============================================================================

st.title("💧 Saisie des Indicateurs Eau")
st.markdown("Formulaire de saisie des 10 indicateurs du secteur de l'eau")

# Sélection commune et année
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    communes = get_communes()
    if not communes:
        st.error("❌ Impossible de charger les communes")
        st.stop()
    
    commune_selectionnee = st.selectbox(
        "🏘️ Sélectionner une commune",
        list(communes.keys()),
        help="Choisissez la commune pour laquelle saisir les indicateurs"
    )
    commune_id = communes[commune_selectionnee]

with col2:
    annee = st.number_input(
        "📅 Année",
        min_value=2020,
        max_value=2030,
        value=2024,
        help="Année de référence des données"
    )

with col3:
    source_globale = st.text_input(
        "📄 Source",
        value="ONEE",
        help="Source des données (ONEE, Commune, etc.)"
    )

st.divider()

# Charger les valeurs existantes
valeurs_existantes = get_valeurs_existantes(commune_id, annee)

# Progression
nb_remplis = len(valeurs_existantes)
progression = (nb_remplis / len(INDICATEURS_EAU)) * 100

col1, col2 = st.columns([3, 1])
with col1:
    st.progress(progression / 100, text=f"Progression : {nb_remplis}/{len(INDICATEURS_EAU)} indicateurs remplis ({progression:.0f}%)")
with col2:
    if st.button("🔄 Rafraîchir", use_container_width=True):
        st.rerun()

st.divider()

# Formulaire de saisie
st.subheader("📝 Saisie des Indicateurs")

# Organiser en accordéon
with st.form("form_eau"):
    indicateurs_sauvegardes = []
    
    for idx, indic in enumerate(INDICATEURS_EAU):
        with st.expander(
            f"{idx+1}. {indic['libelle']} ({indic['unite']})",
            expanded=(indic['code'] not in valeurs_existantes)
        ):
            col1, col2, col3 = st.columns([2, 2, 3])
            
            with col1:
                # Récupérer valeur existante
                valeur_existante = valeurs_existantes.get(indic['code'], {}).get('valeur')
                
                if indic['type'] == 'percentage':
                    valeur = st.number_input(
                        "Valeur (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(valeur_existante) if valeur_existante else 0.0,
                        step=0.1,
                        key=f"val_{indic['code']}"
                    )
                elif indic['type'] == 'integer':
                    valeur = st.number_input(
                        "Valeur",
                        min_value=0,
                        value=int(valeur_existante) if valeur_existante else 0,
                        step=1,
                        key=f"val_{indic['code']}"
                    )
                else:  # decimal
                    valeur = st.number_input(
                        f"Valeur ({indic['unite']})",
                        min_value=0.0,
                        value=float(valeur_existante) if valeur_existante else 0.0,
                        step=0.01,
                        key=f"val_{indic['code']}"
                    )
            
            with col2:
                source_indic = st.text_input(
                    "Source (optionnel)",
                    value=valeurs_existantes.get(indic['code'], {}).get('source', source_globale),
                    key=f"src_{indic['code']}"
                )
            
            with col3:
                commentaire = st.text_area(
                    "Commentaire (optionnel)",
                    value=valeurs_existantes.get(indic['code'], {}).get('commentaire', ''),
                    key=f"cmt_{indic['code']}",
                    height=100
                )
            
            # Stocker pour sauvegarde
            indicateurs_sauvegardes.append({
                'code': indic['code'],
                'valeur': valeur,
                'unite': indic['unite'],
                'source': source_indic,
                'commentaire': commentaire
            })
    
    # Boutons
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        submit = st.form_submit_button("💾 Enregistrer Tout", type="primary", use_container_width=True)
    
    with col2:
        cancel = st.form_submit_button("❌ Annuler", use_container_width=True)

if submit:
    with st.spinner("Enregistrement en cours..."):
        nb_updated = 0
        nb_inserted = 0
        
        for indic_data in indicateurs_sauvegardes:
            if indic_data['valeur'] > 0:  # Ne sauvegarder que si valeur > 0
                result = sauvegarder_indicateur(
                    commune_id,
                    indic_data['code'],
                    indic_data['valeur'],
                    indic_data['unite'],
                    annee,
                    indic_data['source'],
                    indic_data['commentaire']
                )
                
                if result == "updated":
                    nb_updated += 1
                elif result == "inserted":
                    nb_inserted += 1
        
        st.success(f"✅ Enregistrement réussi ! {nb_inserted} nouveau(x), {nb_updated} mis à jour")
        st.balloons()
        st.rerun()

if cancel:
    st.rerun()

# Tableau récapitulatif
st.divider()
st.subheader("📊 Récapitulatif des Valeurs Saisies")

if valeurs_existantes:
    df_recap = pd.DataFrame([
        {
            'Indicateur': next(i['libelle'] for i in INDICATEURS_EAU if i['code'] == code),
            'Valeur': f"{v['valeur']} {v['unite']}",
            'Source': v.get('source', 'N/A'),
            'Date saisie': v.get('date_collecte', 'N/A')
        }
        for code, v in valeurs_existantes.items()
    ])
    
    st.dataframe(df_recap, width='stretch', hide_index=True)
else:
    st.info("ℹ️ Aucune valeur saisie pour cette commune/année")

# Export
st.divider()
if valeurs_existantes:
    csv = df_recap.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Exporter en CSV",
        csv,
        f"indicateurs_eau_{commune_selectionnee}_{annee}.csv",
        "text/csv",
        use_container_width=False
    )
