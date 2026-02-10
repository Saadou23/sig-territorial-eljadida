"""
PAGE : SAISIE INDICATEURS SANTÉ
Formulaire de saisie des 16 indicateurs du secteur Santé
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

st.set_page_config(page_title="Saisie Santé", page_icon="🏥", layout="wide")

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

INDICATEURS_SANTE = [
    {"code": "NB_HABITANTS_PAR_ETABLISSEMENT_PROVINCIAL", "libelle": "Habitants par établissement (provincial)", "unite": "Ratio", "type": "integer", "categorie": "Couverture"},
    {"code": "NB_HABITANTS_PAR_ETABLISSEMENT_URBAIN", "libelle": "Habitants par établissement (urbain)", "unite": "Ratio", "type": "integer", "categorie": "Couverture"},
    {"code": "NB_HABITANTS_PAR_ETABLISSEMENT_RURAL", "libelle": "Habitants par établissement (rural)", "unite": "Ratio", "type": "integer", "categorie": "Couverture"},
    {"code": "NB_HABITANTS_PAR_MEDECIN_PUBLIC", "libelle": "Habitants par médecin public", "unite": "Ratio", "type": "integer", "categorie": "Ressources Humaines"},
    {"code": "NB_HABITANTS_PAR_MEDECIN_PRIVÉ", "libelle": "Habitants par médecin privé", "unite": "Ratio", "type": "integer", "categorie": "Ressources Humaines"},
    {"code": "NB_HABITANTS_PAR_INFIRMIER_PUBLIC", "libelle": "Habitants par infirmier public", "unite": "Ratio", "type": "integer", "categorie": "Ressources Humaines"},
    {"code": "NB_HABITANTS_PAR_LIT_HOSPITALIER", "libelle": "Habitants par lit hospitalier", "unite": "Ratio", "type": "integer", "categorie": "Infrastructure"},
    {"code": "TAUX_SURVEILLANCE_MERES_ENCEINTES", "libelle": "Taux surveillance mères enceintes", "unite": "%", "type": "percentage", "categorie": "Santé Maternelle"},
    {"code": "TAUX_MORTALITE_NEONATALE_PRECOCE", "libelle": "Taux mortalité néonatale précoce", "unite": "‰", "type": "decimal", "categorie": "Santé Infantile"},
    {"code": "TAUX_MORTALITE_INFANTILE", "libelle": "Taux mortalité infantile", "unite": "‰", "type": "decimal", "categorie": "Santé Infantile"},
    {"code": "TAUX_ACCOUCHEMENT_HOSPITALIER", "libelle": "Taux accouchement hospitalier", "unite": "%", "type": "percentage", "categorie": "Santé Maternelle"},
    {"code": "TAUX_MORTALITE_MATERNELLE", "libelle": "Taux mortalité maternelle", "unite": "Pour 100 000", "type": "decimal", "categorie": "Santé Maternelle"},
    {"code": "TAUX_VACCINATION_ENFANTS", "libelle": "Taux vaccination enfants", "unite": "%", "type": "percentage", "categorie": "Santé Infantile"},
    {"code": "NB_BMH", "libelle": "Nombre bureaux municipaux d'hygiène", "unite": "Nombre", "type": "integer", "categorie": "Infrastructure"},
    {"code": "NB_MORGUES", "libelle": "Nombre de morgues", "unite": "Nombre", "type": "integer", "categorie": "Infrastructure"},
    {"code": "NB_AUTRES_EQUIPEMENTS_SANTE", "libelle": "Autres équipements sanitaires", "unite": "Nombre", "type": "integer", "categorie": "Infrastructure"},
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
    """Récupérer les valeurs déjà saisies"""
    try:
        response = supabase.table('indicateurs_communes')\
            .select('*')\
            .eq('commune_id', commune_id)\
            .eq('annee', annee)\
            .eq('axe', 'Santé')\
            .execute()
        return {r['code_indicateur']: r for r in response.data}
    except:
        return {}

def sauvegarder_indicateur(commune_id, code_indicateur, valeur, unite, annee, source, commentaire):
    """Sauvegarder un indicateur"""
    try:
        existing = supabase.table('indicateurs_communes')\
            .select('id')\
            .eq('commune_id', commune_id)\
            .eq('code_indicateur', code_indicateur)\
            .eq('annee', annee)\
            .execute()
        
        data = {
            'commune_id': commune_id,
            'axe': 'Santé',
            'code_indicateur': code_indicateur,
            'valeur': valeur,
            'unite': unite,
            'annee': annee,
            'date_collecte': datetime.now().date().isoformat(),
            'source': source if source else None,
            'commentaire': commentaire if commentaire else None
        }
        
        if existing.data:
            supabase.table('indicateurs_communes').update(data).eq('id', existing.data[0]['id']).execute()
            return "updated"
        else:
            supabase.table('indicateurs_communes').insert(data).execute()
            return "inserted"
    except Exception as e:
        st.error(f"Erreur : {str(e)}")
        return None

# ============================================================================
# INTERFACE
# ============================================================================

st.title("🏥 Saisie des Indicateurs Santé")
st.markdown("Formulaire de saisie des 16 indicateurs du secteur de la santé")

# Sélection commune et année
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    communes = get_communes()
    if not communes:
        st.error("❌ Impossible de charger les communes")
        st.stop()
    
    commune_selectionnee = st.selectbox(
        "🏘️ Sélectionner une commune",
        list(communes.keys())
    )
    commune_id = communes[commune_selectionnee]

with col2:
    annee = st.number_input("📅 Année", min_value=2020, max_value=2030, value=2024)

with col3:
    source_globale = st.text_input("📄 Source", value="Ministère de la Santé")

st.divider()

# Charger valeurs existantes
valeurs_existantes = get_valeurs_existantes(commune_id, annee)

# Progression
nb_remplis = len(valeurs_existantes)
progression = (nb_remplis / len(INDICATEURS_SANTE)) * 100

col1, col2 = st.columns([3, 1])
with col1:
    st.progress(progression / 100, text=f"Progression : {nb_remplis}/{len(INDICATEURS_SANTE)} indicateurs remplis ({progression:.0f}%)")
with col2:
    if st.button("🔄 Rafraîchir", use_container_width=True):
        st.rerun()

st.divider()

# Tabs par catégorie
categories = list(set([i['categorie'] for i in INDICATEURS_SANTE]))
tabs = st.tabs(categories)

# Formulaire
with st.form("form_sante"):
    indicateurs_sauvegardes = []
    
    for tab, categorie in zip(tabs, categories):
        with tab:
            st.subheader(f"📋 {categorie}")
            
            indicateurs_categorie = [i for i in INDICATEURS_SANTE if i['categorie'] == categorie]
            
            for indic in indicateurs_categorie:
                with st.expander(
                    f"{indic['libelle']} ({indic['unite']})",
                    expanded=(indic['code'] not in valeurs_existantes)
                ):
                    col1, col2, col3 = st.columns([2, 2, 3])
                    
                    with col1:
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
                        else:
                            valeur = st.number_input(
                                f"Valeur ({indic['unite']})",
                                min_value=0.0,
                                value=float(valeur_existante) if valeur_existante else 0.0,
                                step=0.01,
                                key=f"val_{indic['code']}"
                            )
                    
                    with col2:
                        source_indic = st.text_input(
                            "Source",
                            value=valeurs_existantes.get(indic['code'], {}).get('source', source_globale),
                            key=f"src_{indic['code']}"
                        )
                    
                    with col3:
                        commentaire = st.text_area(
                            "Commentaire",
                            value=valeurs_existantes.get(indic['code'], {}).get('commentaire', ''),
                            key=f"cmt_{indic['code']}",
                            height=100
                        )
                    
                    indicateurs_sauvegardes.append({
                        'code': indic['code'],
                        'valeur': valeur,
                        'unite': indic['unite'],
                        'source': source_indic,
                        'commentaire': commentaire
                    })
    
    # Boutons
    col1, col2 = st.columns(2)
    with col1:
        submit = st.form_submit_button("💾 Enregistrer Tout", type="primary", use_container_width=True)
    with col2:
        cancel = st.form_submit_button("❌ Annuler", use_container_width=True)

if submit:
    with st.spinner("Enregistrement..."):
        nb_updated = 0
        nb_inserted = 0
        
        for indic_data in indicateurs_sauvegardes:
            if indic_data['valeur'] > 0:
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
        
        st.success(f"✅ {nb_inserted} nouveau(x), {nb_updated} mis à jour")
        st.balloons()
        st.rerun()

if cancel:
    st.rerun()

# Récapitulatif
st.divider()
st.subheader("📊 Valeurs Saisies")

if valeurs_existantes:
    df_recap = pd.DataFrame([
        {
            'Indicateur': next(i['libelle'] for i in INDICATEURS_SANTE if i['code'] == code),
            'Catégorie': next(i['categorie'] for i in INDICATEURS_SANTE if i['code'] == code),
            'Valeur': f"{v['valeur']} {v['unite']}",
            'Source': v.get('source', 'N/A'),
            'Date': v.get('date_collecte', 'N/A')
        }
        for code, v in valeurs_existantes.items()
    ])
    
    st.dataframe(df_recap, width='stretch', hide_index=True)
    
    csv = df_recap.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Exporter CSV",
        csv,
        f"indicateurs_sante_{commune_selectionnee}_{annee}.csv",
        "text/csv"
    )
else:
    st.info("ℹ️ Aucune valeur saisie")
