# 📊 Sales Analytics Dashboard - Documentation Complète

## Vue d'ensemble

Application full-stack de tableau de bord analytique pour le suivi des performances commerciales avec multi-tenancy, développée avec **FastAPI (Python)** pour le backend et **React** pour le frontend. Le système supporte plusieurs vues organisationnelles avec des targets personnalisés, des données isolées, et un système de board interactif avec drag & drop.

**Dernière mise à jour**: Janvier 2025  
**Version**: 2.1.0

---

## 🏗️ Architecture Technique

### Stack Technologique

**Backend:**
- **FastAPI** - Framework web Python moderne et performant  
- **Motor** - Driver MongoDB asynchrone
- **Pandas** - Manipulation et analyse de données
- **Python 3.10+**

**Frontend:**
- **React 18** - Bibliothèque UI avec hooks modernes
- **TailwindCSS** - Framework CSS utility-first
- **Recharts** - Graphiques et visualisations interactifs
- **@hello-pangea/dnd** - Drag & drop library (fork de react-beautiful-dnd)
- **React Router** - Navigation SPA
- **Axios** - Requêtes HTTP avec credentials
- **shadcn/ui** - Composants UI modernes (Tabs, DropdownMenu, etc.)

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

### Dual-Mode Authentication

**Mode 1: ACCESS SECURED TERMINAL (Production)**
- Google OAuth via Emergent integration
- Redirect vers https://auth.emergentagent.com/
- Session ID extraction depuis URL fragment
- Validation backend via https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data

**Mode 2: DEMO ACCESS - SKIP AUTH (Development)**
- Login instantané avec POST `/api/auth/demo-login`
- Crée demo@primelis.com (viewer role)
- Session 24 heures
- Cookie persistence

### Utilisateurs et Permissions

| Email | Rôle | Vues Accessibles | Permissions |
|-------|------|------------------|-------------|
| remi@primelis.com | super_admin | Toutes | Admin targets + User Management + Upload |
| philippe@primelis.com | super_admin | Toutes | Admin targets + User Management + Upload |
| asher@primelis.com | super_admin | Toutes | Admin targets + User Management + Upload |
| oren@primelis.com | viewer | Signal | Upload Signal |
| maxime.toubia@primelis.com | viewer | Full Funnel | Upload Full Funnel |
| coralie.truffy@primelis.com | viewer | Market | Upload Market |
| demo@primelis.com | viewer | Toutes | Lecture seule (Demo mode) |

### Session Management
- Sessions MongoDB (`user_sessions` collection)
- Cookie-based authentication
- 7-day expiration (production) / 24h (demo)
- Auto-cleanup expired sessions

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

#### 1. **Dashboard**
- Vue d'ensemble YTD Revenue avec forecast gap detection
- 5 KPI Cards: YTD Revenue, YTD Remaining, New Pipe Created, Created Weighted Pipe, Active Deals
- Graphiques évolution mensuelle revenue avec pipeline forecast
- 4 Dashboard blocks avec targets dynamiques (Meetings, Intro/POA, Pipe Creation, Revenue)
- Période sélectionnable: Monthly / July-Dec / Custom Period
- Targets se multiplient automatiquement selon la période sélectionnée

#### 2. **Meetings Generation**
- 5 MetricCards: Total New Intros, Inbound, Outbound, Referrals, Upsells/Cross-sell
- Sous-catégories Referrals: Internal, External, Client Referrals
- Event & None/Non-assigned metrics
- **Deal Pipeline Board — Interactive** (Nouveau ✨)
  * Drag & drop deals entre colonnes (Intro, POA Booked, Proposal Sent, Legal)
  * Filtrage par AE (Account Executive)
  * Indicateurs d'âge des deals (Fresh/Aging/Old)
  * Sauvegarde des préférences utilisateur (ordre, deals cachés)
  * Boutons Save/Reset pour persistance
  * Stage filtering: "F Inbox" pour Intro, "D POA Booked", "C Proposal sent", "B Legals"
- BDR Performance Table avec rôles et meeting goals
- Monthly Meetings Evolution graph avec breakdown par source
- Source Distribution & Relevance Analysis charts
- Intro Meetings Details table complète

#### 3. **Meetings Attended**
- 3 MetricCards: Meetings Scheduled, POA Generated, Deals Closed
- AE Performance cards avec Intro Attended, POA Done, Closing, Closing Value
- Monthly Evolution graphs pour chaque métrique
- POA Details table avec dates et valeurs

#### 4. **Upsell & Renew**
- 4 MetricCards: Total Intro Meetings, Business Partners, Consulting Partners, POA Attended
- Upsells vs Renewals breakdown
- Closing Performance (deals closed, closing value)
- Intro Meetings Details & POA Details tables

#### 5. **Deals & Pipeline**
- Pipe Metrics section: Created Pipe, Aggregate Pipe, Raw Pipeline, Weighted Pipe
- Stage Distribution avec counts et valeurs
- Monthly Evolution graphs (Created Pipe, Aggregate Weighted Pipe)
- Deals Closed section avec ARR closed metrics

#### 6. **Projections** (Closing Projections Tab)
- **Hot Deals Section** (B Legals stage)
  * Drag & drop reordering
  * Hide/unhide functionality
  * Deal cards avec client, pipeline value, AE, aging indicators
  * Reset button pour restaurer l'ordre original
- **Hot Leads Table** (C Proposal sent + D POA Booked)
  * MRR/ARR display
  * POA dates
  * Drag & drop reordering
- **Performance Summary**
  * YTD data synchronisé avec dashboard
  * Dashboard blocks pour periods
- **Closing Projections — Interactive Board**
  * 3 colonnes temporelles: Next 14 days, 30-60 days, 60-90 days
  * Drag & drop deals entre colonnes
  * Deal-specific closing probabilities (50%, 75%, 90%)
  * Dynamic total ARR & weighted ARR calculations per column
  * Drag & drop vertical ordering
  * Hide/unhide deals with X button
  * Save/Reset preferences with backend persistence
  * Styled goals avec progress bars par colonne
- **Upcoming POAs Section**
  * Count & total value display
  * Compact display (removed completed section)
- **AE Pipeline Breakdown Table**
  * Sortable columns
  * Pipeline, Expected ARR, Weighted Value pour chaque période
  * TOTAL row avec grand total calculations
  * French character encoding fixes (Rémi, François)
  * Double height board (48rem) pour meilleure visibilité

### Back Office Admin (super_admin uniquement)

#### Admin Targets Configuration
- **Interface par onglets** (une vue = un onglet)
- **6 Sections de configuration** mirroring dashboard structure:
  1. **Revenue Objectives 2025**: 12 mois configurables (Jan-Dec)
  2. **Deals Closed Yearly**: Target deals annuel
  3. **Dashboard Bottom Cards**: New Pipe Created, Created Weighted Pipe
  4. **Meeting Generation**: Total, Inbound, Outbound, Referral, Upsells/Cross-sell, Event targets
  5. **Intro & POA**: Intro target, POA target
  6. **Meetings Attended**: Meetings Scheduled, POA Generated, Deals Closed
  7. **Closing Projections Board**: Targets pour Next 14 days, 30-60 days, 60-90 days columns

- **Features**:
  * MetricCard replicas en gris montrant la structure du dashboard
  * Tous les targets sont mensuels et se multiplient automatiquement selon la période
  * Sauvegarde temps réel dans MongoDB avec confirmation ✅
  * Console logging pour vérification frontend/backend sync
  * Message display étendu (5 secondes)
  * Master view: manual overrides pour targets auto-agrégés

#### User Management (super_admin uniquement)
- Liste utilisateurs avec rôles
- CRUD complet utilisateurs
- Toggle role (viewer ↔ super_admin)
- Gestion accès vues par utilisateur
- Self-delete protection
- Color-coded success/error messages

### Système de Persistance
- **Projections Preferences**: Save/load/reset order et hidden deals par user + view
- **MongoDB Collections**: 
  * `user_projections_preferences` (Closing Projections board)
  * `user_pipeline_preferences` (Deal Pipeline Board - Meetings Generation)
- **View-specific**: Chaque vue a ses propres préférences utilisateur

---

## 🔌 API Endpoints Principaux

### Authentication
- POST `/api/auth/session-data` - Exchange session ID for user session (OAuth)
- POST `/api/auth/demo-login` - Login demo instantané
- GET `/api/auth/me` - Get current authenticated user
- POST `/api/auth/logout` - Déconnexion et clear session

### Views Management
- GET `/api/views/user/accessible` - Vues accessibles à l'user
- GET `/api/views/{view_id}/config` - Config et targets d'une vue
- PUT `/api/admin/views/{view_id}/targets` - Update targets (super_admin)
- POST `/api/views` - Create new view (super_admin)
- DELETE `/api/views/{view_id}` - Delete view (super_admin)

### User Management (super_admin)
- GET `/api/admin/users` - List all users with roles
- POST `/api/admin/users` - Create or update user
- PUT `/api/admin/users/{user_id}/role` - Update user role
- GET `/api/admin/users/{user_id}/views` - Get user's view access
- PUT `/api/admin/users/{user_id}/views` - Update user's view access
- DELETE `/api/admin/users/{user_id}` - Delete user and sessions

### Data Upload
- POST `/api/upload-data?view_id={id}` - Upload CSV
- POST `/api/upload-google-sheets?view_id={id}` - Upload Google Sheets
- GET `/api/data/status?view_id={id}` - Data status (records count, last update)

### Analytics
- GET `/api/analytics/monthly?view_id={id}&month_offset={n}` - Analytics mois
- GET `/api/analytics/yearly?view_id={id}&year={yyyy}` - Analytics année (July-Dec)
- GET `/api/analytics/custom?view_id={id}&start_date={date}&end_date={date}` - Custom period
- GET `/api/analytics/dashboard?view_id={id}` - Dashboard principal
- GET `/api/analytics/upsell-renewals?view_id={id}&month_offset={n}` - Upsells

### Projections
- GET `/api/projections/hot-deals?view_id={id}` - Deals chauds (B Legals stage)
- GET `/api/projections/hot-leads?view_id={id}` - Leads chauds (C+D stages)
- GET `/api/projections/ae-pipeline-breakdown?view_id={id}` - Pipeline par AE (14/30/60-90 days)
- GET `/api/projections/performance-summary?view_id={id}` - YTD performance summary

### User Preferences (Persistence)
- POST `/api/user/projections-preferences` - Save Closing Projections board state
- GET `/api/user/projections-preferences?view_id={id}` - Load saved preferences
- DELETE `/api/user/projections-preferences?view_id={id}` - Reset to default
- POST `/api/user/pipeline-preferences` - Save Deal Pipeline Board state
- GET `/api/user/pipeline-preferences?view_id={id}` - Load pipeline preferences
- DELETE `/api/user/pipeline-preferences?view_id={id}` - Reset pipeline board

### Target Calculations
- **Tous les endpoints supportent `view_id` parameter** pour isolation multi-tenant
- **Dynamic target multiplication**: Targets mensuels × nombre de mois dans la période
- **Master view auto-aggregation**: Signal + Full Funnel + Market avec manual overrides possibles

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
