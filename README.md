# 🗺️ Application SIG Territorial - Province d'El Jadida

Application web de gestion du Système d'Information Territorial pour la Province d'El Jadida.

## 📋 Fonctionnalités

✅ **Phase actuelle (Phase 3)** :
- 🏘️ Consultation des 29 communes
- 🏗️ Visualisation des 1 103 projets de mise à niveau
- 📊 Catalogue des 125 indicateurs sectoriels
- 🔐 Authentification multi-rôles (démo)
- 📥 Export CSV des données

🚧 **En développement** :
- 🗺️ Cartographie interactive (Phase 5)
- 🎯 Module d'aide à la décision (Phase 5)
- ✍️ Saisie guidée des indicateurs (Phase 4)
- 📈 Dashboards analytics avancés (Phase 4)

## 🚀 Installation Locale

### Prérequis
- Python 3.8+
- pip

### Installation

```bash
# Cloner ou télécharger le dossier sig_app/

# Installer les dépendances
cd sig_app
pip install -r requirements.txt

# Lancer l'application
streamlit run app.py
```

L'application sera accessible sur : http://localhost:8501

## ☁️ Déploiement sur Streamlit Cloud (GRATUIT)

### Étape 1 : Préparer le code

1. Créez un compte GitHub (gratuit) : https://github.com
2. Créez un nouveau repository (ex: `sig-territorial`)
3. Uploadez le contenu du dossier `sig_app/` :
   - app.py
   - requirements.txt
   - pages/
     - 1_🏘️_Communes.py
     - 2_🏗️_Projets.py
     - 3_📊_Indicateurs.py

### Étape 2 : Déployer sur Streamlit Cloud

1. Allez sur : https://streamlit.io/cloud
2. Connectez-vous avec votre compte GitHub
3. Cliquez sur "New app"
4. Sélectionnez :
   - Repository : `votre-nom/sig-territorial`
   - Branch : `main`
   - Main file : `app.py`
5. Cliquez "Deploy"

✅ Votre application sera en ligne en 2-3 minutes !

URL : `https://votre-app.streamlit.app`

## 🔑 Configuration

Les credentials Supabase sont déjà configurés dans `app.py` :

```python
SUPABASE_URL = "https://kvmitmgsczlwzhkccvqz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

⚠️ **Pour la production** : Utilisez les secrets Streamlit Cloud :
1. Settings → Secrets
2. Ajoutez :
```toml
SUPABASE_URL = "https://kvmitmgsczlwzhkccvqz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## 📊 Structure des Données

### Base Supabase

**Tables principales** :
- `communes` (29 lignes)
- `projets_sante` (1 103 lignes)
- `referentiel_indicateurs` (125 lignes)
- `indicateurs_communes` (à remplir progressivement)

## 👥 Rôles & Permissions

### Mode Démo (actuel)
- **Admin** : Accès complet
- **Expert Sectoriel** : Consultation + validation
- **Agent Terrain** : Saisie + consultation limitée
- **Lecteur** : Consultation uniquement

### Production (à implémenter)
Authentification via Supabase Auth avec gestion des rôles dans `users_roles`

## 🛠️ Développement

### Ajouter une nouvelle page

Créez un fichier dans `pages/` :

```python
# pages/4_🆕_Nouvelle_Page.py

import streamlit as st

st.set_page_config(page_title="Titre", page_icon="🆕", layout="wide")

if 'supabase' not in st.session_state:
    st.error("Erreur connexion")
    st.stop()

supabase = st.session_state.supabase

st.title("🆕 Ma Nouvelle Page")
# ... votre code
```

### Tester localement

```bash
streamlit run app.py
```

## 📈 Prochaines Étapes

**Phase 4** : Dashboards Analytics
- Metabase intégration
- Export PDF automatique
- Rapports mensuels

**Phase 5** : SIG & IA
- Cartes Leaflet/Kepler.gl
- Scoring multicritères
- Prédictions ML

## 🆘 Support

Pour toute question ou problème :
1. Vérifiez que Supabase est accessible
2. Consultez les logs Streamlit
3. Contactez l'équipe technique

## 📄 Licence

Projet interne - Province d'El Jadida

---

**Version** : 1.0 (Phase 3)  
**Date** : Février 2025
