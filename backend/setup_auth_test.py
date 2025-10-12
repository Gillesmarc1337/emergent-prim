"""
Setup script to create test user session and default view for authentication testing
"""
import os
import asyncio
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorClient

async def setup_test_data():
    # MongoDB connection
    mongo_url = os.environ.get('MONGO_URL')
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'sales_analytics')]
    
    print("🔧 Setting up authentication test data...")
    print(f"📊 Database: {db.name}")
    
    # Check existing collections
    collections = await db.list_collection_names()
    print(f"📁 Existing collections: {collections}")
    
    # 1. Create test users
    print("\n👤 Creating test users...")
    users = [
        {
            "id": f"user-remi-{int(datetime.now(timezone.utc).timestamp())}",
            "email": "remi@primelis.com",
            "name": "Rémi",
            "picture": None,
            "role": "super_admin",
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": f"user-asher-{int(datetime.now(timezone.utc).timestamp())}",
            "email": "asher@primelis.com",
            "name": "Asher",
            "picture": None,
            "role": "viewer",
            "created_at": datetime.now(timezone.utc)
        }
    ]
    
    for user in users:
        existing = await db.users.find_one({"email": user["email"]})
        if existing:
            print(f"  ✓ User already exists: {user['email']}")
        else:
            await db.users.insert_one(user)
            print(f"  ✅ Created user: {user['email']} (role: {user['role']})")
    
    # 2. Create test sessions for both users
    print("\n🔐 Creating test sessions...")
    for user in users:
        user_doc = await db.users.find_one({"email": user["email"]})
        if user_doc:
            session_token = f"test_session_{user_doc['id']}_{int(datetime.now(timezone.utc).timestamp())}"
            session_data = {
                "id": f"session-{int(datetime.now(timezone.utc).timestamp())}",
                "user_id": user_doc["id"],
                "session_token": session_token,
                "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
                "created_at": datetime.now(timezone.utc)
            }
            
            # Delete any existing test sessions for this user
            await db.user_sessions.delete_many({"user_id": user_doc["id"]})
            
            await db.user_sessions.insert_one(session_data)
            print(f"  ✅ Created session for {user['email']}")
            print(f"     Token: {session_token}")
            print(f"     Expires: {session_data['expires_at']}")
    
    # 3. Create default "Organic" view
    print("\n📊 Creating default 'Organic' view...")
    existing_view = await db.views.find_one({"name": "Organic"})
    if existing_view:
        print("  ✓ Organic view already exists")
    else:
        view_data = {
            "id": f"view-organic-{int(datetime.now(timezone.utc).timestamp())}",
            "name": "Organic",
            "sheet_url": "https://docs.google.com/spreadsheets/d/your-sheet-id",
            "sheet_name": "Sheet1",
            "is_master": True,
            "is_default": True,
            "created_by": "system",
            "created_at": datetime.now(timezone.utc)
        }
        await db.views.insert_one(view_data)
        print(f"  ✅ Created default 'Organic' view")
        print(f"     ID: {view_data['id']}")
    
    # 4. Display summary
    print("\n📈 Summary:")
    user_count = await db.users.count_documents({})
    session_count = await db.user_sessions.count_documents({})
    view_count = await db.views.count_documents({})
    
    print(f"  Users: {user_count}")
    print(f"  Sessions: {session_count}")
    print(f"  Views: {view_count}")
    
    print("\n✨ Test data setup complete!")
    print("\n🧪 Test the authentication flow:")
    print("  1. Frontend should load and show login page")
    print("  2. Click 'Sign in with Google' to test OAuth flow")
    print("  3. Or manually test with session tokens above using curl:")
    print("\n  Example curl command:")
    remi_user = await db.users.find_one({"email": "remi@primelis.com"})
    if remi_user:
        remi_session = await db.user_sessions.find_one({"user_id": remi_user["id"]})
        if remi_session:
            print(f"  curl -X GET http://localhost:8001/api/auth/me \\")
            print(f"    -H 'Cookie: session_token={remi_session['session_token']}'")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(setup_test_data())
