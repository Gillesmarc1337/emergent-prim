# Database Structure Documentation

**Database Name**: `sales_analytics`  
**MongoDB Version**: 7.0  
**Last Updated**: January 2025

## Overview

The `sales_analytics` database uses MongoDB to store user authentication, multi-view configurations, sales records, targets, and user preferences. The system supports multiple organizational views with isolated data collections.

---

## Collections

### 1. `users`

Stores user accounts and authentication information.

**Schema:**

```javascript
{
  "_id": ObjectId,                    // MongoDB auto-generated ID
  "id": String,                       // Custom user ID (e.g., "user-remi-1234567890")
  "email": String,                    // User email (unique, used for authentication)
  "name": String,                     // User display name
  "picture": String | null,           // Profile picture URL (from Google OAuth)
  "role": String,                     // "viewer" | "super_admin"
  "view_access": Array<String>,      // List of view names user can access
                                      // e.g., ["Signal", "Full Funnel", "Market", "Master"]
  "created_at": DateTime,             // Account creation timestamp (UTC)
  "last_login": DateTime | null      // Last login timestamp (UTC)
}
```

**Indexes:**

-   `email` (unique)

**Example:**

```javascript
{
  "id": "user-remi-1704067200",
  "email": "remi@primelis.com",
  "name": "Rémi",
  "picture": "https://lh3.googleusercontent.com/...",
  "role": "super_admin",
  "view_access": ["Organic", "Full Funnel", "Signal", "Market", "Master"],
  "created_at": ISODate("2024-01-01T00:00:00.000Z"),
  "last_login": ISODate("2025-01-15T10:30:00.000Z")
}
```

**Roles:**

-   `viewer`: Can view assigned views, upload data to assigned views
-   `super_admin`: Full access to all views, can manage users, configure targets

---

### 2. `user_sessions`

Stores active user sessions for authentication.

**Schema:**

```javascript
{
  "_id": ObjectId,                    // MongoDB auto-generated ID
  "id": String,                       // Custom session ID (e.g., "session-1234567890")
  "user_id": String,                  // Reference to users.id
  "session_token": String,            // Unique session token (used in cookies)
  "expires_at": DateTime,             // Session expiration timestamp (UTC)
  "created_at": DateTime              // Session creation timestamp (UTC)
}
```

**Indexes:**

-   `session_token` (unique)
-   `user_id`
-   `expires_at` (TTL index recommended for auto-cleanup)

**Session Expiration:**

-   Normal sessions: 7 days (168 hours)
-   Demo sessions: 24 hours

**Example:**

```javascript
{
  "id": "session-1704067200",
  "user_id": "user-remi-1704067200",
  "session_token": "session_user-remi-1704067200_1704067200",
  "expires_at": ISODate("2025-01-22T10:30:00.000Z"),
  "created_at": ISODate("2025-01-15T10:30:00.000Z")
}
```

---

### 3. `views`

Stores view configurations, targets, and metadata for each organizational view.

**Schema:**

```javascript
{
  "_id": ObjectId,                    // MongoDB auto-generated ID
  "id": String,                       // Custom view ID (e.g., "view-organic-1234567890")
  "name": String,                     // View name: "Organic" | "Signal" | "Full Funnel" | "Market" | "Master"
  "sheet_url": String | null,         // Google Sheets URL for data source
  "sheet_name": String | null,        // Specific sheet name within the spreadsheet
  "is_master": Boolean,               // true if this is the Master view (aggregates other views)
  "is_default": Boolean,               // true if this is the default view for new users
  "assigned_user": String,            // Email of user assigned to this view
  "aggregates_from": Array<String>,  // Array of view IDs (only for Master view)
  "targets": {                        // Target configuration object
    "revenue_2025": {                 // Monthly revenue targets
      "jan": Number,
      "feb": Number,
      "mar": Number,
      "apr": Number,
      "may": Number,
      "jun": Number,
      "jul": Number,
      "aug": Number,
      "sep": Number,
      "oct": Number,
      "nov": Number,
      "dec": Number
    },
    "deals_closed_yearly": {
      "deals_target": Number          // Annual deals target
    },
    "dashboard_bottom_cards": {
      "new_pipe_created": Number,     // Monthly target
      "created_weighted_pipe": Number, // Monthly target
      "ytd_aggregate_pipeline": Number
    },
    "meeting_generation": {
      "total_target": Number,          // Monthly total meetings
      "inbound": Number,               // Monthly inbound meetings
      "outbound": Number,              // Monthly outbound meetings
      "referral": Number,              // Monthly referral meetings
      "upsells_cross": Number          // Monthly upsell/cross-sell meetings
    },
    "intro_poa": {
      "intro": Number,                 // Monthly intro meetings target
      "poa": Number                    // Monthly POA (Proof of Agreement) target
    },
    "meetings_attended": {
      "meetings_scheduled": Number,    // Monthly target
      "poa_generated": Number,         // Monthly target
      "deals_closed": Number           // Monthly target
    },
    "closing_projections": {
      "next_14_days": Number,          // ARR target for next 14 days
      "next_30_60_days": Number,       // ARR target for 30-60 days
      "next_60_90_days": Number        // ARR target for 60-90 days
    },
    // Legacy format (backward compatibility)
    "dashboard": {
      "objectif_6_mois": Number,      // 6-month revenue objective
      "deals": Number,                 // Monthly deals target
      "new_pipe_created": Number,
      "weighted_pipe": Number
    },
    "meeting_generation": {
      "intro": Number,
      "inbound": Number,
      "outbound": Number,
      "referrals": Number,
      "upsells_x": Number
    },
    "meeting_attended": {
      "poa": Number,
      "deals_closed": Number
    }
  },
  "created_at": DateTime,             // View creation timestamp (UTC)
  "created_by": String | null        // User who created the view
}
```

**Indexes:**

-   `id` (unique)
-   `name` (unique)
-   `is_master`
-   `is_default`

**View Types:**

-   **Organic**: Default view with historical data
-   **Signal**: Focus on acquisition (Oren)
-   **Full Funnel**: Complete sales pipeline (Maxime)
-   **Market**: Market-focused view (Coralie)
-   **Master**: Aggregates Signal + Full Funnel + Market + Organic

**Example:**

```javascript
{
  "id": "view-signal-1704067200",
  "name": "Signal",
  "sheet_url": "https://docs.google.com/spreadsheets/d/1HJSHVRBKbwJ199VxJCioSOTz4gI9KrSniXKwAjcU3bI/edit",
  "sheet_name": "Sheet1",
  "is_master": false,
  "is_default": false,
  "assigned_user": "oren@primelis.com",
  "targets": {
    "revenue_2025": {
      "jan": 0, "feb": 0, "mar": 0, "apr": 0, "may": 0, "jun": 0,
      "jul": 283333, "aug": 283333, "sep": 283333, "oct": 283333, "nov": 283333, "dec": 283333
    },
    "meeting_generation": {
      "total_target": 50,
      "inbound": 2,
      "outbound": 15,
      "referral": 1,
      "upsells_cross": 3
    }
  },
  "created_at": ISODate("2024-01-01T00:00:00.000Z")
}
```

---

### 4. `sales_records` / `sales_records_signal` / `sales_records_fullfunnel` / `sales_records_market`

Stores sales pipeline data for each view. Each view has its own collection.

**Collection Mapping:**

-   `sales_records` → Organic view
-   `sales_records_signal` → Signal view
-   `sales_records_fullfunnel` → Full Funnel view
-   `sales_records_market` → Market view

**Schema:**

```javascript
{
  "_id": ObjectId,                    // MongoDB auto-generated ID
  "id": String,                       // Custom record ID (UUID)
  "month": String | null,             // Month identifier (e.g., "2025-01")
  "discovery_date": DateTime | null,  // Date when deal was discovered
  "client": String,                   // Client/company name
  "hubspot_link": String | null,      // Link to HubSpot deal
  "stage": String,                    // Deal stage: "F Inbox" | "D POA Booked" | "C Proposal sent" | "B Legals" | "A Closed" | "Lost" | "Not Relevant"
  "relevance": String | null,         // Relevance indicator
  "show_noshow": String | null,       // "Show" | "Noshow" | null
  "poa_date": DateTime | null,        // Proof of Agreement date
  "expected_mrr": Number | null,      // Expected Monthly Recurring Revenue
  "expected_arr": Number | null,      // Expected Annual Recurring Revenue
  "pipeline": Number | null,          // Pipeline value
  "type_of_deal": String | null,      // Deal type
  "bdr": String | null,               // Business Development Representative name
  "type_of_source": String | null,    // Source: "Inbound" | "Outbound" | "Referral" | "Internal referral" | "External referral" | "Client referral" | "Event" | "None/Non-assigned" | "Upsell/Cross-sell"
  "product": String | null,           // Product name
  "owner": String | null,             // Account Executive (AE) name
  "supporters": String | null,        // Supporting team members
  "billing_start": DateTime | null,   // Billing start date
  "created_at": DateTime              // Record creation timestamp (UTC)
}
```

**Indexes:**

-   `id` (unique)
-   `client`
-   `stage`
-   `discovery_date`
-   `owner`
-   `type_of_source`
-   `show_noshow`

**Stage Values:**

-   `F Inbox`: Intro stage
-   `D POA Booked`: Proof of Agreement booked
-   `C Proposal sent`: Proposal sent
-   `B Legals`: Legal stage (hot deals)
-   `A Closed`: Deal closed
-   `Lost`: Deal lost
-   `Not Relevant`: Not relevant

**Source Types:**

-   `Inbound`: Inbound lead
-   `Outbound`: Outbound lead
-   `Referral`: General referral
-   `Internal referral`: Internal referral
-   `External referral`: External referral
-   `Client referral`: Client referral
-   `Event`: Event-based lead
-   `None/Non-assigned`: Unassigned
-   `Upsell/Cross-sell`: Upsell or cross-sell

**Example:**

```javascript
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "month": "2025-01",
  "discovery_date": ISODate("2025-01-10T00:00:00.000Z"),
  "client": "Acme Corp",
  "hubspot_link": "https://app.hubspot.com/deals/12345",
  "stage": "B Legals",
  "relevance": "High",
  "show_noshow": "Show",
  "poa_date": ISODate("2025-01-15T00:00:00.000Z"),
  "expected_mrr": 5000,
  "expected_arr": 60000,
  "pipeline": 60000,
  "type_of_deal": "New Business",
  "bdr": "John Doe",
  "type_of_source": "Inbound",
  "product": "Enterprise Plan",
  "owner": "Jane Smith",
  "supporters": "Support Team",
  "billing_start": ISODate("2025-02-01T00:00:00.000Z"),
  "created_at": ISODate("2025-01-10T10:00:00.000Z")
}
```

---

### 5. `data_metadata`

Stores metadata about data uploads and refreshes for each view.

**Schema:**

```javascript
{
  "_id": ObjectId,                    // MongoDB auto-generated ID
  "type": String,                     // "last_update"
  "view_id": String,                  // Reference to views.id
  "source_type": String,              // "csv" | "google_sheets"
  "source_url": String | null,        // URL of the data source
  "last_update": DateTime,            // Last update timestamp (UTC)
  "records_count": Number,             // Number of records in the collection
  "created_at": DateTime              // Metadata creation timestamp (UTC)
}
```

**Indexes:**

-   `type` + `view_id` (compound, unique)
-   `view_id`
-   `last_update`

**Example:**

```javascript
{
  "type": "last_update",
  "view_id": "view-signal-1704067200",
  "source_type": "google_sheets",
  "source_url": "https://docs.google.com/spreadsheets/d/1HJSHVRBKbwJ199VxJCioSOTz4gI9KrSniXKwAjcU3bI/edit",
  "last_update": ISODate("2025-01-15T12:00:00.000Z"),
  "records_count": 150,
  "created_at": ISODate("2025-01-01T00:00:00.000Z")
}
```

---

### 6. `user_projections_preferences`

Stores user preferences for the Closing Projections board (drag & drop order, hidden deals).

**Schema:**

```javascript
{
  "_id": ObjectId,                    // MongoDB auto-generated ID
  "user_id": String,                  // Reference to users.id
  "view_id": String,                  // Reference to views.id
  "preferences": {                    // Preferences object
    "next_14_days": [                 // Array of deals in order
      {
        "id": String,                 // Deal ID (from sales_records)
        "client": String,
        "pipeline": Number,
        "probability": Number,         // 50 | 75 | 90
        "owner": String,
        "stage": String,
        "hidden": Boolean             // true if deal is hidden
      }
    ],
    "next_30_60_days": [...],        // Same structure
    "next_60_90_days": [...]         // Same structure
  },
  "updated_at": DateTime              // Last update timestamp (UTC)
}
```

**Indexes:**

-   `user_id` + `view_id` (compound, unique)
-   `user_id`
-   `view_id`

**Example:**

```javascript
{
  "user_id": "user-remi-1704067200",
  "view_id": "view-signal-1704067200",
  "preferences": {
    "next_14_days": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "client": "Acme Corp",
        "pipeline": 60000,
        "probability": 90,
        "owner": "Jane Smith",
        "stage": "B Legals",
        "hidden": false
      }
    ],
    "next_30_60_days": [],
    "next_60_90_days": []
  },
  "updated_at": ISODate("2025-01-15T14:30:00.000Z")
}
```

---

### 7. `user_pipeline_preferences`

Stores user preferences for the Deal Pipeline Board in Meetings Generation tab.

**Schema:**

```javascript
{
  "_id": ObjectId,                    // MongoDB auto-generated ID
  "user_id": String,                  // Reference to users.id
  "view_id": String,                  // Reference to views.id
  "preferences": {                    // Preferences object
    "intro": [                        // Array of deal IDs in order (F Inbox stage)
      {
        "id": String,                 // Deal ID
        "hidden": Boolean             // true if deal is hidden
      }
    ],
    "poa_booked": [...],             // D POA Booked stage
    "proposal_sent": [...],           // C Proposal sent stage
    "legal": [...]                    // B Legals stage
  },
  "updated_at": DateTime              // Last update timestamp (UTC)
}
```

**Indexes:**

-   `user_id` + `view_id` (compound, unique)
-   `user_id`
-   `view_id`

**Example:**

```javascript
{
  "user_id": "user-remi-1704067200",
  "view_id": "view-signal-1704067200",
  "preferences": {
    "intro": [
      { "id": "deal-123", "hidden": false },
      { "id": "deal-456", "hidden": true }
    ],
    "poa_booked": [],
    "proposal_sent": [],
    "legal": []
  },
  "updated_at": ISODate("2025-01-15T14:30:00.000Z")
}
```

---

### 8. `asher_pov`

Stores Asher's persistent Point of View (POV) preferences for projections board. This is a special collection that persists independently and can be loaded by anyone but only modified by Asher.

**Schema:**

```javascript
{
  "_id": ObjectId,                    // MongoDB auto-generated ID
  "view_id": String,                  // Reference to views.id
  "preferences": {                    // Same structure as user_projections_preferences.preferences
    "next_14_days": [...],
    "next_30_60_days": [...],
    "next_60_90_days": [...]
  },
  "timestamp": String,                // Human-readable timestamp (e.g., "2025-01-15 14:30:00 UTC")
  "updated_at": DateTime             // Last update timestamp (UTC)
}
```

**Indexes:**

-   `view_id` (unique)

**Access Control:**

-   **Read**: Anyone authenticated can load Asher POV
-   **Write**: Only `asher@primelis.com` can save/update

**Example:**

```javascript
{
  "view_id": "view-signal-1704067200",
  "preferences": {
    "next_14_days": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "client": "Acme Corp",
        "pipeline": 60000,
        "probability": 90,
        "owner": "Jane Smith",
        "stage": "B Legals",
        "hidden": false
      }
    ],
    "next_30_60_days": [],
    "next_60_90_days": []
  },
  "timestamp": "2025-01-15 14:30:00 UTC",
  "updated_at": ISODate("2025-01-15T14:30:00.000Z")
}
```

---

## Relationships

### User → Views

-   Users have `view_access` array listing accessible views
-   Super admins can access all views
-   Viewers can only access views in their `view_access` array

### User → Sessions

-   One user can have multiple active sessions
-   Sessions are linked via `user_sessions.user_id` → `users.id`

### View → Sales Records

-   Each view has its own sales records collection
-   Collection name determined by `VIEW_COLLECTION_MAP[view_name]`
-   Master view aggregates from multiple collections

### View → Data Metadata

-   Each view has metadata about its data source
-   Linked via `data_metadata.view_id` → `views.id`

### User → Preferences

-   Users have separate preferences per view
-   Linked via `user_projections_preferences.user_id` + `view_id`
-   Linked via `user_pipeline_preferences.user_id` + `view_id`

---

## Data Isolation

Each view has isolated data:

-   **Organic**: `sales_records`
-   **Signal**: `sales_records_signal`
-   **Full Funnel**: `sales_records_fullfunnel`
-   **Market**: `sales_records_market`
-   **Master**: Aggregates all above collections

---

## Indexes Recommendations

### Performance Indexes

```javascript
// users
db.users.createIndex({email: 1}, {unique: true});
db.users.createIndex({role: 1});
db.users.createIndex({view_access: 1});

// user_sessions
db.user_sessions.createIndex({session_token: 1}, {unique: true});
db.user_sessions.createIndex({user_id: 1});
db.user_sessions.createIndex({expires_at: 1}, {expireAfterSeconds: 0}); // TTL index

// views
db.views.createIndex({id: 1}, {unique: true});
db.views.createIndex({name: 1}, {unique: true});
db.views.createIndex({is_master: 1});
db.views.createIndex({is_default: 1});

// sales_records (and variants)
db.sales_records.createIndex({id: 1}, {unique: true});
db.sales_records.createIndex({client: 1});
db.sales_records.createIndex({stage: 1});
db.sales_records.createIndex({discovery_date: 1});
db.sales_records.createIndex({owner: 1});
db.sales_records.createIndex({type_of_source: 1});
db.sales_records.createIndex({show_noshow: 1});

// data_metadata
db.data_metadata.createIndex({type: 1, view_id: 1}, {unique: true});
db.data_metadata.createIndex({view_id: 1});

// user_projections_preferences
db.user_projections_preferences.createIndex(
    {user_id: 1, view_id: 1},
    {unique: true}
);

// user_pipeline_preferences
db.user_pipeline_preferences.createIndex(
    {user_id: 1, view_id: 1},
    {unique: true}
);

// asher_pov
db.asher_pov.createIndex({view_id: 1}, {unique: true});
```

---

## Data Migration Notes

### Target Format Migration

The system supports both old and new target formats for backward compatibility:

-   **Old format**: `dashboard.objectif_6_mois`, `meeting_generation.intro`
-   **New format**: `revenue_2025.jan`, `meeting_generation.total_target`

The `map_admin_targets_to_analytics_format()` function handles conversion.

---

## Backup & Maintenance

### Regular Maintenance

1. **Session Cleanup**: Expired sessions are automatically cleaned up (TTL index)
2. **Data Refresh**: Auto-refresh scheduled at 12:00 and 20:00 Europe/Paris time
3. **Deduplication**: Sales records are deduplicated by `client` + `stage` on upload

### Backup Strategy

-   MongoDB backups should include all collections
-   Critical collections: `users`, `views`, `user_sessions`
-   Large collections: `sales_records*` (consider compression)

---

## Environment Variables

Required MongoDB connection:

```bash
MONGO_URL=mongodb://root:password@database:27017/sales_analytics?authSource=admin
DB_NAME=sales_analytics
```

**Note**: The hostname `database` matches the service name in `docker-compose.yml`. If running outside Docker, use `localhost` instead.

---

## Version History

-   **v2.1.0** (January 2025): Added user preferences collections, updated target structure
-   **v2.0.0**: Multi-view system with isolated collections
-   **v1.0.0**: Initial single-view system
