# Sales Analytics Dashboard - Documentation Complète

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture de l'application](#architecture-de-lapplication)
3. [Structure des fichiers](#structure-des-fichiers)
4. [Variables d'environnement](#variables-denvironnement)
5. [Backend - API Endpoints](#backend---api-endpoints)
6. [Frontend - Structure et Composants](#frontend---structure-et-composants)
7. [Calculs et Formules](#calculs-et-formules)
8. [Base de données MongoDB](#base-de-données-mongodb)
9. [Guide d'installation et déploiement](#guide-dinstallation-et-déploiement)
10. [Utilisation de l'application](#utilisation-de-lapplication)
11. [Maintenance et Troubleshooting](#maintenance-et-troubleshooting)

---

## 📊 Vue d'ensemble

Le **Sales Analytics Dashboard** est une application full-stack de suivi et d'analyse des performances commerciales. Elle permet d'importer des données via CSV ou Google Sheets, puis d'analyser différentes métriques clés sur plusieurs périodes (mensuelle, juillet-décembre, personnalisée).

### Fonctionnalités principales

- **Import de données** : CSV ou Google Sheets
- **Tableaux de bord dynamiques** : Métriques clés avec cibles et progression
- **Vues temporelles multiples** : Mensuel, Juillet-Décembre 2025, Périodes personnalisées
- **Analyses détaillées** :
  - Génération de meetings (Inbound, Outbound, Referral)
  - Meetings Attended et POA générés
  - Pipeline deals et métriques de closing
  - Projections de closing avec board interactif drag & drop
  - Performance par Account Executive (AE)
  - Weighted pipeline avec formule Excel complexe

### Stack technique

- **Backend** : FastAPI (Python 3.x)
- **Frontend** : React 18
- **Base de données** : MongoDB
- **Styling** : TailwindCSS + Radix UI
- **Charts** : Recharts
- **Drag & Drop** : @hello-pangea/dnd

---

## 🏗️ Architecture de l'application

```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND                            │
│                      React Application                       │
│                    (Port 3000 - dev)                        │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Dashboard   │  │  Meeting Gen │  │  Projections │    │
│  │    Tab       │  │     Tab      │  │     Tab      │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP/REST API
                         │ (JSON)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                         BACKEND                             │
│                    FastAPI Application                       │
│                      (Port 8001)                            │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Endpoints                            │  │
│  │  • /api/analytics/*                                   │  │
│  │  • /api/projections/*                                 │  │
│  │  • /api/upload/*                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                         │                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Business Logic Layer                         │  │
│  │  • calculate_meeting_generation()                     │  │
│  │  • calculate_ae_performance()                         │  │
│  │  • calculate_pipe_metrics()                           │  │
│  │  • calculate_excel_weighted_value()                   │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Motor (Async MongoDB Driver)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                        MONGODB                              │
│                                                             │
│  Collections:                                               │
│  • sales_records    : données principales                   │
│  • data_metadata    : métadonnées d'import                  │
└─────────────────────────────────────────────────────────────┘
```

### Flux de données

1. **Import** : L'utilisateur upload un CSV ou connecte une Google Sheet
2. **Parsing** : Le backend nettoie et normalise les données
3. **Stockage** : Les données sont insérées dans MongoDB (collection `sales_records`)
4. **Calculs** : Le backend effectue les calculs analytiques à la demande
5. **Affichage** : Le frontend reçoit les données structurées et les affiche

---

## 📁 Structure des fichiers

```
/app/
├── backend/
│   ├── server.py              # Application FastAPI principale
│   ├── requirements.txt       # Dépendances Python
│   └── .env                   # Variables d'environnement backend
│
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js             # Composant principal React
│   │   ├── App.css            # Styles globaux
│   │   ├── index.js           # Point d'entrée React
│   │   ├── index.css          # Styles de base + Tailwind
│   │   ├── components/
│   │   │   ├── GoogleSheetsUpload.jsx
│   │   │   ├── DateRangePicker.jsx
│   │   │   ├── ChartComponent.jsx
│   │   │   ├── MetricCard.jsx
│   │   │   └── ui/            # Composants Radix UI
│   │   │       ├── button.jsx
│   │   │       ├── card.jsx
│   │   │       ├── dialog.jsx
│   │   │       ├── input.jsx
│   │   │       ├── tabs.jsx
│   │   │       ├── badge.jsx
│   │   │       └── ...
│   │   └── lib/
│   │       └── utils.js       # Fonctions utilitaires
│   ├── package.json           # Dépendances Node.js
│   ├── tailwind.config.js     # Configuration Tailwind
│   ├── postcss.config.js      # Configuration PostCSS
│   └── .env                   # Variables d'environnement frontend
│
├── test_result.md             # Journal de tests et développement
└── README.md                  # Ce fichier
```

---

## 🔧 Variables d'environnement

### Backend (.env)

```bash
# MongoDB Configuration
MONGO_URL=mongodb://localhost:27017/
DB_NAME=sales_analytics

# IMPORTANT: Ne jamais modifier MONGO_URL en production
# Cette variable est gérée automatiquement par l'infrastructure
```

**Variables importantes** :
- `MONGO_URL` : URL de connexion MongoDB (localhost en dev, gérée automatiquement en prod)
- `DB_NAME` : Nom de la base de données MongoDB

### Frontend (.env)

```bash
# Backend API URL
REACT_APP_BACKEND_URL=http://localhost:8001

# IMPORTANT: Ne jamais hardcoder cette URL dans le code
# Toujours utiliser: process.env.REACT_APP_BACKEND_URL
```

**Variables importantes** :
- `REACT_APP_BACKEND_URL` : URL du backend API (configurée automatiquement en production)

### ⚠️ Règles critiques

1. **NE JAMAIS modifier** `MONGO_URL` ou `REACT_APP_BACKEND_URL` manuellement
2. **TOUJOURS utiliser** les variables d'environnement dans le code
3. En production, ces URLs sont gérées par l'orchestration Kubernetes
4. Tous les endpoints backend **DOIVENT** commencer par `/api`

---

## 🔌 Backend - API Endpoints

### 1. Upload & Import

#### `POST /api/upload/csv`
Importe des données depuis un fichier CSV.

**Body** : `multipart/form-data` avec fichier CSV

**Response** :
```json
{
  "success": true,
  "message": "Successfully imported 128 records from CSV",
  "records_count": 128,
  "source": "csv"
}
```

#### `POST /api/upload/google-sheet`
Importe des données depuis une Google Sheet.

**Body** :
```json
{
  "sheet_url": "https://docs.google.com/spreadsheets/d/...",
  "sheet_name": "Sheet1"
}
```

**Response** :
```json
{
  "success": true,
  "message": "Successfully imported 128 records from Google Sheet",
  "records_count": 128,
  "source": "google_sheets"
}
```

---

### 2. Analytics Endpoints

#### `GET /api/analytics/monthly`
Retourne les analytics pour le mois en cours.

**Response Structure** :
```json
{
  "period": "10/1/2025 - 10/31/2025",
  "big_numbers_recap": {
    "ytd_revenue": 1129596,
    "ytd_target": 4500000,
    "ytd_remaining": 3370404,
    "pipe_created": 6865596,
    "active_deals_count": 75
  },
  "dashboard_blocks": {
    "block_1_meetings": {
      "period": "Oct 2025",
      "inbound_actual": 0,
      "inbound_target": 22,
      "outbound_actual": 0,
      "outbound_target": 17,
      "referral_actual": 0,
      "referral_target": 11,
      "total_actual": 0,
      "total_target": 50,
      "show_actual": 0,
      "no_show_actual": 0
    },
    "block_2_intro_poa": {
      "period": "Oct 2025",
      "intro_actual": 0,
      "intro_target": 50,
      "poa_actual": 0,
      "poa_target": 18
    },
    "block_3_pipe_creation": {
      "period": "Oct 2025",
      "new_pipe_created": 2947200,
      "weighted_pipe_created": 492000,
      "aggregate_weighted_pipe": 4290000,
      "target_pipe_created": 2000000
    },
    "block_4_revenue": {
      "period": "Oct 2025",
      "closed_revenue": 0,
      "revenue_target": 1080000,
      "progress": 0
    }
  },
  "deals_closed": {
    "deals_closed": 0,
    "target_deals": 5,
    "arr_closed": 0,
    "target_arr": 1080000,
    "mrr_closed": 0,
    "avg_deal_size": 0,
    "on_track": false,
    "deals_detail": [],
    "monthly_closed": [...]
  },
  "meeting_generation": {
    "target": 50,
    "inbound_target": 22,
    "outbound_target": 17,
    "referral_target": 11,
    "total_meetings": 0,
    "inbound_meetings": 0,
    "outbound_meetings": 0,
    "referral_meetings": 0,
    "relevant": 0,
    "question_mark": 0,
    "not_relevant": 0,
    "bdr_breakdown": []
  },
  "ae_performance": {
    "ae_performance": [
      {
        "ae": "Guillaume",
        "intros_attended": 45,
        "relevant_intro": 38,
        "poa_fait": 12,
        "closing": 3,
        "valeur_closing": 250000
      }
    ],
    "intros_details": [...],
    "poa_attended_details": [...]
  },
  "pipe_metrics": {
    "created_pipe": {
      "value": 2947200,
      "weighted_value": 492000,
      "count": 15,
      "target": 2000000,
      "on_track": true
    },
    "total_pipe": {
      "value": 9787200,
      "weighted_value": 4290000,
      "count": 75,
      "target": 5000000,
      "on_track": true
    },
    "ae_breakdown": [
      {
        "ae": "Guillaume",
        "total_pipe": 4267200,
        "weighted_pipe": 2145000,
        "new_pipe_created": 1200000,
        "deals_count": 28,
        "new_deals_count": 5
      }
    ]
  },
  "closing_projections": {
    "current_month": {
      "total_deals": 42,
      "total_pipeline": 5623200,
      "weighted_value": 3723000,
      "deals": [...]
    },
    "next_quarter": {...}
  }
}
```

#### `GET /api/analytics/yearly?year=2025`
Retourne les analytics pour la période Juillet-Décembre 2025.

**Query Parameters** :
- `year` : Année (ex: 2025)

**Response** : Même structure que `/monthly` mais avec :
- `period` : "Jul-Dec 2025"
- Targets multipliés par 6 (6 mois)
- Données agrégées sur juillet à décembre

#### `GET /api/analytics/custom?start_date=2025-10-01&end_date=2025-11-30`
Retourne les analytics pour une période personnalisée.

**Query Parameters** :
- `start_date` : Date de début (format: YYYY-MM-DD)
- `end_date` : Date de fin (format: YYYY-MM-DD)

**Response** : Même structure avec targets dynamiques basées sur la durée de la période.

---

### 3. Projections Endpoints

#### `GET /api/projections/hot-deals`
Retourne les deals en stage "B Legals" (proches de closing).

**Response** :
```json
[
  {
    "id": "uuid-123",
    "client": "Cegid",
    "pipeline": 360000,
    "expected_mrr": 30000,
    "expected_arr": 360000,
    "owner": "Guillaume",
    "stage": "B Legals",
    "hubspot_link": "https://..."
  }
]
```

#### `GET /api/projections/hot-leads`
Retourne les leads en stages "C Proposal sent" ou "D POA Booked".

**Response** :
```json
[
  {
    "id": "uuid-456",
    "client": "La SPA",
    "pipeline": 43200,
    "expected_mrr": 3600,
    "expected_arr": 43200,
    "owner": "Bruno",
    "stage": "C Proposal sent",
    "hubspot_link": "https://...",
    "poa_date": "2025-10-15T00:00:00"
  }
]
```

#### `GET /api/projections/ae-pipeline-breakdown`
Retourne le breakdown du pipeline par AE pour différentes périodes temporelles.

**Response** :
```json
[
  {
    "ae": "Guillaume",
    "next14": {
      "pipeline": 717600,
      "expected_arr": 1017600,
      "weighted_value": 483840
    },
    "next30": {
      "pipeline": 240000,
      "expected_arr": 240000,
      "weighted_value": 120000
    },
    "next60": {
      "pipeline": 132000,
      "expected_arr": 132000,
      "weighted_value": 39600
    },
    "total": {
      "pipeline": 1089600,
      "expected_arr": 1389600,
      "weighted_value": 643440
    }
  }
]
```

#### `GET /api/projections/performance-summary`
Retourne le résumé de performance pour l'onglet Projections.

**Response** :
```json
{
  "ytd_revenue": 1129596,
  "ytd_target": 4500000,
  "forecast_gap": true,
  "pipe_created": 6865596,
  "active_deals_count": 75,
  "dashboard_blocks": {...}
}
```

---

## 🎨 Frontend - Structure et Composants

### Structure de l'App.js

Le fichier `App.js` contient un composant `Dashboard` principal qui gère tout l'état de l'application.

#### State Management

```javascript
// États principaux
const [analytics, setAnalytics] = useState(null);
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);

// Navigation temporelle
const [viewMode, setViewMode] = useState('monthly'); // 'monthly' | 'yearly'
const [useCustomDate, setUseCustomDate] = useState(false);
const [dateRange, setDateRange] = useState({ from: null, to: null });

// Import
const [importMethod, setImportMethod] = useState('csv'); // 'csv' | 'sheets'

// Projections
const [hotDeals, setHotDeals] = useState([]);
const [hotLeads, setHotLeads] = useState([]);
const [aeBreakdown, setAeBreakdown] = useState([]);
const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
```

### Composants principaux

#### 1. Dashboard Component
Le composant racine qui contient tous les onglets et gère l'état global.

#### 2. Data Management Section
Zone d'upload CSV/Google Sheets et affichage du statut des données.

#### 3. Tabs Navigation
- **Dashboard** : KPIs principaux, graphiques de revenue
- **Meeting Generation** : Métriques de génération de meetings par source
- **Meetings Attended** : Performance AE sur intros et POA
- **Deals & Pipeline** : Métriques de pipeline et deals par stage
- **Projections** : Board interactif drag & drop et breakdown AE

### Composants réutilisables

#### MetricCard
Affiche une métrique avec valeur, cible, et badge de statut.

```jsx
<MetricCard
  title="YTD Revenue 2025"
  value="1,129,596 $"
  target="Target: 4,500,000 $"
  progress={25.1}
  statusBadge="Needs Attention"
  colors={{ badge: "destructive", bar: "red" }}
  icon={DollarSign}
/>
```

#### ChartComponent
Wrapper pour les graphiques Recharts avec configuration personnalisée.

```jsx
<ChartComponent
  data={chartData}
  type="bar"
  xKey="month"
  lines={[
    { key: 'revenue', name: 'Revenue', color: '#3b82f6' }
  ]}
/>
```

#### DraggableDealItem
Carte de deal draggable pour le board interactif.

```jsx
<DraggableDealItem
  deal={deal}
  index={index}
  showActions={true}
  onHide={() => hideItem('deals', deal.id)}
/>
```

---

## 🧮 Calculs et Formules

### 1. Weighted Pipeline (Formule Excel Complexe)

La valeur pondérée d'un deal est calculée avec la formule :

```
Weighted Value = Pipeline Value × Stage Factor × Source Factor × Recency Factor
```

#### Stage Factors
- **E Intro attended** : Base 0.30
- **D POA Booked** : Base 0.50
- **C Proposal sent** : Base 0.70
- **B Legals** : Base 0.90
- **A Closed** : 1.00

#### Source Factors
- **Inbound** : 0.7 à 1.0 (selon recency)
- **Outbound** : 0.5 à 0.85
- **Client referral** : 0.0 à 1.4
- **Internal referral** : 0.0 à 1.2
- **Partnership** : 0.5 à 0.8

#### Recency Factors
Basés sur le nombre de jours depuis la découverte du deal :
- Deals récents : facteur plus élevé
- Deals anciens : facteur réduit (risque de stagnation)

**Implémentation backend** :
```python
def calculate_excel_weighted_value(row):
    """Calcule la weighted value avec la formule Excel exacte"""
    pipeline_value = float(row.get('pipeline', 0))
    stage = row.get('stage', '')
    source_type = row.get('type_of_source', '')
    discovery_date = row.get('discovery_date')
    
    # Calcul du nombre de jours depuis discovery
    today = datetime.now()
    days_since_discovery = (today - discovery_date).days
    
    # Logique complexe stage × source × recency
    # ... (voir server.py lignes 560-680)
    
    return pipeline_value * probability
```

### 2. Targets Dynamiques

Les targets s'ajustent automatiquement selon la durée de la période :

```python
period_duration_months = max(1, round(period_duration_days / 30))

# Targets mensuels de base
monthly_meetings_target = 50
monthly_poa_target = 18
monthly_deals_target = 6
monthly_revenue_target = 1_080_000

# Targets pour la période
period_meetings_target = monthly_meetings_target * period_duration_months
period_poa_target = monthly_poa_target * period_duration_months
# etc.
```

**Exemples** :
- 1 mois : 50 meetings, 18 POA, 6 deals, 1.08M€ revenue
- 2 mois : 100 meetings, 36 POA, 12 deals, 2.16M€ revenue
- 6 mois (Jul-Dec) : 300 meetings, 108 POA, 36 deals, 6.48M€ revenue

### 3. Meeting Generation Split

Les meetings sont répartis selon la source avec des targets spécifiques :

```python
# Base mensuelle (total = 50)
inbound_target = 22    # 44%
outbound_target = 17   # 34%
referral_target = 11   # 22%
```

Ces ratios sont maintenus quelle que soit la durée de la période.

### 4. Pipeline Metrics

#### Created Pipe
```
New Pipe Created = Σ(pipeline) pour tous les deals découverts dans la période
```

#### Total Pipeline
```
Total Pipeline = Σ(pipeline) pour tous les deals actifs (non Lost/Closed/Not Relevant)
```

#### Aggregate Weighted Pipe
```
Aggregate Weighted Pipe = Σ(weighted_value) pour tous les deals actifs
```

### 5. AE Performance Metrics

Pour chaque Account Executive :

```python
intros_attended = Count(deals où stage ≠ 'F Inbox' ET show_noshow ≠ 'Noshow')
relevant_intro = Count(intros où relevance = 'Relevant')
poa_fait = Count(deals en stages avancés: Legals, Proposal, POA Booked, Closed)
closing = Count(deals en stage 'A Closed')
valeur_closing = Σ(expected_arr pour deals closed)
```

---

## 🗄️ Base de données MongoDB

### Collection: `sales_records`

Chaque document représente un deal/lead avec la structure suivante :

```javascript
{
  "_id": ObjectId("..."),
  "id": "uuid-string",
  "month": "October",
  "discovery_date": ISODate("2025-10-15T00:00:00Z"),
  "client": "Cegid",
  "hubspot_link": "https://app.hubspot.com/...",
  "stage": "B Legals",
  "relevance": "Relevant",
  "show_noshow": "Show",
  "poa_date": ISODate("2025-09-20T00:00:00Z"),
  "expected_mrr": 30000,
  "expected_arr": 360000,
  "pipeline": 360000,
  "type_of_source": "Inbound",
  "bdr": "Sarah",
  "owner": "Guillaume",
  "billing_start": ISODate("2025-11-01T00:00:00Z"),
  "created_at": ISODate("2025-10-10T12:34:56Z")
}
```

#### Champs importants

| Champ | Type | Description |
|-------|------|-------------|
| `id` | String (UUID) | Identifiant unique du deal |
| `discovery_date` | Date | Date de découverte du lead |
| `client` | String | Nom du client |
| `stage` | String | Stage du deal (A à I) |
| `relevance` | String | Relevant, Not relevant, Question mark |
| `show_noshow` | String | Show ou Noshow (pour meetings) |
| `poa_date` | Date | Date du POA (Plan of Action) |
| `expected_arr` | Number | ARR attendu (Annual Recurring Revenue) |
| `expected_mrr` | Number | MRR attendu (Monthly Recurring Revenue) |
| `pipeline` | Number | Valeur du pipeline (deal value) |
| `type_of_source` | String | Inbound, Outbound, Client referral, etc. |
| `bdr` | String | BDR assigné (Business Development Rep) |
| `owner` | String | AE assigné (Account Executive) |

#### Stages du pipeline

| Code | Stage | Description |
|------|-------|-------------|
| A | Closed | Deal fermé/gagné |
| B | Legals | En négociation légale |
| C | Proposal sent | Proposition envoyée |
| D | POA Booked | POA réservé |
| E | Intro attended | Introduction effectuée |
| F | Inbox | Lead non qualifié |
| H | Not relevant | Lead non pertinent |
| I | Lost | Deal perdu |

### Collection: `data_metadata`

Stocke les métadonnées d'import :

```javascript
{
  "_id": ObjectId("..."),
  "type": "last_update",
  "timestamp": ISODate("2025-10-10T12:00:00Z"),
  "source": "google_sheets",
  "source_url": "https://docs.google.com/spreadsheets/d/...",
  "sheet_name": "Sheet1",
  "records_count": 128
}
```

---

## 🚀 Guide d'installation et déploiement

### Prérequis

- **Node.js** 16+ et yarn
- **Python** 3.8+
- **MongoDB** 4.4+
- **Git**

### Installation locale

#### 1. Cloner le repository

```bash
git clone <repository-url>
cd app
```

#### 2. Configuration Backend

```bash
cd backend

# Installer les dépendances
pip install -r requirements.txt

# Configurer .env
cat > .env << EOF
MONGO_URL=mongodb://localhost:27017/
DB_NAME=sales_analytics
EOF

# Lancer MongoDB (si pas déjà en cours)
# macOS/Linux:
mongod --dbpath /data/db

# Lancer le serveur
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

Le backend sera accessible à : `http://localhost:8001`

#### 3. Configuration Frontend

```bash
cd ../frontend

# Installer les dépendances
yarn install

# Configurer .env
cat > .env << EOF
REACT_APP_BACKEND_URL=http://localhost:8001
EOF

# Lancer le serveur de dev
yarn start
```

Le frontend sera accessible à : `http://localhost:3000`

### Déploiement en production

L'application est conçue pour être déployée sur Kubernetes avec :

- **Backend** : Géré par supervisor sur port 8001
- **Frontend** : Build React servi sur port 3000
- **MongoDB** : Instance dédiée avec URL configurée via variable d'environnement

#### Configuration Kubernetes

1. **Ingress Rules** :
   - Routes `/api/*` → Backend (port 8001)
   - Routes `/*` → Frontend (port 3000)

2. **Variables d'environnement** :
   - Gérées automatiquement par l'orchestrateur
   - `MONGO_URL` pointe vers l'instance MongoDB de production
   - `REACT_APP_BACKEND_URL` configuré avec l'URL externe

3. **Supervision** :
```bash
# Redémarrer les services
sudo supervisorctl restart backend
sudo supervisorctl restart frontend
sudo supervisorctl restart all

# Vérifier le statut
sudo supervisorctl status
```

---

## 📱 Utilisation de l'application

### 1. Import des données

#### Via CSV
1. Cliquer sur "Upload New Data"
2. Sélectionner un fichier CSV
3. Attendre la confirmation d'import

#### Via Google Sheets
1. Sélectionner "Google Sheets"
2. Coller l'URL de la sheet
3. Spécifier le nom de l'onglet (optionnel)
4. Cliquer sur "Import from Google Sheets"

**Format CSV attendu** :
```csv
Month,Discovery Date,Client,Stage,Relevance,Show/Noshow,POA Date,Expected MRR,Expected ARR,Pipeline,Type of Source,BDR,Owner,Billing Start
October,2025-10-15,Cegid,B Legals,Relevant,Show,2025-09-20,30000,360000,360000,Inbound,Sarah,Guillaume,2025-11-01
```

### 2. Navigation temporelle

#### Vue Mensuelle
- Affiche le mois en cours
- Boutons "Previous Month" / "Next Month" pour naviguer

#### Vue Juillet-Décembre
- Cliquer sur "July To Dec"
- Affiche les métriques agrégées sur 6 mois
- Targets multipliés par 6

#### Période personnalisée
- Cliquer sur "Custom Period"
- Sélectionner dates de début et fin dans le calendrier
- Targets calculés dynamiquement

### 3. Onglets du dashboard

#### Dashboard (Principal)
- **Big Numbers** : YTD Revenue, Pipe Created, Active Deals
- **Dashboard Blocks** : 4 blocs avec Meetings, Intro/POA, Pipe Creation, Deals Closed
- **Graphiques** : Revenue mensuel, Pipeline trends

#### Meeting Generation
- Métriques par source (Inbound, Outbound, Referral)
- Breakdown par BDR
- Analyse de pertinence (Relevant, Question mark, Not relevant)
- Graphiques de distribution

#### Meetings Attended
- Performance des AEs sur :
  - Intros Attended
  - POA Done
  - Closing Value
- Listes détaillées avec filtres
- Targets dynamiques (50 meetings, 18 POA, 6 deals par mois)

#### Deals & Pipeline
- Métriques de pipeline :
  - New Pipe Created
  - Created Weighted Pipe
  - Total Pipeline
  - Total Weighted Pipe
- Breakdown par AE
- Targets et progression

#### Projections
- **Summary Cards** : Legals, Proposal Sent, Combined Value, POA Status
- **Projections by AE** : Table avec Total Pipeline, Weighted Value, Aggregate Pipe
- **Interactive Board** : Drag & drop des deals par période
  - Next 14 Days (Legals)
  - Next 30 Days (POA Booked)
  - Next 60-90 Days (Proposal sent)
- **AE Pipeline Breakdown** : Table détaillée avec Pipeline, Expected ARR, Weighted Value par période
  - Ligne TOTAL en bas du tableau avec sommes pour chaque métrique

### 4. Fonctionnalités interactives

#### Tri des tableaux
- Cliquer sur les en-têtes de colonnes pour trier
- Indicateurs de direction (↑ ↓)

#### Drag & Drop
- Glisser-déposer les deals entre colonnes
- Changements visuels uniquement (pas de modification en base)

#### Graphiques interactifs
- Hover pour voir les valeurs détaillées
- Cliquer sur les légendes pour masquer/afficher des séries

#### Filtres
- Les tableaux peuvent être filtrés par AE, stage, etc.

---

## 🔧 Maintenance et Troubleshooting

### Logs

#### Backend logs
```bash
# Logs en temps réel
tail -f /var/log/supervisor/backend.*.log

# Erreurs uniquement
tail -f /var/log/supervisor/backend.err.log

# Dernières 100 lignes
tail -n 100 /var/log/supervisor/backend.out.log
```

#### Frontend logs
```bash
# Logs du serveur React
tail -f /var/log/supervisor/frontend.*.log
```

### Problèmes courants

#### 1. Backend ne démarre pas

**Symptôme** : Erreur 502 ou API inaccessible

**Solutions** :
```bash
# Vérifier les logs
tail -n 50 /var/log/supervisor/backend.err.log

# Vérifier MongoDB
mongosh
use sales_analytics
db.sales_records.countDocuments()

# Redémarrer
sudo supervisorctl restart backend
```

#### 2. Données ne s'affichent pas

**Symptôme** : Dashboard vide ou erreurs de chargement

**Solutions** :
```bash
# Vérifier les données en base
mongosh sales_analytics
db.sales_records.countDocuments()
db.sales_records.findOne()

# Réimporter les données via l'interface

# Vérifier la connexion backend
curl http://localhost:8001/api/analytics/monthly
```

#### 3. Encodage incorrect (accents)

**Symptôme** : "RÃ©mi" au lieu de "Rémi"

**Cause** : Données mal encodées en base

**Solution** : La fonction `fix_ae_name_encoding()` corrige automatiquement l'affichage. Si problème persiste :
```python
# Ajouter dans fix_ae_name_encoding():
name_fixes = {
    'RÃ©mi': 'Rémi',
    'FranÃ§ois': 'François',
    # Ajouter d'autres cas
}
```

#### 4. Targets incorrects

**Symptôme** : Targets ne correspondent pas à la période

**Solution** :
```python
# Vérifier le calcul dans server.py
period_duration_months = max(1, round(period_duration_days / 30))
monthly_target = 50
period_target = monthly_target * period_duration_months
```

#### 5. Weighted values à 0

**Symptôme** : Weighted pipeline affiche $0

**Cause** : Formule Excel non appliquée

**Solution** :
```python
# Vérifier que calculate_excel_weighted_value est appelé
df['weighted_value'] = df.apply(calculate_excel_weighted_value, axis=1)
```

### Maintenance régulière

#### Backup MongoDB
```bash
# Backup complet
mongodump --db sales_analytics --out /backup/$(date +%Y%m%d)

# Restauration
mongorestore --db sales_analytics /backup/20251010/sales_analytics
```

#### Nettoyage des anciennes données
```javascript
// Supprimer les deals anciens (> 2 ans)
db.sales_records.deleteMany({
  discovery_date: { $lt: new Date('2023-01-01') }
})
```

#### Réindexation
```javascript
// Créer des index pour améliorer les performances
db.sales_records.createIndex({ discovery_date: 1 })
db.sales_records.createIndex({ owner: 1 })
db.sales_records.createIndex({ stage: 1 })
```

---

## 📊 Métriques et KPIs

### Dashboard principal

| Métrique | Calcul | Target Type |
|----------|--------|-------------|
| YTD Revenue | Σ(expected_arr) stage A Closed | 4.5M€ annuel |
| Pipe Created | Σ(pipeline) deals découverts | 2M€ mensuel |
| Active Deals | Count(deals actifs) | 75+ |
| Meetings | Count(découvertes) | 50/mois |
| POA Generated | Count(stages avancés) | 18/mois |
| Deals Closed | Count(stage A) | 6/mois |

### Formules Excel implémentées

#### Aggregate Weighted Pipe (Z17)
```
Pour chaque deal actif :
  weighted_value = pipeline × stage_factor × source_factor × recency_factor
Total = Σ(weighted_value)
```

#### Pipeline Metrics
```
New Pipe Created = Σ(pipeline) pour period_deals
Total Pipeline = Σ(pipeline) pour active_deals
Weighted Pipeline = Σ(weighted_value) pour active_deals
```

---

## 🎯 Roadmap & Améliorations futures

### Features prévues
- [ ] Export Excel des données
- [ ] Notifications pour deals à risque
- [ ] Prédictions ML sur closing probability
- [ ] Intégration Hubspot API
- [ ] Dashboard mobile responsive
- [ ] Authentification utilisateurs

### Optimisations
- [ ] Caching des calculs lourds
- [ ] Pagination des grandes listes
- [ ] Lazy loading des onglets
- [ ] Compression des réponses API

---

## 📞 Support

Pour toute question ou problème :
1. Consulter les logs backend/frontend
2. Vérifier la documentation API
3. Contacter l'équipe technique

---

**Version** : 1.0.0  
**Dernière mise à jour** : Octobre 2025  
**Maintenu par** : Équipe Sales Analytics
