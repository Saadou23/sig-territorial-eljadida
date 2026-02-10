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
PAGE : SAISIE INDICATEURS ÉDUCATION
Formulaire de saisie des 36 indicateurs du secteur Éducation
"""

import pandas as pd
from datetime import datetime
from supabase import create_client, Client

st.set_page_config(page_title="Saisie Éducation", page_icon="🎓", layout="wide")

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

INDICATEURS_EDUCATION = [
    # Analphabétisme
    {"code": "TAUX_ANALPHABETISME_TOTAL", "libelle": "Taux analphabétisme total", "unite": "%", "type": "percentage", "categorie": "Analphabétisme"},
    {"code": "TAUX_ANALPHABETISME_HOMMES", "libelle": "Taux analphabétisme hommes", "unite": "%", "type": "percentage", "categorie": "Analphabétisme"},
    {"code": "TAUX_ANALPHABETISME_FEMMES", "libelle": "Taux analphabétisme femmes", "unite": "%", "type": "percentage", "categorie": "Analphabétisme"},
    {"code": "TAUX_ANALPHABETISME_URBAIN", "libelle": "Taux analphabétisme urbain", "unite": "%", "type": "percentage", "categorie": "Analphabétisme"},
    {"code": "TAUX_ANALPHABETISME_RURAL", "libelle": "Taux analphabétisme rural", "unite": "%", "type": "percentage", "categorie": "Analphabétisme"},
    
    # Scolarisation
    {"code": "TAUX_SCOLARISATION_PRIMAIRE_URBAIN", "libelle": "Scolarisation primaire (urbain)", "unite": "%", "type": "percentage", "categorie": "Scolarisation"},
    {"code": "TAUX_SCOLARISATION_PRIMAIRE_RURAL", "libelle": "Scolarisation primaire (rural)", "unite": "%", "type": "percentage", "categorie": "Scolarisation"},
    {"code": "TAUX_SCOLARISATION_PRIMAIRE_GARCONS", "libelle": "Scolarisation primaire garçons", "unite": "%", "type": "percentage", "categorie": "Scolarisation"},
    {"code": "TAUX_SCOLARISATION_PRIMAIRE_FILLES", "libelle": "Scolarisation primaire filles", "unite": "%", "type": "percentage", "categorie": "Scolarisation"},
    
    # Effectifs
    {"code": "EFFECTIF_ENFANTS_PRESCOLAIRES_MILLIERS", "libelle": "Effectif préscolaire", "unite": "Milliers", "type": "decimal", "categorie": "Effectifs"},
    {"code": "EFFECTIF_SCOLARISE_TOTAL_MILLIERS", "libelle": "Effectif total scolarisé", "unite": "Milliers", "type": "decimal", "categorie": "Effectifs"},
    {"code": "EFFECTIF_PRIMAIRE_MILLIERS", "libelle": "Effectif primaire", "unite": "Milliers", "type": "decimal", "categorie": "Effectifs"},
    {"code": "EFFECTIF_SECONDAIRE_COLLÉGIAL_MILLIERS", "libelle": "Effectif collège", "unite": "Milliers", "type": "decimal", "categorie": "Effectifs"},
    {"code": "EFFECTIF_SECONDAIRE_QUALIFIANT_MILLIERS", "libelle": "Effectif lycée", "unite": "Milliers", "type": "decimal", "categorie": "Effectifs"},
    
    # Féminisation
    {"code": "TAUX_FEMINISATION_TOTAL", "libelle": "Féminisation total", "unite": "%", "type": "percentage", "categorie": "Féminisation"},
    {"code": "TAUX_FEMINISATION_PRIMAIRE", "libelle": "Féminisation primaire", "unite": "%", "type": "percentage", "categorie": "Féminisation"},
    {"code": "TAUX_FEMINISATION_SECONDAIRE_COLLÉGIAL", "libelle": "Féminisation collège", "unite": "%", "type": "percentage", "categorie": "Féminisation"},
    {"code": "TAUX_FEMINISATION_SECONDAIRE_QUALIFIANT", "libelle": "Féminisation lycée", "unite": "%", "type": "percentage", "categorie": "Féminisation"},
    
    # Ratios enseignants
    {"code": "NB_ELEVES_PAR_ENSEIGNANT_PRIMAIRE", "libelle": "Élèves/enseignant primaire", "unite": "Ratio", "type": "integer", "categorie": "Encadrement"},
    {"code": "NB_ELEVES_PAR_ENSEIGNANT_SECONDAIRE_COLLÉGIAL", "libelle": "Élèves/enseignant collège", "unite": "Ratio", "type": "integer", "categorie": "Encadrement"},
    {"code": "NB_ELEVES_PAR_ENSEIGNANT_SECONDAIRE_QUALIFIANT", "libelle": "Élèves/enseignant lycée", "unite": "Ratio", "type": "integer", "categorie": "Encadrement"},
    
    # Encombrement
    {"code": "TAUX_ENCOMBREMENT_PRIMAIRE", "libelle": "Encombrement primaire", "unite": "%", "type": "percentage", "categorie": "Infrastructure"},
    {"code": "TAUX_ENCOMBREMENT_SECONDAIRE_COLLÉGIAL", "libelle": "Encombrement collège", "unite": "%", "type": "percentage", "categorie": "Infrastructure"},
    {"code": "TAUX_ENCOMBREMENT_SECONDAIRE_QUALIFIANT", "libelle": "Encombrement lycée", "unite": "%", "type": "percentage", "categorie": "Infrastructure"},
    {"code": "NB_CLASSES_MULTINIVEAUX", "libelle": "Classes multiniveaux", "unite": "Nombre", "type": "integer", "categorie": "Infrastructure"},
    {"code": "NB_SALLES_CLASSES_PREFABRIQUEES", "libelle": "Salles préfabriquées", "unite": "Nombre", "type": "integer", "categorie": "Infrastructure"},
    
    # Services
    {"code": "NB_BENEFICIAIRES_TRANSPORT_RURAL", "libelle": "Bénéficiaires transport rural", "unite": "Nombre", "type": "integer", "categorie": "Services"},
    {"code": "NB_BENEFICIAIRES_TRANSPORT_URBAIN", "libelle": "Bénéficiaires transport urbain", "unite": "Nombre", "type": "integer", "categorie": "Services"},
    {"code": "TAUX_RACCORDEMENT_ASSAINISSEMENT_RURAL", "libelle": "Assainissement écoles rurales", "unite": "%", "type": "percentage", "categorie": "Services"},
    {"code": "TAUX_RACCORDEMENT_EAU_RURAL", "libelle": "Eau écoles rurales", "unite": "%", "type": "percentage", "categorie": "Services"},
    {"code": "TAUX_ELECTRIFICATION_ETABLISSEMENTS_RURAUX", "libelle": "Électrification écoles rurales", "unite": "%", "type": "percentage", "categorie": "Services"},
    
    # Abandon
    {"code": "TAUX_ABANDON_TOTAL", "libelle": "Abandon scolaire total", "unite": "%", "type": "percentage", "categorie": "Abandon"},
    {"code": "TAUX_ABANDON_URBAIN", "libelle": "Abandon urbain", "unite": "%", "type": "percentage", "categorie": "Abandon"},
    {"code": "TAUX_ABANDON_RURAL", "libelle": "Abandon rural", "unite": "%", "type": "percentage", "categorie": "Abandon"},
    {"code": "TAUX_ABANDON_FILLES", "libelle": "Abandon filles", "unite": "%", "type": "percentage", "categorie": "Abandon"},
    {"code": "TAUX_ABANDON_GARCONS", "libelle": "Abandon garçons", "unite": "%", "type": "percentage", "categorie": "Abandon"},
]

# ============================================================================
# FONCTIONS
# ============================================================================

def get_communes():
    try:
        response = supabase.table('communes').select('id, nom').order('nom').execute()
        return {c['nom']: c['id'] for c in response.data}
    except:
        return {}

def get_valeurs_existantes(commune_id, annee):
    try:
        response = supabase.table('indicateurs_communes')\
            .select('*')\
            .eq('commune_id', commune_id)\
            .eq('annee', annee)\
            .eq('axe', 'Éducation')\
            .execute()
        return {r['code_indicateur']: r for r in response.data}
    except:
        return {}

def sauvegarder_indicateur(commune_id, code_indicateur, valeur, unite, annee, source, commentaire):
    try:
        existing = supabase.table('indicateurs_communes')\
            .select('id')\
            .eq('commune_id', commune_id)\
            .eq('code_indicateur', code_indicateur)\
            .eq('annee', annee)\
            .execute()
        
        data = {
            'commune_id': commune_id,
            'axe': 'Éducation',
            'code_indicateur': code_indicateur,
            'valeur': valeur,
            'unite': unite,
            'annee': annee,
            'date_collecte': datetime.now().date().isoformat(),
            'source': source,
            'commentaire': commentaire
        }
        
        if existing.data:
            supabase.table('indicateurs_communes').update(data).eq('id', existing.data[0]['id']).execute()
            return "updated"
        else:
            supabase.table('indicateurs_communes').insert(data).execute()
            return "inserted"
    except:
        return None

# ============================================================================
# INTERFACE
# ============================================================================

st.title("🎓 Saisie des Indicateurs Éducation")

# Sélection
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    communes = get_communes()
    if not communes:
        st.error("❌ Erreur communes")
        st.stop()
    commune_selectionnee = st.selectbox("🏘️ Commune", list(communes.keys()))
    commune_id = communes[commune_selectionnee]

with col2:
    annee = st.number_input("📅 Année", 2020, 2030, 2024)

with col3:
    source_globale = st.text_input("📄 Source", "AREF")

st.divider()

valeurs_existantes = get_valeurs_existantes(commune_id, annee)
nb_remplis = len(valeurs_existantes)
progression = (nb_remplis / len(INDICATEURS_EDUCATION)) * 100

st.progress(progression / 100, text=f"{nb_remplis}/{len(INDICATEURS_EDUCATION)} indicateurs ({progression:.0f}%)")

st.divider()

# Tabs par catégorie
categories = list(dict.fromkeys([i['categorie'] for i in INDICATEURS_EDUCATION]))
tabs = st.tabs(categories)

with st.form("form_education"):
    indicateurs_sauvegardes = []
    
    for tab, categorie in zip(tabs, categories):
        with tab:
            indicateurs_cat = [i for i in INDICATEURS_EDUCATION if i['categorie'] == categorie]
            
            for indic in indicateurs_cat:
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    valeur_existante = valeurs_existantes.get(indic['code'], {}).get('valeur')
                    
                    if indic['type'] == 'percentage':
                        valeur = st.number_input(
                            indic['libelle'],
                            0.0, 100.0,
                            float(valeur_existante) if valeur_existante else 0.0,
                            0.1,
                            key=f"v_{indic['code']}"
                        )
                    elif indic['type'] == 'integer':
                        valeur = st.number_input(
                            indic['libelle'],
                            0,
                            value=int(valeur_existante) if valeur_existante else 0,
                            key=f"v_{indic['code']}"
                        )
                    else:
                        valeur = st.number_input(
                            indic['libelle'],
                            min_value=0.0,
                            value=float(valeur_existante) if valeur_existante else 0.0,
                            step=0.01,
                            key=f"v_{indic['code']}"
                        )
                
                with col2:
                    commentaire = st.text_input(
                        "Commentaire",
                        valeurs_existantes.get(indic['code'], {}).get('commentaire', ''),
                        key=f"c_{indic['code']}"
                    )
                
                indicateurs_sauvegardes.append({
                    'code': indic['code'],
                    'valeur': valeur,
                    'unite': indic['unite'],
                    'source': source_globale,
                    'commentaire': commentaire
                })
    
    submitted = st.form_submit_button("💾 Enregistrer", type="primary", use_container_width=True)

if submitted:
    nb_updated = nb_inserted = 0
    
    for item in indicateurs_sauvegardes:
        if item['valeur'] > 0:
            result = sauvegarder_indicateur(
                commune_id, item['code'], item['valeur'],
                item['unite'], annee, item['source'], item['commentaire']
            )
            if result == "updated": nb_updated += 1
            elif result == "inserted": nb_inserted += 1
    
    st.success(f"✅ {nb_inserted} nouveau(x), {nb_updated} mis à jour")
    st.rerun()
