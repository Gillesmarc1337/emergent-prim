"""
Script to set Master view targets to 500 for testing (Admin BO format only)
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/sales_analytics')

async def set_master_500_targets():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.sales_analytics
    
    # Find Master view
    master_view = await db.views.find_one({"name": "Master"})
    if not master_view:
        print("❌ Master view not found!")
        return
    
    print(f"✅ Found Master view: {master_view['id']}")
    
    # Targets with 500 everywhere (Admin BO format ONLY)
    targets_500 = {
        "revenue_2025": {
            "jan": 500, "feb": 500, "mar": 500, "apr": 500, "may": 500, "jun": 500,
            "jul": 500, "aug": 500, "sep": 500, "oct": 500, "nov": 500, "dec": 500
        },
        "dashboard_bottom_cards": {
            "new_pipe_created": 500,
            "created_weighted_pipe": 500,
            "ytd_revenue": 500
        },
        "meeting_generation": {
            "total_target": 500,
            "inbound": 500,
            "outbound": 500,
            "referral": 500,
            "upsells_cross": 500
        },
        "intro_poa": {
            "intro": 500,
            "poa": 500
        },
        "meetings_attended": {
            "meetings_scheduled": 500,
            "poa_generated": 500,
            "deals_closed": 500
        },
        "deals_closed_current_period": {
            "deals_target": 500,
            "arr_target": 500
        },
        "upsell_renew": {
            "upsells_target": 500,
            "renewals_target": 500,
            "mrr_target": 500
        },
        "deals_closed_yearly": {
            "deals_target": 500,
            "arr_target": 500
        }
    }
    
    # Update Master view targets (replace completely)
    result = await db.views.update_one(
        {"id": master_view['id']},
        {"$set": {"targets": targets_500}}
    )
    
    if result.matched_count > 0:
        print("✅ Master targets updated to 500 (Admin BO format only)")
        print(f"   Modified: {result.modified_count} document(s)")
        
        # Verify
        updated = await db.views.find_one({"id": master_view['id']})
        print(f"\n📊 Verification:")
        print(f"   meetings_attended.meetings_scheduled: {updated['targets']['meetings_attended']['meetings_scheduled']}")
        print(f"   meetings_attended.poa_generated: {updated['targets']['meetings_attended']['poa_generated']}")
        print(f"   meetings_attended.deals_closed: {updated['targets']['meetings_attended']['deals_closed']}")
    else:
        print("❌ Failed to update Master targets")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(set_master_500_targets())
