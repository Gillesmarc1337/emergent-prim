# 📊 Sales Analytics Dashboard - Documentation Complète

## Vue d'ensemble

Application full-stack de tableau de bord analytique pour le suivi des performances commerciales, développée avec **FastAPI (Python)** pour le backend et **React** pour le frontend. Le système supporte plusieurs vues organisationnelles avec des targets personnalisés et des données isolées.

---

## 🏗️ Architecture Technique

### Stack Technologique

**Backend:**
- **FastAPI** - Framework web Python moderne et performant  
- **Motor** - Driver MongoDB asynchrone
- **Pandas** - Manipulation et analyse de données
- **Python 3.10+**

**Frontend:**
- **React 18** - Bibliothèque UI
- **TailwindCSS** - Framework CSS utility-first
- **Recharts** - Graphiques et visualisations
- **React Router** - Navigation
- **Axios** - Requêtes HTTP

**Base de données:**
- **MongoDB** - Base NoSQL pour flexibilité et scalabilité

---

## 📁 Structure du Projet

```
/app/
├── backend/
│   ├── server.py                    # API principale avec tous les endpoints
│   ├── auth.py                      # Authentification Google OAuth + Demo
│   ├── setup_multi_views.py         # Script de seed pour vues multi-organisation
│   ├── upload_view_data.py          # Script d'upload Google Sheets par vue
│   ├── requirements.txt             # Dépendances Python
│   └── .env                         # Variables d'environnement backend
│
├── frontend/
│   ├── src/
│   │   ├── App.js                   # Composant principal avec dashboard
│   │   ├── index.js                 # Point d'entrée React
│   │   ├── components/
│   │   │   ├── LoginPage.jsx       # Page de connexion (OAuth + Demo)
│   │   │   ├── Header.jsx          # En-tête avec sélecteur de vue
│   │   │   ├── AdminTargetsPage.jsx # Back office de configuration targets
│   │   │   ├── GoogleSheetsUpload.jsx # Upload de données Google Sheets
│   │   │   ├── DateRangePicker.jsx # Sélecteur de plage de dates
│   │   │   └── ui/                 # Composants UI shadcn/ui
│   │   ├── contexts/
│   │   │   └── AuthContext.jsx     # Contexte d'authentification et vues
│   │   └── lib/
│   │       └── utils.js            # Utilitaires (ex: cn pour classes)
│   ├── public/
│   ├── package.json                # Dépendances npm
│   ├── tailwind.config.js          # Configuration Tailwind
│   └── .env                        # Variables d'environnement frontend
│
└── README.md                        # Ce fichier
```

---

## 🔐 Système d'Authentification

### Utilisateurs et Permissions

| Email | Rôle | Vues Accessibles | Permissions |
|-------|------|------------------|-------------|
| remi@primelis.com | super_admin | Toutes | Admin targets + Upload |
| philippe@primelis.com | super_admin | Toutes | Admin targets + Upload |
| asher@primelis.com | super_admin | Toutes | Admin targets + Upload |
| oren@primelis.com | viewer | Signal | Upload Signal |
| maxime.toubia@primelis.com | viewer | Full Funnel | Upload Full Funnel |
| coralie.truffy@primelis.com | viewer | Market | Upload Market |
| demo@primelis.com | viewer | Toutes | Lecture seule |

---

## 🎯 Système Multi-View

### Vues Disponibles

**Organic** (Default): Vue originale avec données historiques  
**Full Funnel** (Maxime): Pipeline complet sales - Target H2 2025: 4.5M  
**Signal** (Oren): Focus acquisition - Target H2 2025: 1.7M  
**Market** (Coralie): Focus marché - Target H2 2025: 1.7M  
**Master** (Philippe/Remi/Asher): Agrégation des 3 vues - Target H2 2025: 7.9M

### Isolation des Données

Chaque vue a:
- Sa propre collection MongoDB (`sales_records_{view}`)
- Ses propres targets configurables
- Son propre Google Sheet pour upload

La vue Master agrège automatiquement Signal + Full Funnel + Market.

---

## 🚀 Démarrage Rapide

### Backend
```bash
cd /app/backend
pip install -r requirements.txt
python setup_multi_views.py  # Seed des données
sudo supervisorctl restart backend
```

### Frontend  
```bash
cd /app/frontend
yarn install
yarn build
sudo supervisorctl restart frontend
```

### Accès
- Dashboard: https://your-domain.com/
- Admin: https://your-domain.com/admin/targets (super_admin seulement)
- Login: Google OAuth ou Demo Access

---

## 📊 Features Principales

### Dashboard (6 Onglets)
1. **Dashboard**: Vue d'ensemble revenue, pipe, deals actifs
2. **Meetings Generation**: Suivi meetings par source (Intro, Inbound, Outbound, Referrals)
3. **Pipeline Metrics**: Métriques pipeline YTD avec targets
4. **Projections**: Prévisions closing 14 jours, 30-60 jours, 60-90 jours
5. **Upsell & Renew**: Performance upsells et partners
6. **Data Management**: Upload Google Sheets et configuration

### Back Office Admin
- Configuration targets pour 6 sections
- Tous les targets sont mensuels et se multiplient selon la période
- Interface par onglets (une vue = un onglet)
- Sauvegarde temps réel dans MongoDB

---

## 🔌 API Endpoints Principaux

**Authentication:**
- POST `/api/auth/google-login` - Login Google OAuth
- POST `/api/auth/demo-login` - Login demo
- POST `/api/auth/logout` - Déconnexion

**Views:**
- GET `/api/views/user/accessible` - Vues accessibles à l'user
- GET `/api/views/{view_id}/config` - Config d'une vue
- PUT `/api/admin/views/{view_id}/targets` - Update targets (admin)

**Data:**
- POST `/api/upload-data?view_id={id}` - Upload CSV
- POST `/api/upload-google-sheets?view_id={id}` - Upload Google Sheets

**Analytics:**
- GET `/api/analytics/monthly?view_id={id}` - Analytics mois
- GET `/api/analytics/yearly?view_id={id}` - Analytics année
- GET `/api/analytics/dashboard?view_id={id}` - Dashboard principal
- GET `/api/analytics/upsell-renewals?view_id={id}` - Upsells

**Projections:**
- GET `/api/projections/hot-deals?view_id={id}` - Deals chauds (Legals)
- GET `/api/projections/hot-leads?view_id={id}` - Leads chauds
- GET `/api/projections/ae-pipeline-breakdown?view_id={id}` - Pipeline par AE

---

## 🐛 Troubleshooting

**Backend ne démarre pas:**
```bash
tail -50 /var/log/supervisor/backend.err.log
```

**Frontend erreurs:**
```bash
tail -50 /var/log/supervisor/frontend.err.log
```

**Redémarrage:**
```bash
sudo supervisorctl restart all
```

**Vérifier MongoDB:**
```bash
mongosh
use sales_analytics
db.views.find()
db.sales_records_fullfunnel.count()
```

---

## 📈 Roadmap

**Court terme:**
- [ ] Sync automatique targets depuis Google Sheets (colonnes Y et AL)
- [ ] Historique modifications targets
- [ ] Export/Import configurations

**Moyen terme:**
- [ ] Webhooks (Slack, Teams)
- [ ] Rapports automatiques par email
- [ ] Mobile app

**Long terme:**
- [ ] Multi-tenant SaaS
- [ ] AI Assistant pour insights
- [ ] Prédictions ML

---

## 📄 Licence

Propriétaire - Primelis © 2025

**Développé avec ❤️ par Emergent AI**
