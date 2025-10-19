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

### Logs Backend
```bash
# Backend errors
tail -50 /var/log/supervisor/backend.err.log

# Backend output
tail -50 /var/log/supervisor/backend.out.log

# Real-time monitoring
tail -f /var/log/supervisor/backend.*.log
```

### Logs Frontend
```bash
# Frontend errors
tail -50 /var/log/supervisor/frontend.err.log

# Build errors
tail -50 /var/log/supervisor/frontend.out.log
```

### Services Management
```bash
# Restart all services
sudo supervisorctl restart all

# Restart specific service
sudo supervisorctl restart backend
sudo supervisorctl restart frontend

# Check status
sudo supervisorctl status

# Reload supervisor config
sudo supervisorctl reread
sudo supervisorctl update
```

### MongoDB Debugging
```bash
# Connect to MongoDB
mongosh

# Switch to database
use sales_analytics

# Check collections
show collections

# View documents
db.views.find().pretty()
db.users.find().pretty()
db.user_sessions.find().pretty()

# Count records per view
db.sales_records_organic.countDocuments()
db.sales_records_fullfunnel.countDocuments()
db.sales_records_signal.countDocuments()
db.sales_records_market.countDocuments()

# Check user preferences
db.user_projections_preferences.find().pretty()
db.user_pipeline_preferences.find().pretty()

# Clear expired sessions
db.user_sessions.deleteMany({ expires_at: { $lt: new Date() } })
```

### Common Issues

**Issue**: Deal Pipeline Board shows "0 deals"
- **Solution**: Vérifier que les stages dans la data sont "F Inbox", "D POA Booked", "C Proposal sent", "B Legals"
- Check console logs: voir `📊 All meeting stages` dans browser console

**Issue**: Targets pas à jour après save
- **Solution**: Vérifier console logs pour "✅ Targets saved successfully"
- Check MongoDB: `db.views.findOne({id: "view-xxx"})`
- Verify backend response in browser Network tab

**Issue**: Drag & drop ne fonctionne pas
- **Solution**: Clear browser cache et localStorage
- Check que @hello-pangea/dnd est installé: `yarn list @hello-pangea/dnd`

**Issue**: 401 Unauthorized errors
- **Solution**: Session expirée, re-login required
- Check session in MongoDB: `db.user_sessions.find({session_id: "xxx"})`

### Performance Tips
- Les graphiques avec légendes interactives peuvent ralentir sur datasets >1000 points
- Deal Pipeline Board optimisé jusqu'à ~200 deals par column
- MongoDB indexes sur: `view_id`, `user_id`, `session_id`, `discovery_date`

---

## 📈 Améliorations Récentes (v2.1.0 - Janvier 2025)

### ✨ Nouveautés
1. **Deal Pipeline Board Interactive** (Meetings Generation tab)
   - Drag & drop deals entre stages: Intro (F Inbox) → POA Booked → Proposal Sent → Legal
   - Filtrage par AE avec dropdown "All AEs"
   - Aging indicators: Fresh (green) / Aging (yellow) / Old (red)
   - Save/Reset preferences avec persistance backend MongoDB
   - Stage filtering corrigé: "F Inbox" pour Intro column

2. **Closing Projections Enhancements**
   - Deal-specific closing probabilities (50%, 75%, 90% dropdown par deal)
   - Dynamic total ARR & weighted ARR calculations
   - Progress bars pour goals par colonne
   - Doubled board height (48rem) pour meilleure visibilité

3. **Admin Back Office Improvements**
   - Save confirmation avec message "✅ Frontend updated"
   - Console logging pour debug (view name, targets, backend response)
   - Extended message display (5 seconds)
   - Target key mapping automatique entre Admin BO et analytics functions

4. **Charts Interactivity**
   - Toutes les légendes des charts sont cliquables
   - Toggle visibility des data series
   - Persist visibility state pendant navigation

5. **Performance & UX**
   - Tab persistence fix: ne reset plus lors du changement de période
   - Monthly Average calculation corrigée: affiche le target mensuel consistant
   - French character encoding fixes (Rémi, François)
   - actualPeriodMonths calculation dynamique

### 🐛 Bug Fixes
- Fixed Deal Pipeline Board stage filtering (F Inbox recognition)
- Fixed tab reset issue when switching Monthly/July-Dec/Custom
- Fixed target key mapping for Master view
- Fixed Meetings Attended targets not reflecting in dashboard
- Fixed numpy serialization errors in analytics endpoints

### 🔄 Migration Notes
- Targets maintenant stockés avec nouvelle structure dans MongoDB
- Backward compatible via mapping function automatique
- Collections ajoutées: `user_projections_preferences`, `user_pipeline_preferences`

---

## 🎨 Branding & Theming

### Primelis Identity
- **Logo**: Intégré dans Header (top-left) et LoginPage
- **Login Theme**: "Cyber Pirates Terminal" avec animations et effets sci-fi
- **Color Palette**:
  * Primary: Blue/Cyan gradients
  * Secondary: Purple/Slate tones
  * Success: Green indicators
  * Warning: Orange/Yellow alerts
  * Error: Red notifications

### Custom Styling
- Tailwind configuration personnalisée dans `tailwind.config.js`
- Dark mode compatible (slate-900 backgrounds)
- Responsive design (mobile-first approach)
- Custom animations pour login page et interactive boards

---

## 🔧 Technical Implementation Details

### Excel-Based Weighting Logic
Le système utilise une formule Excel complexe pour calculer les weighted values:
```
weighted_value = pipeline_value × stage_probability × source_coefficient × recency_factor
```

**Stage Probabilities:**
- F Inbox (Intro): Variable based on source & recency
- D POA Booked: ~30-40%
- C Proposal sent: ~50-60%
- B Legals: ~75-85%
- A Closed: 100%

**Source Coefficients:**
- Inbound: 1.0
- Outbound: 0.8
- Referral: 1.2

**Recency Factor:**
- Fresh (0-7 days): 1.0
- Aging (8-14 days): 0.9
- Old (15+ days): 0.7

### Target Calculation System
```python
# Monthly base targets
MONTHLY_MEETINGS = 50  # 22 inbound + 17 outbound + 11 referral
MONTHLY_REVENUE = varies_per_view  # Ex: 1,080,000 for Full Funnel
MONTHLY_PIPE_CREATED = 2,000,000
MONTHLY_WEIGHTED_PIPE = 800,000

# Dynamic multiplication
target_for_period = monthly_target × period_duration_months

# Example:
# July-Dec (6 months) = 50 × 6 = 300 meetings target
# Custom 2-month period = 50 × 2 = 100 meetings target
```

### Drag & Drop Implementation
Utilise `@hello-pangea/dnd` (fork maintained de react-beautiful-dnd):
```jsx
<DragDropContext onDragEnd={handleDragEnd}>
  <Droppable droppableId="column-id">
    {(provided) => (
      <div ref={provided.innerRef} {...provided.droppableProps}>
        {deals.map((deal, index) => (
          <Draggable key={deal.id} draggableId={deal.id} index={index}>
            {(provided) => (
              <div ref={provided.innerRef} {...provided.draggableProps} {...provided.dragHandleProps}>
                {/* Deal Card */}
              </div>
            )}
          </Draggable>
        ))}
        {provided.placeholder}
      </div>
    )}
  </Droppable>
</DragDropContext>
```

### State Management
- **React Context**: AuthContext pour user + views globales
- **Local State**: useState pour UI states (deals, filters, modals)
- **Persistence**: MongoDB pour user preferences
- **Cache**: localStorage pour session persistence

### Data Flow
```
Google Sheets → Backend Upload → MongoDB (view-specific collections)
                                        ↓
User → Frontend → API Request (with view_id) → Backend Analytics
                                        ↓
                              Calculate with view targets
                                        ↓
                              Return formatted data → Frontend Display
```

---

## 📈 Roadmap & Future Enhancements

### Court terme (Q1 2025)
- [ ] Sync automatique targets depuis Google Sheets (colonnes Y et AL)
- [ ] Historique modifications targets avec audit trail
- [ ] Export/Import configurations targets entre vues
- [ ] Bulk operations pour Deal Pipeline Board
- [ ] Advanced filtering (date ranges, deal values, multiple AEs)

### Moyen terme (Q2-Q3 2025)
- [ ] Webhooks notifications (Slack, Teams, Discord)
- [ ] Rapports automatiques par email (daily/weekly/monthly)
- [ ] Mobile app React Native
- [ ] Real-time collaboration (WebSocket) pour boards
- [ ] Advanced analytics: Cohort analysis, Win rate by source, AE leaderboard

### Long terme (Q4 2025+)
- [ ] Multi-tenant SaaS transformation
- [ ] AI Assistant pour insights automatiques
- [ ] Prédictions ML pour closing probability
- [ ] Integration HubSpot/Salesforce native
- [ ] Custom dashboards builder
- [ ] API publique pour intégrations tierces

---

## 📄 Licence

Propriétaire - Primelis © 2025

**Développé avec ❤️ par Emergent AI**
