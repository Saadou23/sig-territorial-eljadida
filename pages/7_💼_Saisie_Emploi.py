"""
PAGE : SAISIE INDICATEURS EMPLOI
Formulaire de saisie des 51 indicateurs du secteur Emploi & Économie
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

st.set_page_config(page_title="Saisie Emploi", page_icon="💼", layout="wide")

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
# CONFIGURATION (51 indicateurs organisés en 7 catégories)
# ============================================================================

INDICATEURS_EMPLOI = {
    "Emploi & Chômage": [
        {"code": "TAUX_CHOMAGE_HOMMES", "libelle": "Taux chômage hommes", "unite": "%", "type": "percentage"},
        {"code": "TAUX_CHOMAGE_FEMMES", "libelle": "Taux chômage femmes", "unite": "%", "type": "percentage"},
        {"code": "TAUX_CHOMAGE_TOTAL", "libelle": "Taux chômage total", "unite": "%", "type": "percentage"},
        {"code": "TAUX_ACTIVITE_HOMMES", "libelle": "Taux activité hommes", "unite": "%", "type": "percentage"},
        {"code": "TAUX_ACTIVITE_FEMMES", "libelle": "Taux activité femmes", "unite": "%", "type": "percentage"},
        {"code": "TAUX_ACTIVITE_TOTAL", "libelle": "Taux activité total", "unite": "%", "type": "percentage"},
        {"code": "TAUX_CHOMAGE_REGION", "libelle": "Taux chômage région", "unite": "%", "type": "percentage"},
        {"code": "TAUX_CHOMAGE_NATIONAL", "libelle": "Taux chômage national", "unite": "%", "type": "percentage"},
    ],
    "Industrie & Zones": [
        {"code": "NB_UNITES_INDUSTRIELLES", "libelle": "Unités industrielles", "unite": "Nombre", "type": "integer"},
        {"code": "NB_EMPLOIS_INDUSTRIELS", "libelle": "Emplois industriels", "unite": "Nombre", "type": "integer"},
        {"code": "NB_ZONES_INDUSTRIELLES", "libelle": "Zones industrielles", "unite": "Nombre", "type": "integer"},
        {"code": "SUPERFICIE_ZI_HA", "libelle": "Superficie ZI", "unite": "Hectares", "type": "decimal"},
        {"code": "TAUX_OCCUPATION_ZI", "libelle": "Occupation ZI", "unite": "%", "type": "percentage"},
        {"code": "NB_ZAE", "libelle": "Zones d'activité éco", "unite": "Nombre", "type": "integer"},
        {"code": "SUPERFICIE_ZAE_HA", "libelle": "Superficie ZAE", "unite": "Hectares", "type": "decimal"},
    ],
    "Artisanat & Tourisme": [
        {"code": "NB_ZONES_ARTISANALES", "libelle": "Zones artisanales", "unite": "Nombre", "type": "integer"},
        {"code": "NB_UNITES_ARTISANALES", "libelle": "Unités artisanales", "unite": "Nombre", "type": "integer"},
        {"code": "_NB_ETABLISSEMENTS_TOURISTIQUES", "libelle": "Établissements touristiques", "unite": "Nombre", "type": "integer"},
        {"code": "CAPACITE_LITS_TOURISTIQUES", "libelle": "Capacité litière", "unite": "Lits", "type": "integer"},
    ],
    "Entreprises & Coopératives": [
        {"code": "NB_ORGANISATIONS_ESS", "libelle": "Organisations ESS", "unite": "Nombre", "type": "integer"},
        {"code": "NB_EMPLOIS_ESS", "libelle": "Emplois ESS", "unite": "Nombre", "type": "integer"},
        {"code": "MOYENNE_ENTREPRISES_CREEES_5ANS", "libelle": "Entreprises créées (moy 5 ans)", "unite": "Nombre", "type": "integer"},
        {"code": "NB_TPE", "libelle": "TPE", "unite": "Nombre", "type": "integer"},
        {"code": "NB_PME", "libelle": "PME", "unite": "Nombre", "type": "integer"},
        {"code": "NB_COOPERATIVES", "libelle": "Coopératives", "unite": "Nombre", "type": "integer"},
    ],
    "Investissements": [
        {"code": "INVESTISSEMENT_MOYEN_5ANS_DH", "libelle": "Investissement moyen 5 ans", "unite": "MAD", "type": "decimal"},
        {"code": "INVESTISSEMENT_PUBLIC_DH", "libelle": "Investissement public", "unite": "MAD", "type": "decimal"},
        {"code": "INVESTISSEMENT_PRIVE_DH", "libelle": "Investissement privé", "unite": "MAD", "type": "decimal"},
        {"code": "INVESTISSEMENT_ETRANGER_DH", "libelle": "Investissement étranger", "unite": "MAD", "type": "decimal"},
    ],
    "Équipements Commerciaux": [
        {"code": "NB_MARCHES", "libelle": "Marchés", "unite": "Nombre", "type": "integer"},
        {"code": "NB_SOUKS", "libelle": "Souks", "unite": "Nombre", "type": "integer"},
        {"code": "NB_ABATTOIRS", "libelle": "Abattoirs", "unite": "Nombre", "type": "integer"},
        {"code": "NB_EQUIPEMENTS_ECONOMIQUES_AUTRES", "libelle": "Autres équipements", "unite": "Nombre", "type": "integer"},
    ],
    "Social & Pauvreté": [
        {"code": "TAUX_PAUVRETE_URBAIN", "libelle": "Pauvreté urbain", "unite": "%", "type": "percentage"},
        {"code": "TAUX_PAUVRETE_RURAL", "libelle": "Pauvreté rural", "unite": "%", "type": "percentage"},
        {"code": "TAUX_VULNERABILITE_URBAIN", "libelle": "Vulnérabilité urbain", "unite": "%", "type": "percentage"},
        {"code": "TAUX_VULNERABILITE_RURAL", "libelle": "Vulnérabilité rural", "unite": "%", "type": "percentage"},
        {"code": "TAUX_COUVERTURE_SOCIALE", "libelle": "Couverture sociale", "unite": "%", "type": "percentage"},
        {"code": "NB_BENEFICIAIRES_AMO", "libelle": "Bénéficiaires AMO", "unite": "Nombre", "type": "integer"},
        {"code": "NB_BENEFICIAIRES_AIDES_SOCIALES", "libelle": "Bénéficiaires aides", "unite": "Nombre", "type": "integer"},
        {"code": "NB_BENEFICIAIRES_INDH", "libelle": "Bénéficiaires INDH", "unite": "Nombre", "type": "integer"},
        {"code": "NB_MENAGES_AIDES", "libelle": "Ménages aidés", "unite": "Nombre", "type": "integer"},
    ]
}

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
            .eq('axe', 'Emploi')\
            .execute()
        return {r['code_indicateur']: r for r in response.data}
    except:
        return {}

def sauvegarder_batch(commune_id, indicateurs_data, annee, source):
    """Sauvegarder plusieurs indicateurs d'un coup"""
    nb_updated = nb_inserted = 0
    
    for item in indicateurs_data:
        if item['valeur'] == 0:
            continue
            
        try:
            existing = supabase.table('indicateurs_communes')\
                .select('id')\
                .eq('commune_id', commune_id)\
                .eq('code_indicateur', item['code'])\
                .eq('annee', annee)\
                .execute()
            
            data = {
                'commune_id': commune_id,
                'axe': 'Emploi',
                'code_indicateur': item['code'],
                'valeur': item['valeur'],
                'unite': item['unite'],
                'annee': annee,
                'date_collecte': datetime.now().date().isoformat(),
                'source': source,
                'commentaire': item.get('commentaire')
            }
            
            if existing.data:
                supabase.table('indicateurs_communes').update(data).eq('id', existing.data[0]['id']).execute()
                nb_updated += 1
            else:
                supabase.table('indicateurs_communes').insert(data).execute()
                nb_inserted += 1
        except:
            pass
    
    return nb_inserted, nb_updated

# ============================================================================
# INTERFACE
# ============================================================================

st.title("💼 Saisie des Indicateurs Emploi & Économie")

# Sélection
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    communes = get_communes()
    if not communes:
        st.error("❌ Erreur")
        st.stop()
    commune_selectionnee = st.selectbox("🏘️ Commune", list(communes.keys()))
    commune_id = communes[commune_selectionnee]

with col2:
    annee = st.number_input("📅 Année", 2020, 2030, 2024)

with col3:
    source_globale = st.text_input("📄 Source", "HCP")

st.divider()

# Progression
valeurs_existantes = get_valeurs_existantes(commune_id, annee)
total_indicateurs = sum(len(inds) for inds in INDICATEURS_EMPLOI.values())
nb_remplis = len(valeurs_existantes)
progression = (nb_remplis / total_indicateurs) * 100

st.progress(progression / 100, text=f"{nb_remplis}/{total_indicateurs} indicateurs ({progression:.0f}%)")

st.divider()

# Tabs par catégorie
tabs = st.tabs(list(INDICATEURS_EMPLOI.keys()))

with st.form("form_emploi"):
    all_data = []
    
    for tab, (categorie, indicateurs) in zip(tabs, INDICATEURS_EMPLOI.items()):
        with tab:
            cols = st.columns(2)
            
            for idx, indic in enumerate(indicateurs):
                col = cols[idx % 2]
                
                with col:
                    valeur_existante = valeurs_existantes.get(indic['code'], {}).get('valeur')
                    
                    if indic['type'] == 'percentage':
                        valeur = st.number_input(
                            indic['libelle'],
                            0.0, 100.0,
                            float(valeur_existante) if valeur_existante else 0.0,
                            0.1,
                            key=indic['code']
                        )
                    elif indic['type'] == 'integer':
                        valeur = st.number_input(
                            indic['libelle'],
                            0,
                            value=int(valeur_existante) if valeur_existante else 0,
                            key=indic['code']
                        )
                    else:
                        valeur = st.number_input(
                            indic['libelle'],
                            0.0,
                            value=float(valeur_existante) if valeur_existante else 0.0,
                            key=indic['code']
                        )
                    
                    all_data.append({
                        'code': indic['code'],
                        'valeur': valeur,
                        'unite': indic['unite']
                    })
    
    submitted = st.form_submit_button("💾 Enregistrer Tout", type="primary", use_container_width=True)

if submitted:
    with st.spinner("Enregistrement..."):
        nb_inserted, nb_updated = sauvegarder_batch(commune_id, all_data, annee, source_globale)
        st.success(f"✅ {nb_inserted} nouveau(x), {nb_updated} mis à jour")
        st.rerun()
