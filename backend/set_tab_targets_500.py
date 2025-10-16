"""
Set tab targets to 500 for Master view (NEW direct tab targets)
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/sales_analytics')

async def set_tab_targets():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.sales_analytics
    
    # Find Master view
    master_view = await db.views.find_one({"name": "Master"})
    if not master_view:
        print("❌ Master view not found!")
        return
    
    print(f"✅ Found Master view: {master_view['id']}")
    
    # Get existing targets
    existing_targets = master_view.get("targets", {})
    
    # Add NEW tab targets to existing structure
    existing_targets["meetings_attended_tab"] = {
        "meetings_scheduled_target": 500,
        "poa_generated_target": 500,
        "deals_closed_target": 500
    }
    
    existing_targets["deals_closed_tab"] = {
        "deals_closed_target": 500,
        "arr_closed_target": 500000
    }
    
    # Update Master view targets
    result = await db.views.update_one(
        {"id": master_view['id']},
        {"$set": {"targets": existing_targets}}
    )
    
    if result.matched_count > 0:
        print("✅ Master tab targets updated to 500")
        print(f"   Modified: {result.modified_count} document(s)")
        
        # Verify
        updated = await db.views.find_one({"id": master_view['id']})
        print(f"\n📊 Verification:")
        print(f"   meetings_attended_tab.meetings_scheduled_target: {updated['targets']['meetings_attended_tab']['meetings_scheduled_target']}")
        print(f"   meetings_attended_tab.poa_generated_target: {updated['targets']['meetings_attended_tab']['poa_generated_target']}")
        print(f"   meetings_attended_tab.deals_closed_target: {updated['targets']['meetings_attended_tab']['deals_closed_target']}")
        print(f"   deals_closed_tab.deals_closed_target: {updated['targets']['deals_closed_tab']['deals_closed_target']}")
        print(f"   deals_closed_tab.arr_closed_target: ${updated['targets']['deals_closed_tab']['arr_closed_target']:,}")
    else:
        print("❌ Failed to update Master tab targets")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(set_tab_targets())
