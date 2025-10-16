"""
Script to set dummy targets (150 everywhere) for Master view for testing
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/sales_analytics')

async def set_master_dummy_targets():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.sales_analytics
    
    # Find Master view
    master_view = await db.views.find_one({"name": "Master"})
    if not master_view:
        print("❌ Master view not found!")
        return
    
    print(f"✅ Found Master view: {master_view['id']}")
    
    # Dummy targets with 150 everywhere
    dummy_targets = {
        "revenue_2025": {
            "jan": 150, "feb": 150, "mar": 150, "apr": 150, "may": 150, "jun": 150,
            "jul": 150, "aug": 150, "sep": 150, "oct": 150, "nov": 150, "dec": 150
        },
        "dashboard_bottom_cards": {
            "new_pipe_created": 150,
            "created_weighted_pipe": 150,
            "ytd_revenue": 150
        },
        "meeting_generation": {
            "total_target": 150,
            "inbound": 150,
            "outbound": 150,
            "referral": 150,
            "upsells_cross": 150
        },
        "intro_poa": {
            "intro": 150,
            "poa": 150
        },
        "meetings_attended": {
            "meetings_scheduled": 150,
            "poa_generated": 150,
            "deals_closed": 150
        },
        "deals_closed_yearly": {
            "deals_target": 150,
            "arr_target": 150
        },
        # Old format for compatibility
        "dashboard": {
            "objectif_6_mois": 150,
            "deals": 150,
            "new_pipe_created": 150,
            "weighted_pipe": 150
        },
        "meeting_attended": {
            "poa": 150,
            "deals_closed": 150
        }
    }
    
    # Update Master view targets
    result = await db.views.update_one(
        {"id": master_view['id']},
        {"$set": {"targets": dummy_targets}}
    )
    
    if result.matched_count > 0:
        print("✅ Master targets updated with dummy data (150 everywhere)")
        print(f"   Modified: {result.modified_count} document(s)")
        
        # Verify
        updated = await db.views.find_one({"id": master_view['id']})
        print(f"\n📊 Verification:")
        print(f"   revenue_2025.jan: {updated['targets']['revenue_2025']['jan']}")
        print(f"   dashboard_bottom_cards.new_pipe_created: {updated['targets']['dashboard_bottom_cards']['new_pipe_created']}")
        print(f"   meeting_generation.total_target: {updated['targets']['meeting_generation']['total_target']}")
    else:
        print("❌ Failed to update Master targets")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(set_master_dummy_targets())
