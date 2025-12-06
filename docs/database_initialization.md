# Database Initialization

## Current State: No Explicit Initialization

**The database is NOT explicitly initialized anywhere.** MongoDB creates databases automatically on first write (lazy creation).

---

## Database Creation Points

### 1. **MongoDB Container Startup** (`docker-compose.yml`)

```yaml
mongodb:
    environment:
        MONGO_INITDB_ROOT_USERNAME: root
        MONGO_INITDB_ROOT_PASSWORD: password
        MONGO_INITDB_DATABASE: sales_analytics # ⚠️ Only sets default name, doesn't create DB
```

**Note**: `MONGO_INITDB_DATABASE` only sets the default database name. It does **NOT** create the database. The database is created when data is first written to it.

---

### 2. **Database Connection** (`backend/server.py` & `backend/auth.py`)

**Location**: Module-level code (executed on import)

```python
# backend/server.py (lines 59-62)
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]  # ⚠️ Just references the database, doesn't create it
```

**Location**: Module-level code

```python
# backend/auth.py (lines 12-15)
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'sales_analytics')]  # ⚠️ Just references, doesn't create
```

**What happens**: These lines establish a connection and reference the database, but MongoDB doesn't create the database until the first write operation.

---

### 3. **Application Startup Event** (`backend/server.py`)

**Location**: `@app.on_event("startup")` (line 5116)

```python
@app.on_event("startup")
async def startup_scheduler():
    """Start the scheduler for auto-refresh tasks"""
    # ⚠️ Only starts scheduler, does NOT initialize database
    scheduler.start()
```

**Current behavior**: Only starts the scheduler. Does **NOT** initialize the database.

---

### 4. **Implicit Database Creation** (First Write Operations)

The database is created automatically when data is first written. This can happen through:

#### A. User Authentication (`backend/auth.py`)

**When**: User logs in for the first time

```python
# backend/auth.py - get_or_create_user() (line 96)
await db.users.insert_one(user_data)  # ✅ Creates database + users collection
```

#### B. Session Creation (`backend/auth.py`)

**When**: User session is created

```python
# backend/auth.py - create_session() (line 102)
await db.user_sessions.insert_one(session_data)  # ✅ Creates user_sessions collection
```

#### C. Setup Scripts (Manual)

**Location**: `backend/setup_multi_views.py` and `backend/setup_auth_test.py`

```python
# These scripts create initial data
await db.users.insert_one(user_data)      # ✅ Creates users collection
await db.views.insert_one(view_data)      # ✅ Creates views collection
await db.user_sessions.insert_one(...)    # ✅ Creates user_sessions collection
```

**Usage**: Run manually to seed initial data:

```bash
cd backend
python setup_multi_views.py
python setup_auth_test.py
```

#### D. Data Upload (`backend/server.py`)

**When**: Admin uploads CSV or Google Sheets data

```python
# Creates sales_records* collections when data is uploaded
await collection.insert_many(records)  # ✅ Creates collection if it doesn't exist
```

---

## Database Initialization Flow

```
1. MongoDB Container Starts
   └─> Sets MONGO_INITDB_DATABASE (default name only)

2. Backend Server Starts
   └─> Connects to MongoDB (db = client['sales_analytics'])
   └─> Database does NOT exist yet

3. First Write Operation (any of):
   ├─> User login → db.users.insert_one() → ✅ Database created
   ├─> Setup script → db.views.insert_one() → ✅ Database created
   ├─> Data upload → db.sales_records.insert_many() → ✅ Database created
   └─> Any insert operation → ✅ Database created
```

---

## Problem: Database Not Visible in mongo-express

**Issue**: If no data has been written yet, the database won't appear in mongo-express because MongoDB doesn't show empty databases.

**Solution**: Write at least one document to create the database:

```bash
# Option 1: Run setup script
cd backend
python setup_multi_views.py

# Option 2: Create a test document via MongoDB shell
docker-compose exec mongodb mongosh -u root -p password --authenticationDatabase admin
use sales_analytics
db._system_init.insertOne({type: "database_init", created_at: new Date()})
```

---

## Recommended: Add Explicit Initialization

To ensure the database is always created on startup, add initialization to the startup event:

**Location**: `backend/server.py` - `@app.on_event("startup")`

```python
@app.on_event("startup")
async def startup_scheduler():
    """Initialize database and start the scheduler"""
    try:
        # Initialize database - MongoDB creates databases on first write
        init_collection = db['_system_init']
        init_doc = await init_collection.find_one({"type": "database_init"})

        if not init_doc:
            await init_collection.insert_one({
                "type": "database_init",
                "created_at": datetime.now(timezone.utc),
                "database_name": db.name
            })
            print(f"✅ Database '{db.name}' initialized")
        else:
            print(f"✅ Database '{db.name}' already initialized")
    except Exception as e:
        print(f"⚠️ Database initialization check failed: {str(e)}")

    # ... rest of scheduler code
```

**Note**: This was previously added but rejected. The current implementation relies on lazy creation.

---

## Summary

| Location                               | Action                           | Creates Database?              |
| -------------------------------------- | -------------------------------- | ------------------------------ |
| `docker-compose.yml`                   | `MONGO_INITDB_DATABASE`          | ❌ No (only sets default name) |
| `server.py` line 62                    | `db = client['sales_analytics']` | ❌ No (just references)        |
| `auth.py` line 15                      | `db = client['sales_analytics']` | ❌ No (just references)        |
| `@app.on_event("startup")`             | Scheduler start                  | ❌ No                          |
| First `insert_one()` / `insert_many()` | Any write operation              | ✅ Yes (lazy creation)         |

**Current State**: Database is created implicitly on first write operation. No explicit initialization exists.



