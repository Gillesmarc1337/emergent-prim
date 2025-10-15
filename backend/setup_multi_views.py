"""
Setup script for multi-view system with different targets per view
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'sales_analytics')]

# View configurations with targets per view
VIEW_CONFIGS = {
    "Organic": {
        "user_email": "demo@primelis.com",
        "sheet_url": None,  # Default view
        "targets": {
            "dashboard": {
                "objectif_6_mois": 4500000,  # 4.5M (default from original system)
                "deals": 25,
                "new_pipe_created": 2000000,  # 2M
                "weighted_pipe": 800000  # 800K
            },
            "meeting_generation": {
                "intro": 45,
                "inbound": 22,
                "outbound": 17,
                "referrals": 11,
                "upsells_x": 0
            },
            "meeting_attended": {
                "poa": 18,
                "deals_closed": 6
            }
        }
    },
    "Full Funnel": {
        "user_email": "maxime.toubia@primelis.com",
        "sheet_url": "https://docs.google.com/spreadsheets/d/12vOjTGZKoBNiodDMb-dFNH7r7aUOrPdFs5whMFjDKZo/edit?usp=drive_link",
        "targets": {
            "dashboard": {
                "objectif_6_mois": 4500000,  # 4.5M
                "deals": 25,
                "new_pipe_created": 2000000,  # 2M
                "weighted_pipe": 800000  # 800K
            },
            "meeting_generation": {
                "intro": 12,
                "inbound": 5,
                "outbound": 2,
                "referrals": 5,
                "upsells_x": 10
            },
            "meeting_attended": {
                "poa": 9,
                "deals_closed": 5
            }
        }
    },
    "Signal": {
        "user_email": "oren@primelis.com",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1HJSHVRBKbwJ199VxJCioSOTz4gI9KrSniXKwAjcU3bI/edit?usp=drive_link",
        "targets": {
            "dashboard": {
                "objectif_6_mois": 1700000,  # 1.7M
                "deals": 18,
                "new_pipe_created": 800000,  # 800K
                "weighted_pipe": 300000  # 300K
            },
            "meeting_generation": {
                "intro": 17,
                "inbound": 2,
                "outbound": 15,
                "referrals": 1,
                "upsells_x": 3
            },
            "meeting_attended": {
                "poa": 8,
                "deals_closed": 3
            }
        }
    },
    "Market": {
        "user_email": "coralie.truffy@primelis.com",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1BJ_thepAfcZ7YQY1aWFoPbuBIakzd65hoMfbCJCDSlk/edit?usp=drive_link",
        "targets": {
            "dashboard": {
                "objectif_6_mois": 1700000,  # 1.7M
                "deals": 20,
                "new_pipe_created": 800000,  # 800K
                "weighted_pipe": 300000  # 300K
            },
            "meeting_generation": {
                "intro": 15,
                "inbound": 5,
                "outbound": 8,
                "referrals": 2,
                "upsells_x": 3
            },
            "meeting_attended": {
                "poa": 10,
                "deals_closed": 5
            }
        }
    }
}

async def setup_multi_views():
    """
    Setup multi-view system:
    1. Create new users
    2. Create views with targets
    3. Calculate Master view targets (sum of 4 views: Organic + Signal + Full Funnel + Market)
    """
    print("🚀 Setting up multi-view system...")
    
    # Step 1: Create users
    users_to_create = [
        {
            "email": "oren@primelis.com",
            "name": "Oren (Signal)",
            "role": "viewer",
            "view_access": ["Signal"]
        },
        {
            "email": "maxime.toubia@primelis.com",
            "name": "Maxime (Full Funnel)",
            "role": "viewer",
            "view_access": ["Full Funnel"]
        },
        {
            "email": "coralie.truffy@primelis.com",
            "name": "Coralie (Market)",
            "role": "viewer",
            "view_access": ["Market"]
        },
        {
            "email": "philippe@primelis.com",
            "name": "Philippe (C-Level)",
            "role": "super_admin",
            "view_access": ["Full Funnel", "Signal", "Market", "Master"]
        }
    ]
    
    print("\n📝 Creating users...")
    for user_info in users_to_create:
        existing_user = await db.users.find_one({"email": user_info["email"]})
        
        if existing_user:
            print(f"  ✓ User {user_info['email']} already exists")
        else:
            user_data = {
                "id": f"user-{user_info['email'].split('@')[0]}-{int(datetime.now(timezone.utc).timestamp())}",
                "email": user_info["email"],
                "name": user_info["name"],
                "picture": None,
                "role": user_info["role"],
                "view_access": user_info["view_access"],
                "created_at": datetime.now(timezone.utc)
            }
            await db.users.insert_one(user_data)
            print(f"  ✅ Created user: {user_info['email']} ({user_info['role']})")
    
    # Update remi and asher to have access to all views including Master
    print("\n📝 Updating existing users (remi, asher) access...")
    await db.users.update_one(
        {"email": "remi@primelis.com"},
        {"$set": {"view_access": ["Organic", "Full Funnel", "Signal", "Market", "Master"]}}
    )
    await db.users.update_one(
        {"email": "asher@primelis.com"},
        {"$set": {"view_access": ["Organic", "Full Funnel", "Signal", "Market", "Master"]}}
    )
    print("  ✅ Updated remi and asher with full view access")
    
    # Step 2: Create views with targets
    print("\n📊 Creating views with targets...")
    
    created_view_ids = {}
    
    for view_name, config in VIEW_CONFIGS.items():
        existing_view = await db.views.find_one({"name": view_name})
        
        if existing_view:
            print(f"  ✓ View '{view_name}' already exists")
            created_view_ids[view_name] = existing_view["id"]
        else:
            view_data = {
                "id": f"view-{view_name.lower().replace(' ', '-')}-{int(datetime.now(timezone.utc).timestamp())}",
                "name": view_name,
                "sheet_url": config["sheet_url"],
                "sheet_name": None,
                "is_master": False,
                "is_default": False,
                "targets": config["targets"],
                "assigned_user": config["user_email"],
                "created_at": datetime.now(timezone.utc)
            }
            await db.views.insert_one(view_data)
            created_view_ids[view_name] = view_data["id"]
            print(f"  ✅ Created view: {view_name} ({config['user_email']})")
    
    # Step 3: Calculate and create Master view (sum of all 3 views)
    print("\n🎯 Creating Master view (aggregated targets)...")
    
    master_targets = {
        "dashboard": {
            "objectif_6_mois": sum(config["targets"]["dashboard"]["objectif_6_mois"] for config in VIEW_CONFIGS.values()),
            "deals": sum(config["targets"]["dashboard"]["deals"] for config in VIEW_CONFIGS.values()),
            "new_pipe_created": sum(config["targets"]["dashboard"]["new_pipe_created"] for config in VIEW_CONFIGS.values()),
            "weighted_pipe": sum(config["targets"]["dashboard"]["weighted_pipe"] for config in VIEW_CONFIGS.values())
        },
        "meeting_generation": {
            "intro": sum(config["targets"]["meeting_generation"]["intro"] for config in VIEW_CONFIGS.values()),
            "inbound": sum(config["targets"]["meeting_generation"]["inbound"] for config in VIEW_CONFIGS.values()),
            "outbound": sum(config["targets"]["meeting_generation"]["outbound"] for config in VIEW_CONFIGS.values()),
            "referrals": sum(config["targets"]["meeting_generation"]["referrals"] for config in VIEW_CONFIGS.values()),
            "upsells_x": sum(config["targets"]["meeting_generation"]["upsells_x"] for config in VIEW_CONFIGS.values())
        },
        "meeting_attended": {
            "poa": sum(config["targets"]["meeting_attended"]["poa"] for config in VIEW_CONFIGS.values()),
            "deals_closed": sum(config["targets"]["meeting_attended"]["deals_closed"] for config in VIEW_CONFIGS.values())
        }
    }
    
    existing_master = await db.views.find_one({"name": "Master"})
    
    if existing_master:
        # Update targets
        await db.views.update_one(
            {"name": "Master"},
            {"$set": {"targets": master_targets}}
        )
        print(f"  ✓ Updated Master view targets")
    else:
        master_view_data = {
            "id": f"view-master-{int(datetime.now(timezone.utc).timestamp())}",
            "name": "Master",
            "sheet_url": None,  # Master aggregates from other views
            "sheet_name": None,
            "is_master": True,
            "is_default": False,
            "targets": master_targets,
            "aggregates_from": list(created_view_ids.values()),
            "assigned_user": "philippe@primelis.com",
            "created_at": datetime.now(timezone.utc)
        }
        await db.views.insert_one(master_view_data)
        print(f"  ✅ Created Master view with aggregated targets")
    
    print("\n✨ Master view targets (Sum of 3 views):")
    print(f"  - Objectif 6 mois: ${master_targets['dashboard']['objectif_6_mois']:,}")
    print(f"  - Deals: {master_targets['dashboard']['deals']}")
    print(f"  - New Pipe Created: ${master_targets['dashboard']['new_pipe_created']:,}")
    print(f"  - Weighted Pipe: ${master_targets['dashboard']['weighted_pipe']:,}")
    
    print("\n✅ Multi-view setup complete!")
    print("\nView Summary:")
    print("  - Full Funnel (maxime.toubia@primelis.com)")
    print("  - Signal (oren@primelis.com)")
    print("  - Market (coralie.truffy@primelis.com)")
    print("  - Master (philippe@primelis.com + remi + asher)")
    print("  - Organic (existing default view)")

if __name__ == "__main__":
    asyncio.run(setup_multi_views())
