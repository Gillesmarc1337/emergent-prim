from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Query, Request, Response, Cookie, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.security import HTTPBearer
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np
import io
from dateutil import parser
import json
import re
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import requests
from auth import (
    get_session_data_from_emergent,
    get_or_create_user,
    create_session,
    get_current_user,
    get_user_from_session,
    require_super_admin,
    delete_session,
    create_demo_user
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Custom JSON encoder for numpy types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        return super().default(obj)

def json_response(data: Any) -> JSONResponse:
    """Create JSON response with numpy-safe encoding"""
    json_str = json.dumps(data, cls=NumpyEncoder)
    return JSONResponse(content=json.loads(json_str))

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# View to collection mapping
VIEW_COLLECTION_MAP = {
    "Organic": "sales_records",
    "Signal": "sales_records_signal",
    "Full Funnel": "sales_records_fullfunnel",
    "Market": "sales_records_market"
}

def get_collection_for_view(view_name: str):
    """Get MongoDB collection name for a specific view"""
    return VIEW_COLLECTION_MAP.get(view_name, "sales_records")

def get_collections_for_master():
    """Get all collections to aggregate for Master view (includes Organic)"""
    return ["sales_records", "sales_records_signal", "sales_records_fullfunnel", "sales_records_market"]

def safe_int(value):
    """Convert any numeric type (including numpy types) to Python int"""
    if value is None:
        return 0
    if hasattr(value, 'item'):  # numpy type
        return int(value.item())
    return int(value)

def convert_numpy_types(obj):
    """Recursively convert numpy types to native Python types"""
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif hasattr(obj, 'item'):  # other numpy scalar types
        return obj.item()
    elif pd.isna(obj):  # pandas NaN
        return None
    else:
        return obj

def map_admin_targets_to_analytics_format(admin_targets: dict) -> dict:
    """
    Map Admin Back Office target structure to analytics format expected by calculation functions
    
    Admin BO uses:
        - revenue_2025.{month}
        - dashboard_bottom_cards.new_pipe_created, created_weighted_pipe, ytd_revenue
        - meeting_generation.total_target, inbound, outbound, referral, upsells_cross
        - intro_poa.intro, poa
        - meetings_attended.meetings_scheduled, poa_generated, deals_closed
        - deals_closed_current_period.deals_target, arr_target
        - deals_closed_yearly.deals_target, arr_target
        
    Analytics expects:
        - dashboard.objectif_6_mois, deals, new_pipe_created, weighted_pipe
        - meeting_generation.intro, inbound, outbound, referral/referrals, upsells_x
        - meeting_attended.poa, deals_closed
    """
    # Initialize with defaults
    mapped_targets = {
        "dashboard": {
            "objectif_6_mois": 4500000,
            "deals": 25,
            "new_pipe_created": 2000000,
            "weighted_pipe": 800000
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
    
    # If admin_targets is already COMPLETELY in the old format (no new format keys), return as-is
    new_format_keys = ["revenue_2025", "dashboard_bottom_cards", "meeting_generation", "intro_poa", "meetings_attended", "deals_closed_yearly"]
    has_new_format = any(key in admin_targets for key in new_format_keys)
    
    if not has_new_format and "dashboard" in admin_targets and "objectif_6_mois" in admin_targets.get("dashboard", {}):
        return admin_targets
    
    # Map revenue_2025 -> dashboard.objectif_6_mois (sum of all months or use yearly target)
    if "revenue_2025" in admin_targets:
        revenue_sum = sum(admin_targets["revenue_2025"].values())
        if revenue_sum > 0:
            mapped_targets["dashboard"]["objectif_6_mois"] = revenue_sum
    
    # Map deals_closed_yearly -> dashboard.deals (monthly target)
    if "deals_closed_yearly" in admin_targets:
        yearly_deals = admin_targets["deals_closed_yearly"].get("deals_target", 0)
        if yearly_deals > 0:
            mapped_targets["dashboard"]["deals"] = yearly_deals / 12  # Monthly target
    
    # Map dashboard_bottom_cards -> dashboard
    if "dashboard_bottom_cards" in admin_targets:
        bottom_cards = admin_targets["dashboard_bottom_cards"]
        if "new_pipe_created" in bottom_cards and bottom_cards["new_pipe_created"] > 0:
            mapped_targets["dashboard"]["new_pipe_created"] = bottom_cards["new_pipe_created"]
        if "created_weighted_pipe" in bottom_cards and bottom_cards["created_weighted_pipe"] > 0:
            mapped_targets["dashboard"]["weighted_pipe"] = bottom_cards["created_weighted_pipe"]
        if "ytd_aggregate_pipeline" in bottom_cards and bottom_cards["ytd_aggregate_pipeline"] > 0:
            mapped_targets["dashboard"]["ytd_aggregate_pipeline"] = bottom_cards["ytd_aggregate_pipeline"]
        if "ytd_cumulative_weighted" in bottom_cards and bottom_cards["ytd_cumulative_weighted"] > 0:
            mapped_targets["dashboard"]["ytd_cumulative_weighted"] = bottom_cards["ytd_cumulative_weighted"]
        if "ytd_revenue" in bottom_cards and bottom_cards["ytd_revenue"] > 0:
            # This could also map to objectif_6_mois if preferred
            pass
    
    # Map intro_poa -> meeting_generation.intro
    if "intro_poa" in admin_targets:
        intro_poa = admin_targets["intro_poa"]
        if "intro" in intro_poa and intro_poa["intro"] > 0:
            mapped_targets["meeting_generation"]["intro"] = intro_poa["intro"]
        if "poa" in intro_poa and intro_poa["poa"] > 0:
            mapped_targets["meeting_attended"]["poa"] = intro_poa["poa"]
    
    # Map dashboard_banners (NEW from Admin BO Row 2 cards)
    if "dashboard_banners" in admin_targets:
        banners = admin_targets["dashboard_banners"]
        if "intro_target" in banners and banners["intro_target"] > 0:
            mapped_targets["meeting_generation"]["intro"] = banners["intro_target"]
        if "poa_target" in banners and banners["poa_target"] > 0:
            mapped_targets["meeting_attended"]["poa"] = banners["poa_target"]
        if "meetings_generation_target" in banners and banners["meetings_generation_target"] > 0:
            # Total meetings target can be used for validation
            pass
        if "new_pipe_target" in banners and banners["new_pipe_target"] > 0:
            mapped_targets["dashboard"]["new_pipe_created"] = banners["new_pipe_target"]
        if "deals_closed_count" in banners and banners["deals_closed_count"] > 0:
            mapped_targets["dashboard"]["deals"] = banners["deals_closed_count"]
            # Also map to meeting_attended for calculations
            mapped_targets["meeting_attended"]["deals_closed"] = banners["deals_closed_count"]
        if "deals_closed_arr" in banners and banners["deals_closed_arr"] > 0:
            # Store ARR target for deals closed
            mapped_targets["meeting_attended"]["deals_closed_arr"] = banners["deals_closed_arr"]
    
    # Map meeting_generation (new format keeps most of the same keys)
    if "meeting_generation" in admin_targets:
        meeting_gen = admin_targets["meeting_generation"]
        
        # Keep total_target if configured
        if "total_target" in meeting_gen and meeting_gen["total_target"] > 0:
            mapped_targets["meeting_generation"]["total_target"] = meeting_gen["total_target"]
            
        if "inbound" in meeting_gen and meeting_gen["inbound"] > 0:
            mapped_targets["meeting_generation"]["inbound"] = meeting_gen["inbound"]
        if "outbound" in meeting_gen and meeting_gen["outbound"] > 0:
            mapped_targets["meeting_generation"]["outbound"] = meeting_gen["outbound"]
            
        # Support both singular (new) and plural (old) for referral
        if "referral" in meeting_gen and meeting_gen["referral"] > 0:
            mapped_targets["meeting_generation"]["referral"] = meeting_gen["referral"]
            mapped_targets["meeting_generation"]["referrals"] = meeting_gen["referral"]  # Keep both for backward compatibility
        elif "referrals" in meeting_gen and meeting_gen["referrals"] > 0:
            mapped_targets["meeting_generation"]["referral"] = meeting_gen["referrals"]
            mapped_targets["meeting_generation"]["referrals"] = meeting_gen["referrals"]
            
        # Support both upsells_cross (new) and upsells_x (old)
        if "upsells_cross" in meeting_gen and meeting_gen["upsells_cross"] > 0:
            mapped_targets["meeting_generation"]["upsells_cross"] = meeting_gen["upsells_cross"]
            mapped_targets["meeting_generation"]["upsells_x"] = meeting_gen["upsells_cross"]  # Keep both for backward compatibility
        elif "upsells_x" in meeting_gen and meeting_gen["upsells_x"] > 0:
            mapped_targets["meeting_generation"]["upsells_cross"] = meeting_gen["upsells_x"]
            mapped_targets["meeting_generation"]["upsells_x"] = meeting_gen["upsells_x"]
            
        if "event" in meeting_gen and meeting_gen["event"] > 0:
            mapped_targets["meeting_generation"]["event"] = meeting_gen["event"]
    
    # Map meetings_attended
    if "meetings_attended" in admin_targets:
        meetings_att = admin_targets["meetings_attended"]
        if "meetings_scheduled" in meetings_att and meetings_att["meetings_scheduled"] > 0:
            # Store meetings_scheduled in meeting_attended for the calculate function to use
            mapped_targets["meeting_attended"]["meetings_scheduled"] = meetings_att["meetings_scheduled"]
            # Also use it as intro target if intro hasn't been set
            if mapped_targets["meeting_generation"]["intro"] == 45:  # Still default
                mapped_targets["meeting_generation"]["intro"] = meetings_att["meetings_scheduled"]
        if "poa_generated" in meetings_att and meetings_att["poa_generated"] > 0:
            # Only use if dashboard_banners didn't set it (dashboard_banners has priority)
            if "dashboard_banners" not in admin_targets or "poa_target" not in admin_targets.get("dashboard_banners", {}):
                mapped_targets["meeting_attended"]["poa"] = meetings_att["poa_generated"]
        if "deals_closed" in meetings_att and meetings_att["deals_closed"] > 0:
            # Only use if dashboard_banners didn't set it (dashboard_banners has priority)
            if "dashboard_banners" not in admin_targets or "deals_closed_count" not in admin_targets.get("dashboard_banners", {}):
                mapped_targets["meeting_attended"]["deals_closed"] = meetings_att["deals_closed"]
    
    print(f"🔄 Mapped admin targets to analytics format:")
    print(f"   objectif_6_mois: {mapped_targets['dashboard']['objectif_6_mois']}")
    print(f"   new_pipe_created: {mapped_targets['dashboard']['new_pipe_created']}")
    print(f"   meeting intro: {mapped_targets['meeting_generation']['intro']}")
    print(f"   meeting_attended.meetings_scheduled: {mapped_targets['meeting_attended'].get('meetings_scheduled', 'NOT SET')}")
    print(f"   meeting_attended.poa: {mapped_targets['meeting_attended'].get('poa', 'NOT SET')}")
    print(f"   meeting_attended.deals_closed: {mapped_targets['meeting_attended'].get('deals_closed', 'NOT SET')}")
    
    return mapped_targets

async def get_view_config_with_defaults(view_id: str):
    """
    Get view configuration with default targets if not set
    For Master view: auto-calculates from other views if no manual targets saved
    """
    view = await db.views.find_one({"id": view_id})
    if not view:
        raise HTTPException(status_code=404, detail="View not found")
    
    # Default targets (Organic view defaults)
    default_targets = {
        "dashboard": {
            "objectif_6_mois": 4500000,
            "deals": 25,
            "new_pipe_created": 2000000,
            "weighted_pipe": 800000
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
    
    # Check if this is Master view
    is_master = view.get("is_master", False) or view.get("name") == "Master"
    view_targets = view.get("targets", {})
    
    if is_master and not view_targets:
        # Master view with no manual targets: auto-aggregate from other views
        print(f"🔢 Master view: Auto-aggregating targets from other views")
        
        # Get all non-master views
        all_views = await db.views.find({"name": {"$ne": "Master"}}).to_list(100)
        
        # Initialize aggregated targets
        aggregated = {
            "dashboard": {
                "objectif_6_mois": 0,
                "deals": 0,
                "new_pipe_created": 0,
                "weighted_pipe": 0
            },
            "meeting_generation": {
                "intro": 0,
                "inbound": 0,
                "outbound": 0,
                "referrals": 0,
                "upsells_x": 0
            },
            "meeting_attended": {
                "poa": 0,
                "deals_closed": 0
            }
        }
        
        # Sum targets from all other views
        for v in all_views:
            v_targets = v.get("targets", {})
            if v_targets:
                # Map admin format to analytics format for each view
                mapped_v_targets = map_admin_targets_to_analytics_format(v_targets)
                
                # Dashboard targets
                if "dashboard" in mapped_v_targets:
                    for key in aggregated["dashboard"].keys():
                        aggregated["dashboard"][key] += mapped_v_targets["dashboard"].get(key, 0)
                
                # Meeting generation targets
                if "meeting_generation" in mapped_v_targets:
                    for key in aggregated["meeting_generation"].keys():
                        aggregated["meeting_generation"][key] += mapped_v_targets["meeting_generation"].get(key, 0)
                
                # Meeting attended targets
                if "meeting_attended" in mapped_v_targets:
                    for key in aggregated["meeting_attended"].keys():
                        aggregated["meeting_attended"][key] += mapped_v_targets["meeting_attended"].get(key, 0)
        
        view_targets = aggregated
    elif not view_targets:
        view_targets = default_targets
    else:
        # Map admin format to analytics format
        view_targets = map_admin_targets_to_analytics_format(view_targets)
    
    return {
        "view": view,
        "targets": view_targets
    }

async def get_sales_data_for_view(view_id: str):
    """
    Get sales data for a specific view
    - For Master view: aggregates data from Signal, Full Funnel, Market
    - For other views: returns data from view-specific collection
    """
    # Get view from database
    view = await db.views.find_one({"id": view_id})
    if not view:
        raise HTTPException(status_code=404, detail="View not found")
    
    view_name = view.get("name")
    is_master = view.get("is_master", False)
    
    if is_master:
        # Master view: aggregate from multiple collections
        all_records = []
        for collection_name in get_collections_for_master():
            records = await db[collection_name].find().to_list(10000)
            all_records.extend(records)
        return all_records
    else:
        # Regular view: get from specific collection
        collection_name = get_collection_for_view(view_name)
        records = await db[collection_name].find().to_list(10000)
        return records

# Create the main app without a prefix
app = FastAPI(title="Sales Analytics Dashboard", description="Weekly Sales Reports Analysis", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize scheduler for auto-refresh
scheduler = AsyncIOScheduler()

async def auto_refresh_all_views():
    """
    Auto-refresh Google Sheets data for all views (scheduled task)
    Runs twice daily at 12:00 and 20:00 Europe/Paris time
    """
    try:
        print(f"🔄 [AUTO-REFRESH] Started at {datetime.now(timezone.utc).isoformat()}")
        
        # Get all views that have Google Sheets data
        metadata_docs = await db.data_metadata.find({"type": "last_update", "source_type": "google_sheets"}).to_list(100)
        
        if not metadata_docs:
            print("⚠️ [AUTO-REFRESH] No views with Google Sheets found")
            return
        
        success_count = 0
        error_count = 0
        
        for metadata in metadata_docs:
            view_id = metadata.get("view_id", "organic")
            sheet_url = metadata.get("source_url")
            sheet_name = metadata.get("sheet_name")
            collection_name = metadata.get("collection", "sales_records")
            
            try:
                print(f"  📊 Refreshing view: {view_id} (collection: {collection_name})")
                
                # Read fresh data from Google Sheet
                df = read_google_sheet(sheet_url, sheet_name)
                
                if df.empty:
                    print(f"    ⚠️ Google Sheet is empty for {view_id}")
                    continue
                
                # Clean column names
                df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('/', '_')
                
                # Process records
                records = []
                valid_records = 0
                
                for _, row in df.iterrows():
                    if pd.isna(row.get('client')) or str(row.get('client')).strip() == '':
                        continue
                    
                    try:
                        record = SalesRecord(
                            month=str(row.get('month', '')) if not pd.isna(row.get('month')) else None,
                            discovery_date=clean_date(row.get('discovery_date')),
                            client=str(row.get('client', '')).strip(),
                            hubspot_link=str(row.get('hubspot_link', '')) if not pd.isna(row.get('hubspot_link')) else None,
                            stage=str(row.get('stage', '')) if not pd.isna(row.get('stage')) else None,
                            relevance=str(row.get('relevance', '')) if not pd.isna(row.get('relevance')) else None,
                            show_noshow=str(row.get('show_nowshow', '')) if not pd.isna(row.get('show_nowshow')) else None,
                            poa_date=clean_date(row.get('poa_date')),
                            expected_mrr=clean_monetary_value(row.get('expected_mrr')),
                            expected_arr=clean_monetary_value(row.get('expected_arr')),
                            pipeline=clean_monetary_value(row.get('pipeline')),
                            type_of_deal=str(row.get('type_of_deal', '')) if not pd.isna(row.get('type_of_deal')) else None,
                            bdr=str(row.get('bdr', '')) if not pd.isna(row.get('bdr')) else None,
                            type_of_source=str(row.get('type_of_source', '')) if not pd.isna(row.get('type_of_source')) else None,
                            product=str(row.get('product', '')) if not pd.isna(row.get('product')) else None,
                            owner=str(row.get('owner', '')) if not pd.isna(row.get('owner')) else None,
                            supporters=str(row.get('supporters', '')) if not pd.isna(row.get('supporters')) else None,
                            billing_start=clean_date(row.get('billing_start'))
                        )
                        records.append(record.dict())
                        valid_records += 1
                    except Exception as e:
                        continue
                
                # Update database
                if records:
                    await db[collection_name].delete_many({})
                    await db[collection_name].insert_many(records)
                    
                    # Update metadata
                    await db.data_metadata.update_one(
                        {"type": "last_update", "view_id": view_id},
                        {
                            "$set": {
                                "last_update": datetime.now(timezone.utc),
                                "records_count": valid_records,
                                "last_auto_refresh": datetime.now(timezone.utc)
                            }
                        }
                    )
                    
                    print(f"    ✅ Refreshed {valid_records} records for {view_id}")
                    success_count += 1
                else:
                    print(f"    ⚠️ No valid records found for {view_id}")
                    error_count += 1
                    
            except Exception as e:
                print(f"    ❌ Error refreshing {view_id}: {str(e)}")
                error_count += 1
        
        print(f"🎉 [AUTO-REFRESH] Completed: {success_count} success, {error_count} errors")
        
        # Log to database
        await db.auto_refresh_logs.insert_one({
            "timestamp": datetime.now(timezone.utc),
            "success_count": success_count,
            "error_count": error_count,
            "views_processed": len(metadata_docs)
        })
        
    except Exception as e:
        print(f"❌ [AUTO-REFRESH] Fatal error: {str(e)}")
        await db.auto_refresh_logs.insert_one({
            "timestamp": datetime.now(timezone.utc),
            "error": str(e),
            "status": "failed"
        })

# Pydantic Models
class SalesRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    month: Optional[str] = None
    discovery_date: Optional[datetime] = None
    client: Optional[str] = None
    hubspot_link: Optional[str] = None
    stage: Optional[str] = None
    relevance: Optional[str] = None
    show_noshow: Optional[str] = None
    poa_date: Optional[datetime] = None
    expected_mrr: Optional[float] = None
    expected_arr: Optional[float] = None
    pipeline: Optional[float] = None
    type_of_deal: Optional[str] = None
    bdr: Optional[str] = None
    type_of_source: Optional[str] = None
    product: Optional[str] = None
    owner: Optional[str] = None
    supporters: Optional[str] = None
    billing_start: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class WeeklyAnalytics(BaseModel):
    week_start: datetime
    week_end: datetime
    meeting_generation: Dict[str, Any]
    meetings_attended: Dict[str, Any]
    ae_performance: Dict[str, Any]
    attribution: Dict[str, Any]
    deals_closed: Dict[str, Any]
    pipe_metrics: Dict[str, Any]
    old_pipe: Dict[str, Any]
    closing_projections: Dict[str, Any]
    big_numbers_recap: Dict[str, Any]
    dashboard_blocks: Optional[Dict[str, Any]] = None

class UploadResponse(BaseModel):
    message: str
    records_processed: int
    records_valid: int
    analytics_id: Optional[str] = None

class GoogleSheetsRequest(BaseModel):
    sheet_url: str
    sheet_name: Optional[str] = None

class DateRangeRequest(BaseModel):
    start_date: datetime
    end_date: datetime

# Auth Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    email: str
    name: str
    picture: Optional[str] = None
    role: str = "viewer"  # viewer or super_admin
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    
    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

class UserSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    
    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

class View(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    name: str
    sheet_url: Optional[str] = None
    sheet_name: Optional[str] = None
    is_master: bool = False
    is_default: bool = False
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    
    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

class ViewCreateRequest(BaseModel):
    name: str
    sheet_url: Optional[str] = None
    sheet_name: Optional[str] = None
    is_master: bool = False

class SessionDataResponse(BaseModel):
    id: str
    email: str
    name: str
    picture: Optional[str]
    session_token: str

class UserCreateRequest(BaseModel):
    email: str
    name: str
    role: str = "viewer"
    view_access: List[str] = []
    picture: Optional[str] = None

class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    view_access: Optional[List[str]] = None
    picture: Optional[str] = None

class UserRoleUpdateRequest(BaseModel):
    role: str

class UserViewAccessRequest(BaseModel):
    view_access: List[str]

class ProjectionDeal(BaseModel):
    id: str
    hidden: bool = False
    deleted: bool = False  # Permanently deleted deals (user-specific)
    probability: int = 75  # Custom close probability (50, 75, 90)
    order: int = 0  # Position in the column

class ProjectionsPreferencesRequest(BaseModel):
    view_id: str
    preferences: Dict[str, List[ProjectionDeal]]  # e.g., {"next30": [...], "next60": [...], "next90": [...]}

# Utility functions
def clean_records(records):
    """Clean records to ensure all values are JSON serializable"""
    cleaned = []
    for record in records:
        cleaned_record = {}
        for key, value in record.items():
            if pd.isna(value):
                cleaned_record[key] = None
            elif isinstance(value, (np.integer, np.int64, np.int32)):
                cleaned_record[key] = int(value)
            elif isinstance(value, (np.floating, np.float64, np.float32)):
                cleaned_record[key] = float(value)
            elif isinstance(value, np.bool_):
                cleaned_record[key] = bool(value)
            else:
                # Fix encoding for AE names (owner field)
                if key == 'owner' and value:
                    cleaned_record[key] = fix_ae_name_encoding(value)
                else:
                    cleaned_record[key] = value
        cleaned.append(cleaned_record)
    return cleaned

def clean_monetary_value(value):
    """Clean and convert monetary values"""
    if pd.isna(value) or value == '' or value is None:
        return 0.0
    
    if isinstance(value, (int, float)):
        return float(value)
    
    # Remove currency symbols and commas
    cleaned = str(value).replace('$', '').replace(',', '').replace('"', '').strip()
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0

def clean_date(date_value):
    """Clean and parse date values"""
    if pd.isna(date_value) or date_value == '' or date_value is None:
        return None
    
    if isinstance(date_value, datetime):
        return date_value
    
    try:
        # Try parsing different date formats
        return parser.parse(str(date_value))
    except (ValueError, TypeError):
        return None

def get_week_range(date=None):
    """Get start and end date for the week"""
    if date is None:
        date = datetime.now()
    
    # Get Monday of the current week
    days_since_monday = date.weekday()
    monday = date - timedelta(days=days_since_monday)
    sunday = monday + timedelta(days=6)
    
    return monday.replace(hour=0, minute=0, second=0, microsecond=0), \
           sunday.replace(hour=23, minute=59, second=59, microsecond=999999)

def extract_sheet_id_from_url(url):
    """Extract Google Sheet ID from URL"""
    # Pattern to match Google Sheets URLs
    patterns = [
        r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
        r'key=([a-zA-Z0-9-_]+)',
        r'spreadsheets/d/([a-zA-Z0-9-_]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # If no pattern matches, assume the URL is the sheet ID itself
    if len(url) > 20 and '/' not in url:
        return url
        
    raise HTTPException(status_code=400, detail="Invalid Google Sheets URL format")

def read_google_sheet(sheet_url: str, sheet_name: str = None):
    """Read data from Google Sheets using public access"""
    try:
        # Extract sheet ID from URL
        sheet_id = extract_sheet_id_from_url(sheet_url)
        
        # Try to access the sheet publicly first
        if sheet_name:
            # If sheet name is provided, use it
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        else:
            # Use the first sheet (gid=0)
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
        
        # Try to download the CSV
        response = requests.get(csv_url)
        
        if response.status_code == 200:
            # Read CSV data
            csv_data = io.StringIO(response.text)
            df = pd.read_csv(csv_data)
            return df
        else:
            # If public access fails, try alternative URL format
            alt_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
            alt_response = requests.get(alt_url)
            
            if alt_response.status_code == 200:
                csv_data = io.StringIO(alt_response.text)
                df = pd.read_csv(csv_data)
                return df
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cannot access Google Sheet. Make sure the sheet is public or shared. Status: {response.status_code}"
                )
                
    except Exception as e:
        if "Invalid Google Sheets URL format" in str(e):
            raise e
        raise HTTPException(
            status_code=500, 
            detail=f"Error reading Google Sheet: {str(e)}. Make sure the sheet is publicly accessible."
        )

def fix_ae_name_encoding(name):
    """Fix encoding issues for French characters in AE names"""
    if not name:
        return name
    name_str = str(name)
    name_fixes = {
        'RÃ©mi': 'Rémi',
        'FranÃ§ois': 'François',
        'FranÃ§oise': 'Françoise'
    }
    return name_fixes.get(name_str, name_str)

def is_upsell(deal_type):
    """Check if a deal type is an upsell/cross-sell (case-insensitive, handles variations)"""
    if pd.isna(deal_type):
        return False
    deal_type_str = str(deal_type).lower().strip()
    # Match: "upsell", "up-sell", "up sell", "cross-sell", "crosssell"
    return 'upsell' in deal_type_str or 'up-sell' in deal_type_str or 'up sell' in deal_type_str

def is_renewal(deal_type):
    """Check if a deal type is a renewal (case-insensitive)"""
    if pd.isna(deal_type):
        return False
    deal_type_str = str(deal_type).lower().strip()
    # Match: "renew", "renewal", "re-new"
    return 'renew' in deal_type_str

def is_partner_source(source_type):
    """Check if source is a business or consulting partner"""
    if pd.isna(source_type):
        return False
    source_str = str(source_type).lower().strip()
    # Match: "business partner", "consulting partner", "partner"
    return 'partner' in source_str

def calculate_meeting_generation(df, start_date, end_date, view_targets=None):
    """Calculate meeting generation metrics for specified period
    
    Args:
        df: DataFrame with sales data
        start_date: Start date for period
        end_date: End date for period
        view_targets: Optional dict with view-specific targets (from back office)
    """
    period_data = df[
        (df['discovery_date'] >= start_date) & 
        (df['discovery_date'] <= end_date)
    ]
    
    # Split by source type
    inbound = period_data[period_data['type_of_source'] == 'Inbound']
    outbound = period_data[period_data['type_of_source'] == 'Outbound']
    
    # Breakdown referrals by type
    internal_referral = period_data[period_data['type_of_source'] == 'Internal referral']
    external_referral = period_data[period_data['type_of_source'] == 'External referral']
    client_referral = period_data[period_data['type_of_source'] == 'Client referral']
    event = period_data[period_data['type_of_source'] == 'Event']
    
    # None & Non assigned: empty or null type_of_source
    none_unassigned = period_data[
        period_data['type_of_source'].isna() |
        (period_data['type_of_source'] == '')
    ]
    
    # Referrals include: Internal referral, External referral, Client referral ONLY
    referrals = period_data[
        period_data['type_of_source'].isin(['Internal referral', 'External referral', 'Client referral'])
    ]
    
    # Relevance analysis
    relevant = period_data[period_data['relevance'] == 'Relevant']
    question_mark = period_data[period_data['relevance'].isin(['Question mark', 'Maybe'])]
    not_relevant = period_data[period_data['relevance'] == 'Not relevant']
    
    # BDR level detail
    bdr_stats = period_data.groupby('bdr').agg({
        'id': 'count',
        'relevance': lambda x: (x == 'Relevant').sum()
    }).rename(columns={'id': 'total_meetings', 'relevance': 'relevant_meetings'})
    
    # Calculate dynamic targets based on period duration
    period_duration_days = (end_date - start_date).days + 1
    # Calculate exact months for better accuracy
    months_diff = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
    period_duration_months = max(1, months_diff)
    
    # List of BDRs (Business Development Representatives)
    bdr_list = ['Xavier', 'Selma', 'Kenny', 'Marie', 'Gil', 'Louis', 'Yered', 'Killian']
    monthly_bdr_meeting_target = 6  # 6 meetings per month per BDR
    
    # Get targets from view_targets if provided, otherwise use defaults
    if view_targets:
        meeting_gen = view_targets.get("meeting_generation", {})
        monthly_inbound_target = meeting_gen.get("inbound", 22)
        monthly_outbound_target = meeting_gen.get("outbound", 17)
        monthly_referral_target = meeting_gen.get("referral", meeting_gen.get("referrals", 11))
        monthly_event_target = meeting_gen.get("event", 5)
        monthly_upsells_target = meeting_gen.get("upsells_cross", meeting_gen.get("upsells_x", 0))
        
        # Use configured total_target if available, otherwise calculate sum
        if "total_target" in meeting_gen and meeting_gen["total_target"] > 0:
            monthly_total_target = meeting_gen["total_target"]
        else:
            monthly_total_target = monthly_inbound_target + monthly_outbound_target + monthly_referral_target + monthly_event_target
    else:
        # Default targets
        monthly_inbound_target = 22
        monthly_outbound_target = 17 
        monthly_referral_target = 11
        monthly_event_target = 5
        monthly_upsells_target = 0
        monthly_total_target = 55
    
    # Dynamic targets based on period duration
    inbound_target = monthly_inbound_target * period_duration_months
    outbound_target = monthly_outbound_target * period_duration_months
    referral_target = monthly_referral_target * period_duration_months
    total_target = monthly_total_target * period_duration_months
    
    print(f"🎯 Meeting Generation Targets - monthly_total_target: {monthly_total_target}, total_target: {total_target}, period_duration: {period_duration_months}")
    
    # Convert numpy types to Python native types
    total_intros = int(len(period_data))
    
    # Detailed meetings list for table display (matching meetings_attended format)
    meetings_list = []
    for _, row in period_data.iterrows():
        meetings_list.append({
            'date': row['discovery_date'].strftime('%b %d') if pd.notna(row['discovery_date']) else 'N/A',
            'discovery_date': row['discovery_date'].strftime('%Y-%m-%d') if pd.notna(row['discovery_date']) else None,  # Full date for charts
            'client': str(row.get('client', 'N/A')),
            'bdr': str(row.get('bdr', 'N/A')),
            'source': str(row.get('type_of_source', 'N/A')),
            'type_of_source': str(row.get('type_of_source', 'N/A')),  # Add for consistency
            'relevance': str(row.get('relevance', 'N/A')),
            'owner': str(row.get('owner', 'N/A')),  # AE owner
            'stage': str(row.get('stage', 'N/A')),  # Deal stage
            'expected_arr': float(row.get('expected_arr', 0)),  # Column K - Expected ARR
            'poa_date': row['poa_date'].strftime('%Y-%m-%d') if pd.notna(row.get('poa_date')) else None  # Column H - POA Date
        })
    
    return {
        'total_new_intros': total_intros,
        'inbound': int(len(inbound)),
        'outbound': int(len(outbound)),
        'referrals': int(len(referrals)),
        'internal_referral': int(len(internal_referral)),
        'external_referral': int(len(external_referral)),
        'client_referral': int(len(client_referral)),
        'event': int(len(event)),
        'event_target': int(monthly_event_target * period_duration_months) if 'event' in view_targets.get("meeting_generation", {}) else 0,
        'none_unassigned': int(len(none_unassigned)),
        'relevance_analysis': {
            'relevant': int(len(relevant)),
            'question_mark': int(len(question_mark)),
            'not_relevant': int(len(not_relevant)),
            'relevance_rate': float(len(relevant) / len(period_data) * 100 if len(period_data) > 0 else 0)
        },
        'bdr_performance': {k: {
            'total_meetings': int(v['total_meetings']),
            'relevant_meetings': int(v['relevant_meetings']),
            'role': 'BDR' if k in bdr_list else 'AE',
            'meeting_target': monthly_bdr_meeting_target * period_duration_months if k in bdr_list else None
        } for k, v in bdr_stats.to_dict('index').items()} if not bdr_stats.empty else {},
        'meetings_details': meetings_list,
        'target': total_target,
        'inbound_target': inbound_target,
        'outbound_target': outbound_target,
        'referral_target': referral_target,
        'event_target': monthly_event_target * period_duration_months,
        'on_track': bool(total_intros >= total_target)
    }

def calculate_meetings_attended(df, start_date, end_date, view_targets=None):
    """Calculate meetings attended metrics
    
    Args:
        df: DataFrame with sales data
        start_date: Start date for period
        end_date: End date for period
        view_targets: Optional dict with view-specific targets (from back office)
    """
    period_data = df[
        (df['discovery_date'] >= start_date) & 
        (df['discovery_date'] <= end_date)
    ]
    
    # Note: Using stage data as fallback since show_noshow column is empty in the data
    
    # All meetings with details for table
    meetings_detail = period_data[~period_data['client'].isna()].copy()
    meetings_detail['meeting_date'] = meetings_detail['discovery_date']
    meetings_detail['status'] = meetings_detail['show_noshow'].fillna('Scheduled')
    meetings_detail['closed_status'] = meetings_detail['stage'].apply(
        lambda x: 'Closed Won' if x in ['Closed Won', 'Won', 'Signed'] else 
                 ('Closed Lost' if x in ['Closed Lost', 'Lost', 'I Lost'] else 'Open')
    )
    
    # Since show_noshow column is empty, use fallback logic:
    # Meeting Scheduled = all meetings with a discovery_date (meeting was scheduled)
    scheduled_meetings = period_data[period_data['discovery_date'].notna()]
    
    # Meeting Attended = meetings that have progressed beyond just being scheduled
    # (have a stage that indicates the meeting actually happened)
    attended_stages = ['E Intro attended', 'D POA Booked', 'C Proposal sent', 'B Legals', 
                      'Closed Won', 'Won', 'Signed', 'Closed Lost', 'Lost', 'I Lost']
    attended_meetings = period_data[period_data['stage'].isin(attended_stages)]
    
    # POA Generated = POA Booked + Legal + Proposal sent + Closed
    poa_generated_stages = ['D POA Booked', 'POA Booked', 'B Legals', 'Legal', 
                           'C Proposal sent', 'Proposal sent', 
                           'Closed Won', 'Won', 'Signed', 'Closed Lost', 'Lost', 'I Lost']
    poa_generated = period_data[period_data['stage'].isin(poa_generated_stages)]
    
    # Deals Closed = A Closed stage only, filtered by billing_start date (like calculate_deals_closed)
    deals_closed_stages = ['A Closed']
    deals_closed = df[
        (df['stage'].isin(deals_closed_stages)) &
        (df['billing_start'] >= start_date) &
        (df['billing_start'] <= end_date) &
        (df['expected_arr'].notna()) &
        (df['expected_arr'] > 0)
    ]
    
    # AE level performance with corrected calculations
    ae_stats = []
    for owner in period_data['owner'].dropna().unique():
        owner_data = period_data[period_data['owner'] == owner]
        
        # Meetings Scheduled = all meetings with discovery_date
        scheduled = len(owner_data[owner_data['discovery_date'].notna()])
        
        # Meetings Attended = meetings that progressed to attended stages
        attended = len(owner_data[owner_data['stage'].isin(attended_stages)])
        
        # POA Generated (POA Booked + Legal + Proposal sent + Closed)
        poa_gen = len(owner_data[owner_data['stage'].isin(poa_generated_stages)])
        
        # Deals Closed
        closed = len(owner_data[owner_data['stage'].isin(deals_closed_stages)])
        
        # Attendance rate
        attendance_rate = (attended / scheduled * 100) if scheduled > 0 else 0
        
        ae_stats.append({
            'owner': str(owner),
            'total_scheduled': scheduled,
            'attended': attended,
            'poa_generated': poa_gen,
            'deals_closed': closed,
            'attendance_rate': float(attendance_rate)
        })
    
    # Convert numpy types to Python native types
    scheduled_count = int(len(scheduled_meetings))
    attended_count = int(len(attended_meetings))
    poa_generated_count = int(len(poa_generated))
    deals_closed_count = int(len(deals_closed))
    
    # Calculate dynamic targets based on period duration
    period_duration_days = (end_date - start_date).days + 1
    period_duration_months = max(1, round(period_duration_days / 30))  # At least 1 month
    
    # Get targets from view_targets if provided, otherwise use defaults
    if view_targets:
        meeting_att = view_targets.get("meeting_attended", {})
        # meetings_scheduled target is now stored under intro or as a separate value
        base_meetings_target = meeting_att.get("meetings_scheduled", meeting_att.get("intro", 50))
        base_poa_target = meeting_att.get("poa", 30)
        base_deals_target = meeting_att.get("deals_closed", 15)
    else:
        # Base monthly targets (defaults)
        base_meetings_target = 50
        base_poa_target = 30
        base_deals_target = 15
    
    # Dynamic targets based on period duration
    dynamic_meetings_target = base_meetings_target * period_duration_months
    dynamic_poa_target = base_poa_target * period_duration_months
    dynamic_deals_target = base_deals_target * period_duration_months
    
    return {
        'intro_metrics': {
            'target': dynamic_meetings_target,
            'attended': attended_count,
            'scheduled': scheduled_count,
            'attendance_rate': float(attended_count / scheduled_count * 100 if scheduled_count > 0 else 0)
        },
        'poa_generated_metrics': {  # Renamed from discovery_metrics
            'target': dynamic_poa_target,
            'completed': poa_generated_count,
            'conversion_rate': float(poa_generated_count / attended_count * 100 if attended_count > 0 else 0)
        },
        'deals_closed_metrics': {  # Renamed from poa_metrics
            'target': dynamic_deals_target,
            'generated': deals_closed_count,
            'conversion_rate': float(deals_closed_count / poa_generated_count * 100 if poa_generated_count > 0 else 0)
        },
        'ae_performance': ae_stats,  # Use the new ae_stats list directly
        'conversion_rates': {
            'intro_to_poa': {
                'global_rate': float(poa_generated_count / attended_count * 100 if attended_count > 0 else 0),
                'total_intros': attended_count,
                'total_poas': poa_generated_count,
                'by_ae': [
                    {
                        'ae': ae['owner'],
                        'intros': ae['attended'],
                        'poas': ae['poa_generated'],
                        'rate': float(ae['poa_generated'] / ae['attended'] * 100 if ae['attended'] > 0 else 0)
                    }
                    for ae in ae_stats
                ]
            },
            'poa_to_closing': {
                'global_rate': float(deals_closed_count / poa_generated_count * 100 if poa_generated_count > 0 else 0),
                'total_poas': poa_generated_count,
                'total_closed': deals_closed_count,
                'by_ae': [
                    {
                        'ae': ae['owner'],
                        'poas': ae['poa_generated'],
                        'closed': ae['deals_closed'],
                        'rate': float(ae['deals_closed'] / ae['poa_generated'] * 100 if ae['poa_generated'] > 0 else 0)
                    }
                    for ae in ae_stats
                ]
            }
        },
        'meetings_detail': clean_records(meetings_detail[['client', 'meeting_date', 'status', 'closed_status', 'owner', 'stage']].to_dict('records')),
        'monthly_breakdown': {
            'months': [],
            'attended': [],
            'poa_generated': [],
            'deals_closed': []
        } if len(period_data) == 0 else {
            'months': [m.strftime('%b %Y') for m in sorted(period_data.groupby(period_data['discovery_date'].dt.to_period('M')).groups.keys())],
            'attended': [int(len(period_data[(period_data['discovery_date'].dt.to_period('M') == m) & (~period_data['stage'].isin(['F Inbox'])) & (~period_data['show_noshow'].isin(['Noshow']))])) for m in sorted(period_data.groupby(period_data['discovery_date'].dt.to_period('M')).groups.keys())],
            'poa_generated': [int(len(period_data[(period_data['discovery_date'].dt.to_period('M') == m) & (period_data['stage'].isin(['B Legals', 'Legal', 'C Proposal sent', 'Proposal sent', 'D POA Booked', 'POA Booked', 'Closed Won', 'Won', 'Signed', 'A Closed', 'Lost']))])) for m in sorted(period_data.groupby(period_data['discovery_date'].dt.to_period('M')).groups.keys())],
            'deals_closed': [int(len(period_data[(period_data['discovery_date'].dt.to_period('M') == m) & (period_data['stage'] == 'A Closed')])) for m in sorted(period_data.groupby(period_data['discovery_date'].dt.to_period('M')).groups.keys())]
        },
        'on_track': bool(attended_count >= 40 and deals_closed_count >= 15)
    }

def calculate_ae_performance(df, start_date, end_date):
    """Calculate AE performance metrics"""
    period_data = df[
        (df['discovery_date'] >= start_date) & 
        (df['discovery_date'] <= end_date)
    ]
    
    # Intros = tout sauf inbox et noshow
    intros_data = period_data[
        (~period_data['stage'].isin(['F Inbox'])) &
        (~period_data['show_noshow'].isin(['Noshow']))
    ].copy()
    
    # POA Attended = legals, proposal send, POA Booked, Closed, lost
    poa_attended_stages = ['B Legals', 'Legal', 'C Proposal sent', 'Proposal sent', 
                          'D POA Booked', 'POA Booked', 'Closed Won', 'Won', 'Signed', 
                          'Closed Lost', 'Lost', 'I Lost']
    poa_attended_data = period_data[period_data['stage'].isin(poa_attended_stages)]
    
    # POA Closed = Only closed won deals
    poa_closed_stages = ['A Closed']
    poa_closed_data = period_data[period_data['stage'].isin(poa_closed_stages)]
    
    # Legacy POA definition (for backward compatibility) - Updated to include A Closed
    poa_stages = ['A Closed', 'Closed Won', 'Won', 'Signed', 'Closed Lost', 'Lost', 'I Lost', 
                  'B Legals', 'D POA Booked', 'Legal', 'POA Booked']
    poa_data = period_data[period_data['stage'].isin(poa_stages)]
    
    # AE Performance calculation
    ae_performance = []
    ae_poa_performance = []
    
    for ae in intros_data['owner'].dropna().unique():
        ae_intros = intros_data[intros_data['owner'] == ae]
        ae_poas = poa_data[poa_data['owner'] == ae]
        ae_poa_attended = poa_attended_data[poa_attended_data['owner'] == ae]
        ae_poa_closed = poa_closed_data[poa_closed_data['owner'] == ae]
        
        # Relevant intros (assuming relevant means they progressed)
        relevant_intros = ae_intros[ae_intros['relevance'] == 'Relevant']
        
        # Closing value calculation - FIXED: Filter by billing_start (column R) instead of discovery_date
        # This ensures we count closed deals in the period they actually closed, not when they were discovered
        closed_won = df[
            (df['owner'] == ae) & 
            (df['stage'] == 'A Closed') &
            (df['billing_start'] >= start_date) &
            (df['billing_start'] <= end_date)
        ]
        closing_value = float(closed_won['expected_arr'].fillna(0).sum())
        
        ae_performance.append({
            'ae': fix_ae_name_encoding(ae),
            'intros_attended': len(ae_intros),
            'relevant_intro': len(relevant_intros),
            'poa_fait': len(ae_poas),
            'closing': len(closed_won),
            'valeur_closing': closing_value
        })
        
        # POA Performance metrics
        ae_poa_performance.append({
            'ae': fix_ae_name_encoding(ae),
            'poa_attended': len(ae_poa_attended),
            'poa_closed': len(ae_poa_closed)
        })
    
    # Sort by intros attended descending
    ae_performance.sort(key=lambda x: x['intros_attended'], reverse=True)
    ae_poa_performance.sort(key=lambda x: x['poa_attended'], reverse=True)
    
    # Total metrics
    total_intros = len(intros_data)
    total_relevant = len(intros_data[intros_data['relevance'] == 'Relevant'])
    total_poa = len(poa_data)
    total_poa_attended = len(poa_attended_data)
    total_poa_closed = len(poa_closed_data)
    total_closing = len(poa_data[poa_data['stage'].isin(['Closed Won', 'Won', 'Signed'])])
    total_value = float(poa_data[poa_data['stage'].isin(['Closed Won', 'Won', 'Signed'])]['expected_arr'].fillna(0).sum())
    
    # Detailed intros list
    intros_list = []
    for _, row in intros_data.iterrows():
        intros_list.append({
            'date': row['discovery_date'].strftime('%b %d') if pd.notna(row['discovery_date']) else 'N/A',
            'client': str(row.get('client', 'N/A')),
            'ae': fix_ae_name_encoding(row.get('owner', 'N/A')),
            'stage': str(row.get('stage', 'N/A')),
            'relevance': str(row.get('relevance', 'N/A')),
            'expected_arr': float(row.get('expected_arr', 0)) if pd.notna(row.get('expected_arr', 0)) else 0
        })
    
    # Detailed POA attended list
    poa_attended_list = []
    for _, row in poa_attended_data.iterrows():
        poa_attended_list.append({
            'date': row['discovery_date'].strftime('%b %d') if pd.notna(row['discovery_date']) else 'N/A',
            'client': str(row.get('client', 'N/A')),
            'ae': fix_ae_name_encoding(row.get('owner', 'N/A')),
            'stage': str(row.get('stage', 'N/A')),
            'relevance': str(row.get('relevance', 'N/A')),
            'expected_arr': float(row.get('expected_arr', 0)) if pd.notna(row.get('expected_arr', 0)) else 0
        })
    
    return {
        'ae_performance': ae_performance,
        'ae_poa_performance': ae_poa_performance,
        'total_metrics': {
            'total_intros': total_intros,
            'total_relevant': total_relevant,
            'total_poa': total_poa,
            'total_poa_attended': total_poa_attended,
            'total_poa_closed': total_poa_closed,
            'total_closing': total_closing,
            'total_value': total_value
        },
        'intros_details': intros_list,
        'poa_attended_details': poa_attended_list
    }

def calculate_deals_closed(df, start_date, end_date, view_targets=None):
    """Calculate deals closed metrics - based on stage 'A Closed' with billing_start date
    Uses targets from Back Office (deals_closed_current_period)"""
    # Use billing_start (colonne R) as the reference date for when the deal was closed
    # Sum expected_arr (colonne J) for ARR Closed
    closed_deals = df[
        (df['stage'] == 'A Closed') &
        (df['billing_start'] >= start_date) &
        (df['billing_start'] <= end_date) &
        (df['expected_arr'].notna()) &
        (df['expected_arr'] > 0)
    ]
    
    # Monthly breakdown for chart (using billing_start as reference)
    monthly_closed = []
    current_date = start_date
    while current_date <= end_date:
        month_start = current_date.replace(day=1)
        if current_date.month == 12:
            month_end = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(seconds=1)
        else:
            month_end = current_date.replace(month=current_date.month + 1, day=1) - timedelta(seconds=1)
        
        month_deals = closed_deals[
            (closed_deals['billing_start'] >= month_start) &
            (closed_deals['billing_start'] <= month_end)
        ]
        
        monthly_closed.append({
            'month': current_date.strftime('%b %Y'),
            'deals_count': int(len(month_deals)),
            'arr_closed': float(month_deals['expected_arr'].fillna(0).sum()),
            'mrr_closed': float(month_deals['expected_mrr'].fillna(0).sum())
        })
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    # Convert numpy types to Python native types
    deals_count = int(len(closed_deals))
    arr_sum = float(closed_deals['expected_arr'].fillna(0).sum())
    mrr_sum = float(closed_deals['expected_mrr'].fillna(0).sum())
    avg_deal = float(closed_deals['expected_arr'].fillna(0).mean() if len(closed_deals) > 0 else 0)
    
    # Get targets from Back Office (deals_closed_current_period)
    monthly_target_deals = 10  # Default fallback
    monthly_target_arr = 500000  # Default fallback
    
    if view_targets and 'deals_closed_current_period' in view_targets:
        monthly_target_deals = view_targets['deals_closed_current_period'].get('deals_target', 10)
        monthly_target_arr = view_targets['deals_closed_current_period'].get('arr_target', 500000)
    
    # Calculate period length to adjust targets
    period_days = (end_date - start_date).days
    
    # Adjust targets based on period length
    if period_days <= 31:  # Monthly or shorter
        target_deals = monthly_target_deals
        target_arr = monthly_target_arr
    else:  # Longer periods
        # Calculate exact months for better accuracy
        months_diff = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
        months_in_period = months_diff
        target_deals = int(monthly_target_deals * months_in_period)
        target_arr = int(monthly_target_arr * months_in_period)

    return {
        'deals_closed': deals_count,
        'target_deals': target_deals,
        'arr_closed': arr_sum,
        'target_arr': target_arr,
        'mrr_closed': mrr_sum,
        'avg_deal_size': avg_deal,
        'on_track': bool(deals_count >= target_deals or arr_sum >= target_arr),
        'deals_detail': clean_records(closed_deals[['client', 'expected_arr', 'owner', 'type_of_deal']].to_dict('records')),
        'monthly_closed': monthly_closed,
        'period': f"{start_date.strftime('%b %Y')}"  # Add period display
    }

# Centralized Excel weighting function
def calculate_excel_weighted_value(row):
    """Calculate weighted value using exact Excel formula logic"""
    stage = row.get('stage', '')
    source = row.get('type_of_source', '')
    pipeline_value = row.get('pipeline', 0)
    discovery_date = row.get('discovery_date')
    
    # Skip if no pipeline value
    if not pipeline_value or pipeline_value == 0:
        return 0
        
    # Calculate days since creation
    if pd.isna(discovery_date):
        days_since_creation = 0
    else:
        try:
            if isinstance(discovery_date, str):
                discovery_date = pd.to_datetime(discovery_date)
            days_since_creation = (pd.Timestamp.now() - discovery_date).days
        except:
            days_since_creation = 0
    
    # Initialize weight
    weight = 0
    
    # Excel formula implementation - exact replication
    if stage == 'E Intro attended':
        if source == 'Outbound':
            weight = 0.17 if days_since_creation > 180 else 0.15
        elif source == 'Inbound':
            weight = 0.33 if days_since_creation > 90 else 0.35
        elif source == 'Client referral':
            weight = 0 if days_since_creation > 30 else 0.7
        elif source == 'Internal referral':
            weight = 0 if days_since_creation > 30 else 0.6
        elif source == 'Partnership':
            weight = 0.25 if days_since_creation > 60 else 0.4
            
    elif stage == 'D POA Booked':
        weight = 0.5
        
    elif stage == 'C Proposal sent':
        weight = 0.3 if days_since_creation > 90 else 0.5
        
    elif stage == 'B Legals':
        if source == 'Client referral':
            weight = 0 if days_since_creation > 15 else 0.9
        elif source == 'Internal referral':
            weight = 0 if days_since_creation > 15 else 0.85
        elif source == 'Outbound':
            weight = 0.75 if days_since_creation > 45 else 0.9
        elif source == 'Inbound':
            weight = 0.75 if days_since_creation > 45 else 0.9
        elif source == 'Partnership':
            weight = 0.5 if days_since_creation > 30 else 0.8
    
    return float(pipeline_value * weight)

def calculate_pipe_metrics(df, start_date, end_date, targets=None):
    """Calculate pipeline metrics with Excel-exact weighted pipe logic"""
    
    # Filter to only deals with valid pipeline first
    df_with_pipeline = df[
        (df['pipeline'].notna()) & 
        (df['pipeline'] > 0)
    ].copy()
    
    # Apply centralized Excel weighting formula to each row
    df_with_pipeline['weighted_value'] = df_with_pipeline.apply(calculate_excel_weighted_value, axis=1)
    
    # Calculate dynamic targets based on period duration
    period_duration_days = (end_date - start_date).days + 1
    period_duration_months = max(1, round(period_duration_days / 30))
    
    # Base monthly targets - use from targets if provided, otherwise use defaults
    if targets and "dashboard" in targets:
        monthly_new_pipe_target = targets["dashboard"].get("new_pipe_created", 2_000_000)
        monthly_weighted_pipe_target = targets["dashboard"].get("weighted_pipe", 800_000)
    else:
        monthly_new_pipe_target = 2_000_000  # $2M per month (default)
        monthly_weighted_pipe_target = 800_000  # $800K per month (default)
    
    monthly_total_pipe_target = 5_000_000  # $5M (this is overall, not scaled by period)
    monthly_total_weighted_target = 1_500_000  # $1.5M (this is overall, not scaled by period)
    
    # Dynamic targets for created pipe (scales with period)
    created_pipe_target = monthly_new_pipe_target * period_duration_months
    created_weighted_target = monthly_weighted_pipe_target * period_duration_months
    
    # New pipe created in period (Excel logic: ALL deals created in period with valid pipeline)
    new_pipe = df_with_pipeline[
        (df_with_pipeline['discovery_date'] >= start_date) & 
        (df_with_pipeline['discovery_date'] <= end_date)
        # Note: Already filtered to have pipeline > 0
    ]
    
    # Total active pipeline (Excel logic: exclude A Closed, I Lost, H not relevant)
    active_pipe = df_with_pipeline[~df_with_pipeline['stage'].isin(['A Closed', 'I Lost', 'H not relevant'])]
    
    # AE breakdown
    ae_breakdown = []
    for ae in active_pipe['owner'].dropna().unique():
        ae_deals = active_pipe[active_pipe['owner'] == ae]
        ae_new_pipe = new_pipe[new_pipe['owner'] == ae]
        
        ae_breakdown.append({
            'ae': fix_ae_name_encoding(ae),
            'total_pipe': float(ae_deals['pipeline'].sum()),
            'weighted_pipe': float(ae_deals['weighted_value'].sum()),
            'new_pipe_created': float(ae_new_pipe['pipeline'].sum()),
            'new_weighted_pipe': float(ae_new_pipe['weighted_value'].sum()),  # Add weighted value for new pipe
            'deals_count': len(ae_deals),
            'new_deals_count': len(ae_new_pipe)
        })
    
    # Sort by total pipe descending
    ae_breakdown.sort(key=lambda x: x['total_pipe'], reverse=True)
    
    # Convert numpy types to Python native types
    new_pipe_value = float(new_pipe['pipeline'].sum())
    new_weighted_pipe = float(new_pipe['weighted_value'].sum())
    total_pipe_value = float(active_pipe['pipeline'].sum())
    total_weighted_pipe = float(active_pipe['weighted_value'].sum())
    
    return {
        'created_pipe': {
            'value': new_pipe_value,
            'weighted_value': new_weighted_pipe,
            'count': int(len(new_pipe)),
            'target': created_pipe_target,  # Dynamic target based on period
            'target_weighted': created_weighted_target,  # Dynamic target based on period
            'on_track': bool(new_pipe_value >= created_pipe_target)
        },
        'total_pipe': {
            'value': total_pipe_value,
            'weighted_value': total_weighted_pipe,
            'count': int(len(active_pipe)),
            'target': monthly_total_pipe_target,  # Total pipeline target (not period-dependent)
            'target_weighted': monthly_total_weighted_target,  # Total weighted pipeline target (not period-dependent)
            'on_track': bool(total_pipe_value >= monthly_total_pipe_target)
        },
        'ae_breakdown': ae_breakdown,
        'pipe_details': clean_records(active_pipe[['client', 'pipeline', 'weighted_value', 'stage', 'owner']].to_dict('records')),
        'monthly_breakdown': {
            'months': [],
            'new_pipe_created': [],
            'new_weighted_pipe': [],
            'total_pipe': [],
            'total_weighted': []
        } if len(df_with_pipeline) == 0 else {
            'months': [m.strftime('%b %Y') for m in sorted(df_with_pipeline.groupby(df_with_pipeline['discovery_date'].dt.to_period('M')).groups.keys())],
            'new_pipe_created': [float(df_with_pipeline[(df_with_pipeline['discovery_date'].dt.to_period('M') == m) & (df_with_pipeline['discovery_date'] >= start_date) & (df_with_pipeline['discovery_date'] <= end_date)]['pipeline'].sum()) for m in sorted(df_with_pipeline.groupby(df_with_pipeline['discovery_date'].dt.to_period('M')).groups.keys())],
            'new_weighted_pipe': [float(df_with_pipeline[(df_with_pipeline['discovery_date'].dt.to_period('M') == m) & (df_with_pipeline['discovery_date'] >= start_date) & (df_with_pipeline['discovery_date'] <= end_date)]['weighted_value'].sum()) for m in sorted(df_with_pipeline.groupby(df_with_pipeline['discovery_date'].dt.to_period('M')).groups.keys())],
            'total_pipe': [float(df_with_pipeline[(df_with_pipeline['discovery_date'].dt.to_period('M') == m) & (~df_with_pipeline['stage'].isin(['A Closed', 'I Lost', 'H not relevant']))]['pipeline'].sum()) for m in sorted(df_with_pipeline.groupby(df_with_pipeline['discovery_date'].dt.to_period('M')).groups.keys())],
            'total_weighted': [float(df_with_pipeline[(df_with_pipeline['discovery_date'].dt.to_period('M') == m) & (~df_with_pipeline['stage'].isin(['A Closed', 'I Lost', 'H not relevant']))]['weighted_value'].sum()) for m in sorted(df_with_pipeline.groupby(df_with_pipeline['discovery_date'].dt.to_period('M')).groups.keys())]
        }
    }

def calculate_closing_projections(df):
    """Calculate closing projections with Excel-exact weighted pipeline logic"""
    
    # Apply centralized Excel weighting formula
    df['weighted_value'] = df.apply(calculate_excel_weighted_value, axis=1)
    
    # Calculate simplified probability for filtering (approximation for projections)
    stage_probabilities = {
        'B Legals': 85,  # High probability stage
        'C Proposal sent': 50,  # Medium probability stage  
        'D POA Booked': 50,  # Medium probability stage
        'E Intro attended': 25  # Lower probability stage
    }
    df['probability'] = df['stage'].map(stage_probabilities).fillna(0)
    
    # Filter active deals
    active_deals = df[~df['stage'].isin(['Closed Won', 'Closed Lost', 'I Lost'])]
    
    projections_7_days = active_deals[active_deals['probability'] >= 70]
    projections_month = active_deals[active_deals['probability'] >= 50]
    projections_quarter = active_deals[active_deals['probability'] >= 30]
    
    # Convert numpy types to Python native types
    ae_projections = active_deals.groupby('owner').agg({
        'weighted_value': 'sum',
        'pipeline': 'sum'
    })
    
    return {
        'next_7_days': {
            'deals': clean_records(projections_7_days[['client', 'pipeline', 'probability', 'owner', 'stage']].to_dict('records')),
            'total_value': float(projections_7_days['pipeline'].sum()),
            'weighted_value': float(projections_7_days['weighted_value'].sum())
        },
        'current_month': {
            'deals': clean_records(projections_month[['client', 'pipeline', 'probability', 'owner', 'stage']].to_dict('records')),
            'total_value': float(projections_month['pipeline'].sum()),
            'weighted_value': float(projections_month['weighted_value'].sum())
        },
        'next_quarter': {
            'deals': clean_records(projections_quarter[['client', 'pipeline', 'probability', 'owner', 'stage']].to_dict('records')),
            'total_value': float(projections_quarter['pipeline'].sum()),
            'weighted_value': float(projections_quarter['weighted_value'].sum())
        },
        'ae_projections': {fix_ae_name_encoding(k): {
            'weighted_value': float(v['weighted_value']),
            'pipeline': float(v['pipeline'])
        } for k, v in ae_projections.to_dict('index').items()} if not ae_projections.empty else {}
    }

def calculate_hot_deals_closing(df):
    """Calculate hot deals closing in next 2 weeks to 30 days (legals stage)"""
    # Filter deals in legals stage
    legals_deals = df[df['stage'] == 'B Legals'].copy()
    
    if legals_deals.empty:
        return []
    
    # Add expected closing timeframe (2 weeks to 30 days from now)
    today = datetime.now()
    legals_deals['expected_close_start'] = today + timedelta(days=14)
    legals_deals['expected_close_end'] = today + timedelta(days=30)
    
    return clean_records(legals_deals[['id', 'client', 'pipeline', 'expected_mrr', 'expected_arr', 'owner', 'stage', 'hubspot_link']].to_dict('records'))

def calculate_hot_leads(df):
    """Calculate additional hot leads for next 3 months (Proposal sent + PoA booked)"""
    # Filter deals in target stages
    hot_leads = df[df['stage'].isin(['C Proposal sent', 'D POA Booked'])].copy()
    
    if hot_leads.empty:
        return []
    
    # Add expected closing timeframe (next 3 months)
    today = datetime.now()
    hot_leads['expected_close_end'] = today + timedelta(days=90)
    
    return clean_records(hot_leads[['id', 'client', 'pipeline', 'expected_mrr', 'expected_arr', 'owner', 'stage', 'hubspot_link', 'poa_date']].to_dict('records'))

def calculate_aggregate_weighted_pipe(df, target_date):
    """Calculate aggregate weighted pipe using the complex Z17 formula"""
    from datetime import datetime, timedelta, timezone
    
    # Filter data for the target month and year
    target_month = target_date.month
    target_year = target_date.year
    
    # Filter deals for the specific month/year, excluding closed/lost
    filtered_deals = df[
        (df['discovery_date'].dt.month == target_month) &
        (df['discovery_date'].dt.year == target_year) &
        (~df['stage'].isin(['A Closed', 'I Lost'])) &
        (df['pipeline'].notna()) &
        (df['pipeline'] != 0)
    ].copy()
    
    if filtered_deals.empty:
        return 0.0
    
    today = datetime.now()
    total_weighted_value = 0.0
    
    for _, deal in filtered_deals.iterrows():
        pipeline_value = float(deal['pipeline'])
        stage = deal['stage']
        source_type = deal['type_of_source']
        discovery_date = deal['discovery_date']
        
        # Calculate days since discovery
        days_since_discovery = (today - discovery_date).days
        
        # Calculate probability based on stage and source type
        probability = 0.0
        
        if stage == 'E Intro attended':
            if source_type == 'Outbound':
                probability = 0.17 if days_since_discovery > 180 else 0.15
            elif source_type == 'Inbound':
                probability = 0.33 if days_since_discovery > 90 else 0.35
            elif source_type == 'Client referral':
                probability = 0.0 if days_since_discovery > 30 else 0.7
            elif source_type == 'Internal referral':
                probability = 0.0 if days_since_discovery > 30 else 0.6
            elif source_type == 'Partnership':
                probability = 0.25 if days_since_discovery > 60 else 0.4
                
        elif stage == 'D POA Booked':
            probability = 0.5
            
        elif stage == 'C Proposal sent':
            probability = 0.3 if days_since_discovery > 90 else 0.5
            
        elif stage == 'B Legals':
            if source_type == 'Client referral':
                probability = 0.0 if days_since_discovery > 15 else 0.9
            elif source_type == 'Internal referral':
                probability = 0.0 if days_since_discovery > 15 else 0.85
            elif source_type == 'Outbound':
                probability = 0.75 if days_since_discovery > 45 else 0.9
            elif source_type == 'Inbound':
                probability = 0.75 if days_since_discovery > 45 else 0.9
            elif source_type == 'Partnership':
                probability = 0.5 if days_since_discovery > 30 else 0.8
        
        # Calculate weighted value for this deal
        weighted_value = pipeline_value * probability
        total_weighted_value += weighted_value
    
    return float(total_weighted_value)

def calculate_cumulative_aggregate_weighted_pipe(df, target_date):
    """Calculate cumulative aggregate weighted pipe from July to current month"""
    from datetime import datetime
    
    # Start from July 2025
    start_month = 7
    start_year = 2025
    target_month = target_date.month
    target_year = target_date.year
    
    total_cumulative_value = 0.0
    
    # Calculate for each month from July to target month
    current_month = start_month
    current_year = start_year
    
    while (current_year < target_year) or (current_year == target_year and current_month <= target_month):
        # Create date for the current month being processed
        month_date = datetime(current_year, current_month, 1)
        
        # Calculate weighted pipe for this specific month
        monthly_value = calculate_aggregate_weighted_pipe(df, month_date)
        total_cumulative_value += monthly_value
        
        # Move to next month
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1
    
    return float(total_cumulative_value)

# API Endpoints
@api_router.get("/")
async def root():
    return {"message": "Sales Analytics API", "version": "1.0.0"}

# ============= AUTH ENDPOINTS =============
@api_router.post("/auth/session-data")
async def auth_session_data(request: Request, response: Response):
    """
    Handle Emergent OAuth callback - exchange session ID for user session
    """
    try:
        body = await request.json()
        session_id = body.get("sessionId")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID required")
        
        # Get user data from Emergent
        emergent_data = await get_session_data_from_emergent(session_id)
        
        email = emergent_data.get("email")
        name = emergent_data.get("name", email.split("@")[0])
        picture = emergent_data.get("picture")
        
        # Get or create user (checks authorization)
        user = await get_or_create_user(email, name, picture)
        
        # Create session
        session_token = f"session_{user['id']}_{int(datetime.now(timezone.utc).timestamp())}"
        session = await create_session(user["id"], session_token)
        
        # Set cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=7 * 24 * 60 * 60  # 7 days
        )
        
        return {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "picture": user.get("picture"),
            "role": user["role"],
            "session_token": session_token
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")

@api_router.get("/auth/me")
async def get_current_user_info(user: dict = Depends(get_current_user)):
    """
    Get current authenticated user
    """
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "picture": user.get("picture"),
        "role": user["role"]
    }

@api_router.post("/auth/logout")
async def logout(
    response: Response,
    session_token: Optional[str] = Cookie(None)
):
    """
    Logout user and clear session
    """
    if session_token:
        await delete_session(session_token)
    
    response.delete_cookie(key="session_token")
    return {"message": "Logged out successfully"}

@api_router.post("/auth/demo-login")
async def demo_login(response: Response):
    """
    Create demo session for development/testing
    Demo sessions expire after 24 hours
    """
    try:
        # Create or get demo user
        demo_user = await create_demo_user()
        
        # Create demo session (24 hours expiration)
        session_token = f"demo_session_{demo_user['id']}_{int(datetime.now(timezone.utc).timestamp())}"
        session = await create_session(demo_user["id"], session_token, expires_hours=24)
        
        # Set cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=24 * 60 * 60  # 24 hours
        )
        
        return {
            "id": demo_user["id"],
            "email": demo_user["email"],
            "name": demo_user["name"],
            "picture": demo_user.get("picture"),
            "role": demo_user["role"],
            "session_token": session_token,
            "is_demo": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Demo login error: {str(e)}")

# ============= VIEW MANAGEMENT ENDPOINTS =============
@api_router.get("/views")
async def get_views(user: dict = Depends(get_current_user)):
    """
    Get all views (accessible to all authenticated users)
    """
    views = await db.views.find().to_list(100)
    
    # Clean MongoDB _id for JSON (keep custom id field)
    for view in views:
        if '_id' in view:
            del view['_id']
    
    return views

@api_router.post("/views")
async def create_view(
    view_request: ViewCreateRequest,
    user: dict = Depends(require_super_admin)
):
    """
    Create a new view (super admin only)
    """
    view_data = {
        "id": f"view-{int(datetime.now(timezone.utc).timestamp())}",
        "name": view_request.name,
        "sheet_url": view_request.sheet_url,
        "sheet_name": view_request.sheet_name,
        "is_master": view_request.is_master,
        "is_default": False,
        "created_by": user["id"],
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.views.insert_one(view_data)
    
    # Remove _id for response
    if '_id' in view_data:
        del view_data['_id']
    
    return view_data

@api_router.delete("/views/{view_id}")
async def delete_view(
    view_id: str,
    user: dict = Depends(require_super_admin)
):
    """
    Delete a view (super admin only)
    """
    result = await db.views.delete_one({"id": view_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="View not found")
    
    return {"message": "View deleted successfully"}

@api_router.get("/views/{view_id}/config")
async def get_view_config(
    view_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get view configuration including targets
    """
    view = await db.views.find_one({"id": view_id})
    
    if not view:
        raise HTTPException(status_code=404, detail="View not found")
    
    # Clean MongoDB _id for JSON (keep custom id field)
    if '_id' in view:
        del view['_id']
    
    return view

@api_router.put("/admin/views/{view_id}/targets")
async def update_view_targets(
    view_id: str,
    targets: dict,
    user: dict = Depends(get_current_user)
):
    """
    Update targets for a specific view (super_admin only)
    """
    # Check if user is super_admin
    if user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Only super administrators can update targets")
    
    # Get view
    view = await db.views.find_one({"id": view_id})
    if not view:
        raise HTTPException(status_code=404, detail="View not found")
    
    # Update targets
    result = await db.views.update_one(
        {"id": view_id},
        {"$set": {"targets": targets}}
    )
    
    # Check if view was found (matched_count)
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="View not found")
    
    return {"message": "Targets updated successfully", "targets": targets}

@api_router.get("/views/{view_id}/tab-targets")
async def get_tab_targets(
    view_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get DIRECT tab display targets (no multiplication, no mapping)
    Returns: meetings_attended_tab and deals_closed_tab targets
    """
    view = await db.views.find_one({"id": view_id})
    
    if not view:
        raise HTTPException(status_code=404, detail="View not found")
    
    targets = view.get("targets", {})
    
    # Get deals_closed_target from multiple possible sources (with priority)
    deals_closed_target = None
    poa_generated_target = None
    meetings_scheduled_target = None
    
    # Priority 1: Check meetings_attended_tab (from Admin BO - HIGHEST PRIORITY)
    # This is where super_admin configures targets in Back Office
    if "meetings_attended_tab" in targets:
        if "deals_closed_target" in targets["meetings_attended_tab"]:
            deals_closed_target = targets["meetings_attended_tab"]["deals_closed_target"]
        if "poa_generated_target" in targets["meetings_attended_tab"]:
            poa_generated_target = targets["meetings_attended_tab"]["poa_generated_target"]
        if "meetings_scheduled_target" in targets["meetings_attended_tab"]:
            meetings_scheduled_target = targets["meetings_attended_tab"]["meetings_scheduled_target"]
    
    # Priority 2: Check dashboard_banners (only if not set by meetings_attended_tab)
    if "dashboard_banners" in targets:
        if deals_closed_target is None and "deals_closed_count" in targets["dashboard_banners"]:
            deals_closed_target = targets["dashboard_banners"]["deals_closed_count"]
        if poa_generated_target is None and "poa_target" in targets["dashboard_banners"]:
            poa_generated_target = targets["dashboard_banners"]["poa_target"]
    
    # Priority 3: Check meetings_attended (legacy, only if nothing set yet)
    if "meetings_attended" in targets:
        if deals_closed_target is None and "deals_closed" in targets["meetings_attended"]:
            deals_closed_target = targets["meetings_attended"]["deals_closed"]
        if poa_generated_target is None and "poa_generated" in targets["meetings_attended"]:
            poa_generated_target = targets["meetings_attended"]["poa_generated"]
        if meetings_scheduled_target is None and "meetings_scheduled" in targets["meetings_attended"]:
            meetings_scheduled_target = targets["meetings_attended"]["meetings_scheduled"]
    
    # Set defaults if still None
    if deals_closed_target is None:
        deals_closed_target = 6
    if poa_generated_target is None:
        poa_generated_target = 18
    if meetings_scheduled_target is None:
        meetings_scheduled_target = 50
    
    # Get ARR target from dashboard_banners or deals_closed_yearly
    deals_closed_arr = 500000  # default
    if "dashboard_banners" in targets and "deals_closed_arr" in targets["dashboard_banners"]:
        deals_closed_arr = targets["dashboard_banners"]["deals_closed_arr"]
    elif "deals_closed_yearly" in targets and "arr_target" in targets["deals_closed_yearly"]:
        # This is 6-month target, convert to monthly
        deals_closed_arr = targets["deals_closed_yearly"]["arr_target"] / 6
    
    return {
        "meetings_attended_tab": {
            "meetings_scheduled_target": meetings_scheduled_target,
            "poa_generated_target": poa_generated_target,
            "deals_closed_target": deals_closed_target
        },
        "deals_closed_tab": {
            "deals_closed_target": deals_closed_target,
            "arr_closed_target": int(deals_closed_arr)
        }
    }

@api_router.post("/admin/views/{view_id}/sync-targets-from-sheet")
async def sync_targets_from_sheet(
    view_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Sync targets from Google Sheet (reads Target Revenue from columns Y and AL)
    Super_admin only
    """
    # Check if user is super_admin
    if user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Only super administrators can sync targets")
    
    # Get view
    view = await db.views.find_one({"id": view_id})
    if not view:
        raise HTTPException(status_code=404, detail="View not found")
    
    sheet_url = view.get("sheet_url")
    if not sheet_url:
        raise HTTPException(status_code=400, detail="No Google Sheet URL configured for this view")
    
    try:
        # Read Google Sheet to extract targets from columns Y and AL
        df = read_google_sheet(sheet_url, view.get("sheet_name"))
        
        # Initialize default targets structure
        synced_targets = {
            "revenue_2025": {
                "jan": 0, "feb": 0, "mar": 0, "apr": 0, "may": 0, "jun": 0,
                "jul": 0, "aug": 0, "sep": 0, "oct": 0, "nov": 0, "dec": 0
            },
            "meeting_generation": {
                "total_target": 50,
                "inbound": 22,
                "outbound": 17,
                "referral": 11,
                "upsells_cross": 5
            },
            "intro_poa": {
                "intro": 45,
                "poa": 18
            }
        }
        
        # Try to find "Target Revenue" row in the sheet
        # Look for columns with month names (July 2025, August 2025, etc.)
        # This is a simplified version - in production, you'd parse the exact cells Y19, Z19, etc.
        
        # For now, return a message that manual configuration is needed
        # (Full implementation would require parsing specific cells from the sheet)
        
        return {
            "message": "Sync from sheet not yet fully implemented. Please configure targets manually.",
            "note": "Full implementation requires parsing columns Y (2025) and AL (2026) from row 19",
            "current_targets": view.get("targets", {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing from sheet: {str(e)}")

@api_router.get("/views/user/accessible")
async def get_user_accessible_views(user: dict = Depends(get_current_user)):
    """
    Get views accessible to the current user based on their view_access
    """
    user_email = user.get("email")
    view_access = user.get("view_access", [])
    role = user.get("role")
    
    # Super admins, demo user, and specific emails can see all views
    if (role == "super_admin" or 
        user_email in ["remi@primelis.com", "asher@primelis.com", "philippe@primelis.com", "demo@primelis.com"]):
        views = await db.views.find().to_list(100)
    elif view_access:
        # Users with view_access see only their assigned views
        views = await db.views.find({"name": {"$in": view_access}}).to_list(100)
    else:
        # Users without view_access see only default/Organic view
        views = await db.views.find({"$or": [{"is_default": True}, {"name": "Organic"}]}).to_list(100)
    
    # Clean MongoDB _id for JSON (keep custom id field)
    for view in views:
        if '_id' in view:
            del view['_id']
    
    return views

# ============= USER MANAGEMENT ENDPOINTS =============
@api_router.get("/admin/users")
async def get_all_users(user: dict = Depends(require_super_admin)):
    """
    Get all users (super admin only)
    Returns list of users with their roles and view access
    """
    users = await db.users.find().to_list(1000)
    
    # Clean MongoDB _id for JSON and format response
    result = []
    for u in users:
        user_data = {
            "id": u.get("id"),
            "email": u.get("email"),
            "name": u.get("name"),
            "role": u.get("role", "viewer"),
            "view_access": u.get("view_access", []),
            "picture": u.get("picture"),
            "created_at": u.get("created_at").isoformat() if u.get("created_at") else None
        }
        result.append(user_data)
    
    return result

@api_router.post("/admin/users")
async def create_or_update_user(
    user_request: UserCreateRequest,
    user: dict = Depends(require_super_admin)
):
    """
    Create or update a user (super admin only)
    """
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_request.email})
    
    if existing_user:
        # Update existing user
        update_data = {}
        if user_request.name:
            update_data["name"] = user_request.name
        if user_request.role:
            update_data["role"] = user_request.role
        if user_request.view_access is not None:
            update_data["view_access"] = user_request.view_access
        if user_request.picture:
            update_data["picture"] = user_request.picture
        
        await db.users.update_one(
            {"email": user_request.email},
            {"$set": update_data}
        )
        
        # Get updated user
        updated_user = await db.users.find_one({"email": user_request.email})
        return {
            "message": "User updated successfully",
            "user": {
                "id": updated_user.get("id"),
                "email": updated_user.get("email"),
                "name": updated_user.get("name"),
                "role": updated_user.get("role"),
                "view_access": updated_user.get("view_access", [])
            }
        }
    else:
        # Create new user
        user_data = {
            "id": f"user-{user_request.email.split('@')[0]}-{int(datetime.now(timezone.utc).timestamp())}",
            "email": user_request.email,
            "name": user_request.name,
            "picture": user_request.picture,
            "role": user_request.role,
            "view_access": user_request.view_access,
            "created_at": datetime.now(timezone.utc)
        }
        
        await db.users.insert_one(user_data)
        
        return {
            "message": "User created successfully",
            "user": {
                "id": user_data.get("id"),
                "email": user_data.get("email"),
                "name": user_data.get("name"),
                "role": user_data.get("role"),
                "view_access": user_data.get("view_access", [])
            }
        }

@api_router.put("/admin/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role_request: UserRoleUpdateRequest,
    user: dict = Depends(require_super_admin)
):
    """
    Update user role (super admin only)
    """
    # Validate role
    if role_request.role not in ["viewer", "super_admin"]:
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'viewer' or 'super_admin'")
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"role": role_request.role}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": f"User role updated to {role_request.role}"}

@api_router.get("/admin/users/{user_id}/views")
async def get_user_view_access(
    user_id: str,
    user: dict = Depends(require_super_admin)
):
    """
    Get user's view access (super admin only)
    """
    target_user = await db.users.find_one({"id": user_id})
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user_id": user_id,
        "email": target_user.get("email"),
        "view_access": target_user.get("view_access", [])
    }

@api_router.put("/admin/users/{user_id}/views")
async def update_user_view_access(
    user_id: str,
    view_access_request: UserViewAccessRequest,
    user: dict = Depends(require_super_admin)
):
    """
    Update user's view access (super admin only)
    """
    # Verify all views exist
    for view_name in view_access_request.view_access:
        view_exists = await db.views.find_one({"name": view_name})
        if not view_exists:
            raise HTTPException(status_code=400, detail=f"View '{view_name}' not found")
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"view_access": view_access_request.view_access}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "message": "User view access updated successfully",
        "view_access": view_access_request.view_access
    }

@api_router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: str,
    user: dict = Depends(require_super_admin)
):
    """
    Delete a user (super admin only)
    Note: This will also delete all associated sessions
    """
    # Check if user exists
    target_user = await db.users.find_one({"id": user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting self
    if user.get("id") == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    # Delete user's sessions
    await db.user_sessions.delete_many({"user_id": user_id})
    
    # Delete user
    await db.users.delete_one({"id": user_id})
    
    return {"message": f"User {target_user.get('email')} and all associated sessions deleted successfully"}

# ============= USER PROJECTIONS PREFERENCES ENDPOINTS =============
@api_router.post("/user/projections-preferences")
async def save_projections_preferences(
    preferences_request: ProjectionsPreferencesRequest,
    user: dict = Depends(get_current_user)
):
    """
    Save user's projections board preferences (order, hidden deals) per view
    """
    try:
        user_id = user.get("id")
        view_id = preferences_request.view_id
        
        # Convert Pydantic models to dict for MongoDB
        preferences_data = {
            "user_id": user_id,
            "view_id": view_id,
            "preferences": {
                key: [deal.dict() for deal in deals]
                for key, deals in preferences_request.preferences.items()
            },
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Upsert (update if exists, insert if not)
        await db.user_projections_preferences.update_one(
            {"user_id": user_id, "view_id": view_id},
            {"$set": preferences_data},
            upsert=True
        )
        
        return {
            "message": "Projections preferences saved successfully",
            "user_id": user_id,
            "view_id": view_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving preferences: {str(e)}")

@api_router.get("/user/projections-preferences")
async def get_projections_preferences(
    view_id: str = Query(..., description="View ID to get preferences for"),
    user: dict = Depends(get_current_user)
):
    """
    Get user's saved projections board preferences for a specific view
    """
    try:
        user_id = user.get("id")
        
        # Find preferences for this user and view
        preferences_doc = await db.user_projections_preferences.find_one({
            "user_id": user_id,
            "view_id": view_id
        })
        
        if not preferences_doc:
            return {
                "has_preferences": False,
                "preferences": None
            }
        
        # Clean MongoDB _id
        if '_id' in preferences_doc:
            del preferences_doc['_id']
        
        return {
            "has_preferences": True,
            "preferences": preferences_doc.get("preferences"),
            "updated_at": preferences_doc.get("updated_at").isoformat() if preferences_doc.get("updated_at") else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading preferences: {str(e)}")

@api_router.get("/user/projections-preferences/asher")
async def get_asher_projections_preferences(
    view_id: str = Query(..., description="View ID to get Asher's preferences for"),
    user: dict = Depends(get_current_user)
):
    """
    Get Asher's projections board preferences for a specific view (for "Asher POV" feature)
    """
    try:
        # Find Asher's user document
        asher_user = await db.users.find_one({"email": "asher@primelis.com"})
        
        if not asher_user:
            return {
                "has_preferences": False,
                "preferences": None,
                "message": "Asher user not found"
            }
        
        asher_user_id = asher_user.get("id")
        
        # Find Asher's preferences for this view
        preferences_doc = await db.user_projections_preferences.find_one({
            "user_id": asher_user_id,
            "view_id": view_id
        })
        
        if not preferences_doc:
            return {
                "has_preferences": False,
                "preferences": None,
                "message": "Asher has not saved preferences for this view yet"
            }
        
        # Clean MongoDB _id
        if '_id' in preferences_doc:
            del preferences_doc['_id']
        
        return {
            "has_preferences": True,
            "preferences": preferences_doc.get("preferences"),
            "updated_at": preferences_doc.get("updated_at").isoformat() if preferences_doc.get("updated_at") else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading Asher's preferences: {str(e)}")

@api_router.delete("/user/projections-preferences")
async def reset_projections_preferences(
    view_id: str = Query(..., description="View ID to reset preferences for"),
    user: dict = Depends(get_current_user)
):
    """
    Reset user's projections board preferences for a specific view (delete saved state)
    """
    try:
        user_id = user.get("id")
        
        result = await db.user_projections_preferences.delete_one({
            "user_id": user_id,
            "view_id": view_id
        })
        
        if result.deleted_count == 0:
            return {
                "message": "No preferences found to reset (already at default)",
                "reset": True
            }
        
        return {
            "message": "Projections preferences reset successfully",
            "reset": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting preferences: {str(e)}")


@api_router.post("/user/pipeline-board-preferences")
async def save_pipeline_board_preferences(
    request: Request,
    view_id: str = Query(..., description="View ID"),
    user: dict = Depends(get_current_user)
):
    """
    Save user's pipeline board preferences (stage assignments, order) per view for Meetings Generation tab
    """
    try:
        data = await request.json()
        user_email = user.get("email")
        
        # Store in user_preferences collection with user_email + view_id as key
        pref_key = f"{user_email}_{view_id}_pipeline_board"
        
        await db.user_preferences.update_one(
            {"key": pref_key},
            {
                "$set": {
                    "key": pref_key,
                    "user_email": user_email,
                    "view_id": view_id,
                    "type": "pipeline_board",
                    "deal_stages": data.get("deal_stages", {}),  # {deal_id: stage}
                    "deal_order": data.get("deal_order", {}),  # {stage: [deal_ids]}
                    "hidden_deals": data.get("hidden_deals", []),
                    "updated_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
        
        return {"message": "Pipeline board preferences saved successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving pipeline board preferences: {str(e)}")

@api_router.get("/user/pipeline-board-preferences")
async def get_pipeline_board_preferences(
    view_id: str = Query(..., description="View ID"),
    user: dict = Depends(get_current_user)
):
    """
    Get user's saved pipeline board preferences for a specific view
    """
    try:
        user_email = user.get("email")
        pref_key = f"{user_email}_{view_id}_pipeline_board"
        
        preferences = await db.user_preferences.find_one({"key": pref_key})
        
        if not preferences:
            return {
                "deal_stages": {},
                "deal_order": {},
                "hidden_deals": [],
                "has_preferences": False
            }
        
        return {
            "deal_stages": preferences.get("deal_stages", {}),
            "deal_order": preferences.get("deal_order", {}),
            "hidden_deals": preferences.get("hidden_deals", []),
            "has_preferences": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading pipeline board preferences: {str(e)}")

@api_router.delete("/user/pipeline-board-preferences")
async def reset_pipeline_board_preferences(
    view_id: str = Query(..., description="View ID"),
    user: dict = Depends(get_current_user)
):
    """
    Reset pipeline board preferences for a specific view
    """
    try:
        user_email = user.get("email")
        pref_key = f"{user_email}_{view_id}_pipeline_board"
        
        result = await db.user_preferences.delete_one({"key": pref_key})
        
        return {
            "message": "Pipeline board preferences reset successfully",
            "reset": True,
            "deleted_count": result.deleted_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting pipeline board preferences: {str(e)}")

@api_router.post("/upload-data", response_model=UploadResponse)
async def upload_sales_data(
    file: UploadFile = File(...),
    view_id: str = Query(None, description="View ID to associate data with"),
    user: dict = Depends(get_current_user)
):
    """Upload and process sales data CSV file"""
    try:
        # Determine which collection to use
        collection_name = "sales_records"  # Default to Organic
        
        if view_id:
            view = await db.views.find_one({"id": view_id})
            if not view:
                raise HTTPException(status_code=404, detail="View not found")
            
            view_name = view.get("name")
            # Master view cannot upload data (it aggregates from others)
            if view.get("is_master"):
                raise HTTPException(status_code=400, detail="Cannot upload data to Master view. Master aggregates data from other views.")
            
            collection_name = get_collection_for_view(view_name)
        
        # Read the uploaded file
        contents = await file.read()
        
        # Parse CSV
        try:
            df = pd.read_csv(io.BytesIO(contents))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading CSV: {str(e)}")
        
        # Clean column names
        df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('/', '_')
        
        # Process and clean data
        records = []
        valid_records = 0
        
        for _, row in df.iterrows():
            # Skip empty or summary rows
            if pd.isna(row.get('client')) or str(row.get('client')).strip() == '':
                continue
                
            try:
                record = SalesRecord(
                    month=str(row.get('month', '')) if not pd.isna(row.get('month')) else None,
                    discovery_date=clean_date(row.get('discovery_date')),
                    client=str(row.get('client', '')).strip(),
                    hubspot_link=str(row.get('hubspot_link', '')) if not pd.isna(row.get('hubspot_link')) else None,
                    stage=str(row.get('stage', '')) if not pd.isna(row.get('stage')) else None,
                    relevance=str(row.get('relevance', '')) if not pd.isna(row.get('relevance')) else None,
                    show_noshow=str(row.get('show_nowshow', '')) if not pd.isna(row.get('show_nowshow')) else None,
                    poa_date=clean_date(row.get('poa_date')),
                    expected_mrr=clean_monetary_value(row.get('expected_mrr')),
                    expected_arr=clean_monetary_value(row.get('expected_arr')),
                    pipeline=clean_monetary_value(row.get('pipeline')),
                    type_of_deal=str(row.get('type_of_deal', '')) if not pd.isna(row.get('type_of_deal')) else None,
                    bdr=str(row.get('bdr', '')) if not pd.isna(row.get('bdr')) else None,
                    type_of_source=str(row.get('type_of_source', '')) if not pd.isna(row.get('type_of_source')) else None,
                    product=str(row.get('product', '')) if not pd.isna(row.get('product')) else None,
                    owner=str(row.get('owner', '')) if not pd.isna(row.get('owner')) else None,
                    supporters=str(row.get('supporters', '')) if not pd.isna(row.get('supporters')) else None,
                    billing_start=clean_date(row.get('billing_start'))
                )
                records.append(record.dict())
                valid_records += 1
                
            except Exception as e:
                print(f"Error processing row: {str(e)}")
                continue
        
        # Store in MongoDB
        if records:
            # Clear existing data for this view's collection
            await db[collection_name].delete_many({})
            # Insert new data
            await db[collection_name].insert_many(records)
            
            # Save metadata for CSV upload
            await db.data_metadata.update_one(
                {"type": "last_update", "view_id": view_id if view_id else "organic"},
                {
                    "$set": {
                        "last_update": datetime.utcnow(),
                        "source_type": "csv",
                        "source_url": file.filename,
                        "records_count": valid_records,
                        "collection": collection_name
                    }
                },
                upsert=True
            )
        
        return UploadResponse(
            message=f"Successfully processed {len(records)} sales records",
            records_processed=len(df),
            records_valid=valid_records
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

def get_month_range(date=None, month_offset=0):
    """Get start and end date for the month"""
    if date is None:
        date = datetime.now()
    
    # Apply month offset
    target_date = date - timedelta(days=30 * month_offset)
    
    # Get first day of the month
    month_start = target_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Get last day of the month
    if target_date.month == 12:
        month_end = target_date.replace(year=target_date.year + 1, month=1, day=1) - timedelta(seconds=1)
    else:
        month_end = target_date.replace(month=target_date.month + 1, day=1) - timedelta(seconds=1)
    
    return month_start, month_end

@api_router.get("/analytics/yearly")
async def get_yearly_analytics(year: int = 2025, view_id: str = Query(None)):
    """Generate yearly analytics report"""
    try:
        # Get view config and targets if view_id provided
        view_config = None
        view_targets = None
        if view_id:
            config_data = await get_view_config_with_defaults(view_id)
            view_config = config_data["view"]
            view_targets = config_data["targets"]
            # Map admin targets to analytics format
            # Targets already mapped in get_view_config_with_defaults
            records = await get_sales_data_for_view(view_id)
        else:
            # Default targets for Organic view
            view_targets = {
                "dashboard": {
                    "objectif_6_mois": 4500000,
                    "deals": 25,
                    "new_pipe_created": 2000000,
                    "weighted_pipe": 800000
                },
                "meeting_generation": {
                    "intro": 45,
                    "inbound": 22,
                    "outbound": 17,
                    "referrals": 11
                },
                "meeting_attended": {
                    "poa": 18,
                    "deals_closed": 6
                }
            }
            # Fallback to default Organic collection
            records = await db.sales_records.find().to_list(10000)
            
        if not records:
            raise HTTPException(status_code=404, detail="No sales data found. Please upload data first.")
        
        # Calculate year range (January 1 to December 31)
        year_start = datetime(year, 1, 1, 0, 0, 0, 0)
        year_end = datetime(year, 12, 31, 23, 59, 59, 999999)
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(records)
        
        # Convert date strings back to datetime
        date_columns = ['discovery_date', 'poa_date', 'billing_start', 'created_at']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Debug: Print data info
        print(f"Processing {len(df)} total records for year {year}")
        
        # Dashboard blocks for July-December period (6 months)
        # Calculate actual values for July-December period
        july_dec_start = datetime(year, 7, 1)
        july_dec_end = datetime(year, 12, 31, 23, 59, 59, 999999)
        
        # Generate analytics sections - use July-December period for meeting_generation to match dashboard blocks
        meeting_generation = calculate_meeting_generation(df, july_dec_start, july_dec_end, view_targets)
        meetings_attended = calculate_meetings_attended(df, july_dec_start, july_dec_end, view_targets)
        ae_performance = calculate_ae_performance(df, july_dec_start, july_dec_end)
        deals_closed = calculate_deals_closed(df, july_dec_start, july_dec_end, view_targets)
        pipe_metrics = calculate_pipe_metrics(df, july_dec_start, july_dec_end, view_targets)
        closing_projections = calculate_closing_projections(df)
        
        # Attribution analysis
        attribution = {
            'intro_attribution': {k: int(v) for k, v in df.groupby('type_of_source')['id'].count().to_dict().items()},
            'disco_attribution': {k: int(v) for k, v in df[~df['discovery_date'].isna()].groupby('type_of_source')['id'].count().to_dict().items()},
            'bdr_attribution': {k: int(v) for k, v in df.groupby('bdr')['id'].count().to_dict().items()}
        }
        
        # Old pipe (reviving deals)
        old_pipe_data = df[df['stage'].isin(['G Stalled', 'H Lost - can be revived'])]
        old_pipe = {
            'total_stalled_deals': int(len(old_pipe_data)),
            'total_stalled_value': float(old_pipe_data['pipeline'].sum()),
            'companies_to_recontact': int(old_pipe_data['client'].nunique()),
            'revival_opportunities': clean_records(old_pipe_data[['client', 'pipeline', 'stage', 'owner']].to_dict('records'))
        }
        
        # Big numbers recap for the year
        ytd_closed = df[df['stage'].isin(['Closed Won', 'Won', 'Signed'])]
        ytd_revenue = float(ytd_closed['expected_arr'].sum())
        
        # Calculate pipe created (YTD)
        current_year = datetime.now().year
        year_start = datetime(current_year, 1, 1)
        year_end = datetime(current_year, 12, 31, 23, 59, 59)
        ytd_pipe_created = df[
            (df['discovery_date'] >= year_start) &
            (df['discovery_date'] <= year_end)
        ]
        total_pipe_created = float(ytd_pipe_created['pipeline'].sum())
        
        # Calculate active deals count (not lost, not inbox, show and relevant)
        active_deals = df[
            ~df['stage'].isin(['I Lost', 'H Lost - can be revived', 'F Inbox']) &
            (df['show_noshow'] == 'Show') &
            (df['relevance'] == 'Relevant')
        ]
        active_deals_count = len(active_deals)
        
        # Get YTD target from view config (July-December H2 target)
        ytd_target = float(view_targets.get("dashboard", {}).get("objectif_6_mois", 4500000))
        
        big_numbers_recap = {
            'ytd_revenue': ytd_revenue,
            'ytd_target': ytd_target,
            'remaining_target': ytd_target - ytd_revenue,
            'pipe_created': total_pipe_created,
            'active_deals_count': active_deals_count,
            'monthly_breakdown': {str(k): float(v) for k, v in df.groupby(df['discovery_date'].dt.to_period('M'))['pipeline'].sum().to_dict().items()} if len(df) > 0 else {},
            'forecast_gap': ytd_revenue < ytd_target * 0.75
        }
        
        # For realistic testing, let's use a period that has actual data
        # Instead of July-Dec, let's use year-to-date or available data range
        current_date = datetime.now()
        
        # Meeting generation for July-Dec period (only up to current date)
        july_dec_meetings = df[
            (df['discovery_date'] >= july_dec_start) & 
            (df['discovery_date'] <= min(july_dec_end, current_date))
        ]
        
        # Calculate meeting targets from view config for full July-Dec period (6 months)
        # Support both 'referral' (back office) and 'referrals' (setup script) for backward compatibility
        meeting_gen = view_targets.get("meeting_generation", {})
        monthly_inbound_target = meeting_gen.get("inbound", 22)
        monthly_outbound_target = meeting_gen.get("outbound", 17)
        monthly_referral_target = meeting_gen.get("referral", meeting_gen.get("referrals", 11))  # Try singular first, then plural
        monthly_upsells_target = meeting_gen.get("upsells_cross", meeting_gen.get("upsells_x", 0))
        
        # Use configured total_target if available, otherwise calculate sum
        if "total_target" in meeting_gen and meeting_gen["total_target"] > 0:
            monthly_meeting_target = meeting_gen["total_target"]
        else:
            monthly_meeting_target = monthly_inbound_target + monthly_outbound_target + monthly_referral_target
        
        # For yearly analytics, always use full 6-month July-December period
        months_in_july_dec_period = 6  # July, August, September, October, November, December
        
        july_dec_meeting_target = monthly_meeting_target * months_in_july_dec_period
        july_dec_inbound_target = monthly_inbound_target * months_in_july_dec_period
        july_dec_outbound_target = monthly_outbound_target * months_in_july_dec_period
        july_dec_referral_target = monthly_referral_target * months_in_july_dec_period
        
        # Meeting breakdown
        actual_total_july_dec = len(july_dec_meetings)
        actual_inbound_july_dec = len(july_dec_meetings[july_dec_meetings['type_of_source'] == 'Inbound'])
        actual_outbound_july_dec = len(july_dec_meetings[july_dec_meetings['type_of_source'] == 'Outbound'])
        # Include all referral types: Referral, Internal referral, Client referral
        referral_types = ['Referral', 'Internal referral', 'Client referral']
        actual_referral_july_dec = len(july_dec_meetings[july_dec_meetings['type_of_source'].isin(referral_types)])
        actual_show_july_dec = len(july_dec_meetings[july_dec_meetings['show_noshow'] == 'Show'])
        actual_no_show_july_dec = len(july_dec_meetings[july_dec_meetings['show_noshow'] == 'Noshow'])
        
        # Intro & POA for July-Dec period - use view-specific targets
        intro_july_dec = len(july_dec_meetings[july_dec_meetings['show_noshow'] == 'Show'])
        monthly_intro_target = view_targets.get("meeting_generation", {}).get("intro", 45)
        july_dec_intro_target = monthly_intro_target * months_in_july_dec_period
        
        poa_stages = ['D POA Booked', 'C Proposal sent', 'B Legals', 'A Closed']
        poa_july_dec = len(df[
            (df['discovery_date'] >= july_dec_start) & 
            (df['discovery_date'] <= min(july_dec_end, current_date)) &
            (df['stage'].isin(poa_stages))
        ])
        monthly_poa_target = view_targets.get("meeting_attended", {}).get("poa", 18)
        july_dec_poa_target = monthly_poa_target * months_in_july_dec_period
        
        # Upsells / Cross-sells for July-Dec period (Type of deal = "Upsell", "Up-sell", etc.)
        upsells_july_dec = len(df[
            (df['discovery_date'] >= july_dec_start) & 
            (df['discovery_date'] <= min(july_dec_end, current_date)) &
            df['type_of_deal'].apply(is_upsell)
        ])
        july_dec_upsell_target = monthly_upsells_target * months_in_july_dec_period
        
        # New pipe created for July-Dec period
        new_pipe_july_dec = july_dec_meetings['pipeline'].sum()
        
        # Calculate target pipe created from view config
        monthly_pipe_target = view_targets.get("dashboard", {}).get("new_pipe_created", 2000000)
        target_pipe_july_dec = monthly_pipe_target * months_in_july_dec_period
        
        # Calculate weighted pipe for July-Dec period using Excel formula (stage × source × recency)
        july_dec_weighted_data = df[
            (df['discovery_date'] >= july_dec_start) & 
            (df['discovery_date'] <= july_dec_end)
        ].copy()
        
        july_dec_weighted_data['weighted_value'] = july_dec_weighted_data.apply(calculate_excel_weighted_value, axis=1)
        weighted_pipe_july_dec = july_dec_weighted_data['weighted_value'].sum()
        
        # Calculate aggregate weighted pipe (all active deals, not just July-Dec created) using Excel formula
        # This includes all deals regardless of when they were created
        all_active_deals = df[
            ~df['stage'].isin(['I Lost', 'H Lost - can be revived', 'F Inbox', 'A Closed']) &
            (df['show_noshow'] == 'Show') &
            (df['relevance'] == 'Relevant')
        ].copy()
        
        all_active_deals['weighted_value'] = all_active_deals.apply(calculate_excel_weighted_value, axis=1)
        aggregate_weighted_pipe_july_dec = all_active_deals['weighted_value'].sum()
        
        # Revenue for July-Dec period from view config
        total_july_dec_target = float(view_targets.get("dashboard", {}).get("objectif_6_mois", 4500000))
        
        # Calculate actual closed revenue for July-Dec
        closed_deals_july_dec = df[
            (df['billing_start'] >= july_dec_start) & 
            (df['billing_start'] <= july_dec_end) &
            (df['stage'].isin(['A Closed', 'Closed Won', 'Won', 'Signed']))
        ]
        actual_closed_july_dec = closed_deals_july_dec['expected_arr'].sum()
        
        # Calculate unassigned meetings (difference between total and sum of sources)
        sum_of_sources_july_dec = actual_inbound_july_dec + actual_outbound_july_dec + actual_referral_july_dec
        unassigned_july_dec = max(0, actual_total_july_dec - sum_of_sources_july_dec)
        
        dashboard_blocks = {
            'block_1_meetings': {
                'title': 'Meetings Generation',
                'period': f'Jul-Dec 2025 ({months_in_july_dec_period} months)',
                'total_actual': actual_total_july_dec,
                'total_target': july_dec_meeting_target,
                'inbound_actual': actual_inbound_july_dec,
                'inbound_target': july_dec_inbound_target,
                'outbound_actual': actual_outbound_july_dec,
                'outbound_target': july_dec_outbound_target,
                'referral_actual': actual_referral_july_dec,
                'referral_target': july_dec_referral_target,
                'unassigned_actual': unassigned_july_dec,
                'unassigned_target': 0,  # No target for unassigned as it indicates data issue
                'show_actual': actual_show_july_dec,
                'no_show_actual': actual_no_show_july_dec,
                'upsells_actual': upsells_july_dec,
                'upsells_target': july_dec_upsell_target,
                'debug_info': {
                    'months_elapsed': months_in_july_dec_period,
                    'current_month': 12,  # December (end of July-Dec period)
                    'july_dec_start': july_dec_start.isoformat(),
                    'filter_end_date': min(july_dec_end, current_date).isoformat(),
                    'total_meetings_found': len(july_dec_meetings)
                }
            },
            'block_2_intro_poa': {
                'title': 'Intro & POA',
                'period': 'Jul-Dec 2025',
                'intro_actual': intro_july_dec,
                'intro_target': july_dec_intro_target,
                'poa_actual': poa_july_dec,
                'poa_target': july_dec_poa_target,
                'upsells_actual': upsells_july_dec,
                'upsells_target': july_dec_upsell_target
            },
            'block_3_pipe_creation': {
                'title': 'New Pipe Created',
                'new_pipe_created': new_pipe_july_dec,
                'weighted_pipe_created': weighted_pipe_july_dec,
                'aggregate_weighted_pipe': aggregate_weighted_pipe_july_dec,
                'target_pipe_created': target_pipe_july_dec,
                'target_weighted_pipe': view_targets.get("dashboard", {}).get("weighted_pipe", 800000) * months_in_july_dec_period,
                'period': f'Jul-Dec 2025 ({months_in_july_dec_period} months)',
                'debug_info': {
                    'months_elapsed': months_in_july_dec_period,
                    'monthly_target': monthly_pipe_target,
                    'period_target': target_pipe_july_dec
                }
            },
            'block_4_revenue': {
                'title': 'July-December Revenue Objective',
                'revenue_target': total_july_dec_target,
                'closed_revenue': actual_closed_july_dec,
                'progress': (actual_closed_july_dec / total_july_dec_target * 100) if total_july_dec_target > 0 else 0,
                'period': 'Jul-Dec 2025'
            },
            'block_5_upsells': {
                'title': 'Upsells / Cross-sell',
                'period': 'Jul-Dec 2025',
                'closing_actual': len(df[
                    (df['discovery_date'] >= july_dec_start) & 
                    (df['discovery_date'] <= july_dec_end) &
                    df['type_of_deal'].apply(is_upsell) &
                    (df['stage'] == 'A Closed')
                ]),
                'closing_target': 6 * 6,  # 6 closing upsells per month × 6 months
                'closing_value': float(df[
                    (df['discovery_date'] >= july_dec_start) & 
                    (df['discovery_date'] <= july_dec_end) &
                    df['type_of_deal'].apply(is_upsell) &
                    (df['stage'] == 'A Closed')
                ]['expected_arr'].fillna(0).sum())
            }
        }

        analytics = {
            'week_start': july_dec_start,  # July 1st for July To Dec period
            'week_end': july_dec_end,      # December 31st for July To Dec period
            'meeting_generation': meeting_generation,
            'meetings_attended': meetings_attended,
            'ae_performance': ae_performance,
            'attribution': attribution,
            'deals_closed': deals_closed,
            'deals_closed_current_period': deals_closed,  # Same data, for banner display
            'pipe_metrics': pipe_metrics,
            'old_pipe': old_pipe,
            'closing_projections': closing_projections,
            'big_numbers_recap': big_numbers_recap,
            'dashboard_blocks': dashboard_blocks,
            'view_targets': view_targets  # Add view_targets to response
        }
        
        return convert_numpy_types(analytics)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating yearly analytics: {str(e)}")

@api_router.get("/analytics/monthly")
async def get_monthly_analytics(month_offset: int = 0, view_id: str = Query(None)):
    """Generate monthly analytics report"""
    try:
        # Get view config and targets if view_id provided
        view_config = None
        view_targets = None
        if view_id:
            config_data = await get_view_config_with_defaults(view_id)
            view_config = config_data["view"]
            view_targets = config_data["targets"]
            # Map admin targets to analytics format
            # Targets already mapped in get_view_config_with_defaults
        else:
            # Default targets for Organic view
            view_targets = {
                "dashboard": {
                    "objectif_6_mois": 4500000,
                    "deals": 25,
                    "new_pipe_created": 2000000,
                    "weighted_pipe": 800000
                },
                "meeting_generation": {
                    "intro": 45,
                    "inbound": 22,
                    "outbound": 17,
                    "referrals": 11
                },
                "meeting_attended": {
                    "poa": 18,
                    "deals_closed": 6
                }
            }
        
        # Calculate month range based on offset
        if month_offset == 0:
            # Current month (October 2025)
            target_date = datetime(2025, 10, 1)
        else:
            # Navigate from October 2025 base
            base_date = datetime(2025, 10, 1)
            if month_offset > 0:
                # Previous months (September, August, July...)
                target_date = base_date.replace(month=max(1, base_date.month - month_offset))
            else:
                # Future months (November, December...)
                target_date = base_date.replace(month=min(12, base_date.month - month_offset))
        
        month_start, month_end = get_month_range(target_date, 0)
        
        # Get data from MongoDB based on view
        if view_id:
            records = await get_sales_data_for_view(view_id)
        else:
            # Fallback to default Organic collection
            records = await db.sales_records.find().to_list(10000)
            
        if not records:
            raise HTTPException(status_code=404, detail="No sales data found. Please upload data first.")
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(records)
        
        # Convert date strings back to datetime
        date_columns = ['discovery_date', 'poa_date', 'billing_start', 'created_at']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Debug: Print data info
        print(f"Processing {len(df)} total records for period {month_start} to {month_end}")
        print(f"Records with ARR data: {len(df[df['expected_arr'].notna()])}")
        print(f"Records in date range: {len(df[(df['discovery_date'] >= month_start) & (df['discovery_date'] <= month_end)])}")
        
        # Generate all analytics sections
        meeting_generation = calculate_meeting_generation(df, month_start, month_end, view_targets)
        meetings_attended = calculate_meetings_attended(df, month_start, month_end, view_targets)
        ae_performance = calculate_ae_performance(df, month_start, month_end)
        deals_closed = calculate_deals_closed(df, month_start, month_end, view_targets)
        pipe_metrics = calculate_pipe_metrics(df, month_start, month_end, view_targets)
        closing_projections = calculate_closing_projections(df)
        
        # Debug: Print results
        print(f"Deals closed found: {deals_closed['deals_closed']}, ARR: {deals_closed['arr_closed']}")
        
        # Attribution analysis - convert numpy types to Python native types
        attribution = {
            'intro_attribution': {k: int(v) for k, v in df.groupby('type_of_source')['id'].count().to_dict().items()},
            'disco_attribution': {k: int(v) for k, v in df[~df['discovery_date'].isna()].groupby('type_of_source')['id'].count().to_dict().items()},
            'bdr_attribution': {k: int(v) for k, v in df.groupby('bdr')['id'].count().to_dict().items()}
        }
        
        # Old pipe (reviving deals)
        old_pipe_data = df[df['stage'].isin(['G Stalled', 'H Lost - can be revived'])]
        old_pipe = {
            'total_stalled_deals': int(len(old_pipe_data)),
            'total_stalled_value': float(old_pipe_data['pipeline'].sum()),
            'companies_to_recontact': int(old_pipe_data['client'].nunique()),
            'revival_opportunities': clean_records(old_pipe_data[['client', 'pipeline', 'stage', 'owner']].to_dict('records'))
        }
        
        # Big numbers recap
        ytd_closed = df[df['stage'].isin(['Closed Won', 'Won', 'Signed'])]
        ytd_revenue = float(ytd_closed['expected_arr'].sum())
        ytd_target = 4500000  # Should be configurable
        
        # Calculate pipe created (YTD)
        # New pipe created this year (deals discovered this year)
        current_year = datetime.now().year
        year_start = datetime(current_year, 1, 1)
        year_end = datetime(current_year, 12, 31, 23, 59, 59)
        ytd_pipe_created = df[
            (df['discovery_date'] >= year_start) &
            (df['discovery_date'] <= year_end)
        ]
        total_pipe_created = float(ytd_pipe_created['pipeline'].sum())
        
        # Calculate active deals count (not lost, not inbox, show and relevant)
        active_deals = df[
            ~df['stage'].isin(['I Lost', 'H Lost - can be revived', 'F Inbox']) &
            (df['show_noshow'] == 'Show') &
            (df['relevance'] == 'Relevant')
        ]
        active_deals_count = len(active_deals)
        
        big_numbers_recap = {
            'ytd_revenue': ytd_revenue,
            'ytd_target': ytd_target,
            'remaining_target': float(ytd_target - ytd_revenue),
            'pipe_created': total_pipe_created,
            'active_deals_count': active_deals_count,
            'monthly_breakdown': {str(k): float(v) for k, v in df.groupby(df['discovery_date'].dt.to_period('M'))['pipeline'].sum().to_dict().items()},
            'forecast_gap': bool(ytd_revenue < ytd_target * 0.75)
        }
        
        # Calculate dashboard blocks for monthly view
        focus_month = target_date
        focus_month_num = focus_month.month
        focus_month_str = focus_month.strftime('%b %Y')
        
        # Block 1: Meetings Generation (for selected month) - use view-specific targets
        # Support both 'referral' (back office) and 'referrals' (setup script) for backward compatibility
        meeting_gen = view_targets.get("meeting_generation", {})
        target_inbound = meeting_gen.get("inbound", 22)
        target_outbound = meeting_gen.get("outbound", 17)
        target_referral = meeting_gen.get("referral", meeting_gen.get("referrals", 11))  # Try singular first, then plural
        target_upsells = meeting_gen.get("upsells_cross", meeting_gen.get("upsells_x", 0))
        
        # Use configured total_target if available, otherwise calculate sum
        if "total_target" in meeting_gen and meeting_gen["total_target"] > 0:
            target_total = meeting_gen["total_target"]
        else:
            target_total = target_inbound + target_outbound + target_referral
        
        # Calculate actual values for the focus month
        focus_month_meetings = df[
            (df['discovery_date'] >= month_start) & 
            (df['discovery_date'] <= month_end)
        ]
        
        actual_inbound = len(focus_month_meetings[focus_month_meetings['type_of_source'] == 'Inbound'])
        actual_outbound = len(focus_month_meetings[focus_month_meetings['type_of_source'] == 'Outbound'])
        # Include all referral types: Referral, Internal referral, Client referral
        referral_types = ['Referral', 'Internal referral', 'Client referral']
        actual_referral = len(focus_month_meetings[focus_month_meetings['type_of_source'].isin(referral_types)])
        
        # Calculate total meetings and unassigned meetings
        actual_total = len(focus_month_meetings)  # Total meetings in the period
        sum_of_sources_monthly = actual_inbound + actual_outbound + actual_referral
        unassigned_monthly = max(0, actual_total - sum_of_sources_monthly)
        
        # Calculate Show and No Show numbers (case insensitive and flexible matching)
        show_meetings = focus_month_meetings[
            focus_month_meetings['show_noshow'].notna() & 
            focus_month_meetings['show_noshow'].str.strip().str.lower().str.contains('show', na=False) &
            ~focus_month_meetings['show_noshow'].str.strip().str.lower().str.contains('noshow|no show', na=False)
        ]
        no_show_meetings = focus_month_meetings[
            focus_month_meetings['show_noshow'].notna() & 
            focus_month_meetings['show_noshow'].str.strip().str.lower().str.contains('noshow|no show', na=False)
        ]
        actual_show = len(show_meetings)
        actual_no_show = len(no_show_meetings)
        
        # Block 2: Intro & POA (filtered for focus month) - use view-specific targets
        target_intro = view_targets.get("meeting_generation", {}).get("intro", 45)
        target_poa = view_targets.get("meeting_attended", {}).get("poa", 18)
        
        # Intro = "Show" (une intro c'est un "show") for the focus month
        intro_data = df[
            (df['discovery_date'] >= month_start) & 
            (df['discovery_date'] <= month_end) &
            (df['show_noshow'] == 'Show')
        ]
        actual_intro = len(intro_data)
        
        # POA = "D POA Booked", "C Proposal sent", "B Legals", closed ou lost for the focus month
        poa_data = df[
            (df['discovery_date'] >= month_start) & 
            (df['discovery_date'] <= month_end) &
            df['stage'].isin(['D POA Booked', 'C Proposal sent', 'B Legals', 'Closed Won', 'Won', 'Signed', 'Closed Lost', 'I Lost'])
        ]
        actual_poa = len(poa_data)
        
        # Upsells / Cross-sells (Type of deal = "Upsell", "Up-sell", etc.) for the focus month
        upsells_data = df[
            (df['discovery_date'] >= month_start) & 
            (df['discovery_date'] <= month_end) &
            df['type_of_deal'].apply(is_upsell)
        ]
        actual_upsells = len(upsells_data)
        # target_upsells removed - using dynamic targets from view config
        
        # Block 3: Pipe creation - use Excel formula from spreadsheet
        new_pipe_focus_month = df[
            (df['discovery_date'] >= month_start) & 
            (df['discovery_date'] <= month_end) &
            (df['pipeline'].notna()) & 
            (df['pipeline'] > 0)
        ].copy()
        new_pipe_created = float(new_pipe_focus_month['pipeline'].sum())
        
        # Weighted pipe created using Excel formula (stage × source × recency)
        new_pipe_focus_month['weighted_value'] = new_pipe_focus_month.apply(calculate_excel_weighted_value, axis=1)
        weighted_pipe_created = float(new_pipe_focus_month['weighted_value'].sum())
        
        # Calculate aggregate weighted pipe (all active deals) using Excel formula
        all_active_deals_monthly = df[
            ~df['stage'].isin(['I Lost', 'H Lost - can be revived', 'F Inbox', 'A Closed']) &
            (df['show_noshow'] == 'Show') &
            (df['relevance'] == 'Relevant')
        ].copy()
        
        all_active_deals_monthly['weighted_value'] = all_active_deals_monthly.apply(calculate_excel_weighted_value, axis=1)
        aggregate_weighted_pipe_monthly = float(all_active_deals_monthly['weighted_value'].sum())
        
        # Block 4: Revenue objective vs closed - use back office targets or calculate
        revenue_2025 = view_targets.get("revenue_2025", {})
        objectif_6_mois = view_targets.get("dashboard", {}).get("objectif_6_mois", 4500000)
        
        # Map focus month to back office key (e.g., "Jul 2025" -> "jul")
        month_key_map = {
            'Jan 2025': 'jan', 'Feb 2025': 'feb', 'Mar 2025': 'mar',
            'Apr 2025': 'apr', 'May 2025': 'may', 'Jun 2025': 'jun',
            'Jul 2025': 'jul', 'Aug 2025': 'aug', 'Sep 2025': 'sep',
            'Oct 2025': 'oct', 'Nov 2025': 'nov', 'Dec 2025': 'dec'
        }
        month_key = month_key_map.get(focus_month_str, 'jul')
        
        # Use back office target if available, otherwise calculate from distribution
        if revenue_2025 and revenue_2025.get(month_key):
            focus_month_target = safe_int(revenue_2025.get(month_key, 0))
        else:
            # Fallback: Calculate from distribution
            monthly_distribution = {
                'Jul 2025': 0.103, 'Aug 2025': 0.088, 'Sep 2025': 0.122,
                'Oct 2025': 0.24, 'Nov 2025': 0.186, 'Dec 2025': 0.261
            }
            focus_month_target = int(objectif_6_mois * monthly_distribution.get(focus_month_str, 0.167))
        
        # Calculate actual closed revenue from data
        focus_month_closed_deals = df[
            (df['stage'] == 'A Closed') &
            (df['discovery_date'] >= month_start) &
            (df['discovery_date'] <= month_end)
        ]
        focus_month_closed = float(focus_month_closed_deals['expected_arr'].fillna(0).sum())
        
        dashboard_blocks = {
            'block_1_meetings': {
                'title': 'Meetings Generation',
                'period': focus_month_str,
                'total_actual': actual_total,
                'total_target': target_total,
                'inbound_actual': actual_inbound,
                'inbound_target': target_inbound,
                'outbound_actual': actual_outbound,
                'outbound_target': target_outbound,
                'referral_actual': actual_referral,
                'referral_target': target_referral,
                'unassigned_actual': unassigned_monthly,
                'unassigned_target': 0,  # No target for unassigned
                'show_actual': actual_show,
                'no_show_actual': actual_no_show,
                'upsells_actual': actual_upsells,
                'upsells_target': target_upsells
            },
            'block_2_intro_poa': {
                'title': 'Intro & POA',
                'period': focus_month_str,
                'intro_actual': actual_intro,
                'intro_target': target_intro,
                'poa_actual': actual_poa,
                'poa_target': target_poa,
                'upsells_actual': actual_upsells,
                'upsells_target': target_upsells
            },
            'block_3_pipe_creation': {
                'title': 'New Pipe Created',
                'new_pipe_created': new_pipe_created,
                'weighted_pipe_created': weighted_pipe_created,
                'aggregate_weighted_pipe': aggregate_weighted_pipe_monthly,
                'target_pipe_created': view_targets.get("dashboard", {}).get("new_pipe_created", 2000000),  # Use view-specific monthly target
                'target_weighted_pipe': view_targets.get("dashboard", {}).get("weighted_pipe", 800000),  # Weighted pipe target
                'period': focus_month_str
            },
            'block_4_revenue': {
                'title': 'Monthly Revenue Objective',
                'revenue_target': focus_month_target,
                'closed_revenue': focus_month_closed,
                'progress': (focus_month_closed / focus_month_target * 100) if focus_month_target > 0 else 0,
                'period': focus_month_str
            },
            'block_5_upsells': {
                'title': 'Upsells / Cross-sell',
                'period': focus_month_str,
                'closing_actual': len(df[
                    (df['discovery_date'] >= month_start) & 
                    (df['discovery_date'] <= month_end) &
                    df['type_of_deal'].apply(is_upsell) &
                    (df['stage'] == 'A Closed')
                ]),
                'closing_target': view_targets.get("meeting_attended", {}).get("deals_closed", 6),  # Use view-specific monthly target
                'closing_value': float(df[
                    (df['discovery_date'] >= month_start) & 
                    (df['discovery_date'] <= month_end) &
                    df['type_of_deal'].apply(is_upsell) &
                    (df['stage'] == 'A Closed')
                ]['expected_arr'].fillna(0).sum())
            }
        }

        analytics = {
            'week_start': month_start,
            'week_end': month_end,
            'meeting_generation': meeting_generation,
            'meetings_attended': meetings_attended,
            'ae_performance': ae_performance,
            'attribution': attribution,
            'deals_closed': deals_closed,
            'deals_closed_current_period': deals_closed,  # Same data, for banner display
            'pipe_metrics': pipe_metrics,
            'old_pipe': old_pipe,
            'closing_projections': closing_projections,
            'big_numbers_recap': big_numbers_recap,
            'dashboard_blocks': dashboard_blocks,
            'view_targets': view_targets  # Add view_targets to response
        }
        
        return convert_numpy_types(analytics)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating analytics: {str(e)}")

@api_router.get("/analytics/custom")
async def get_custom_analytics(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    view_id: str = Query(None)
):
    """Generate analytics report for custom date range"""
    try:
        # Get view config and targets if view_id provided
        view_config = None
        view_targets = None
        if view_id:
            config_data = await get_view_config_with_defaults(view_id)
            view_config = config_data["view"]
            view_targets = config_data["targets"]
            # Map admin targets to analytics format
            # Targets already mapped in get_view_config_with_defaults
        else:
            # Default targets for Organic view
            view_targets = {
                "dashboard": {
                    "objectif_6_mois": 4500000,
                    "deals": 25,
                    "new_pipe_created": 2000000,
                    "weighted_pipe": 800000
                },
                "meeting_generation": {
                    "intro": 45,
                    "inbound": 22,
                    "outbound": 17,
                    "referrals": 11
                },
                "meeting_attended": {
                    "poa": 18,
                    "deals_closed": 6
                }
            }
        
        # Parse dates
        try:
            custom_start = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
            custom_end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Get data from MongoDB based on view
        if view_id:
            records = await get_sales_data_for_view(view_id)
        else:
            # Fallback to default Organic collection
            records = await db.sales_records.find().to_list(10000)
            
        if not records:
            raise HTTPException(status_code=404, detail="No sales data found. Please upload data first.")
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(records)
        
        # Convert date strings back to datetime
        date_columns = ['discovery_date', 'poa_date', 'billing_start', 'created_at']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Generate all analytics sections using custom date range
        meeting_generation = calculate_meeting_generation(df, custom_start, custom_end, view_targets)
        meetings_attended = calculate_meetings_attended(df, custom_start, custom_end, view_targets)
        ae_performance = calculate_ae_performance(df, custom_start, custom_end)
        deals_closed = calculate_deals_closed(df, custom_start, custom_end, view_targets)
        pipe_metrics = calculate_pipe_metrics(df, custom_start, custom_end, view_targets)
        closing_projections = calculate_closing_projections(df)
        
        # Attribution analysis - convert numpy types to Python native types
        attribution = {
            'intro_attribution': {k: int(v) for k, v in df.groupby('type_of_source')['id'].count().to_dict().items()},
            'disco_attribution': {k: int(v) for k, v in df[~df['discovery_date'].isna()].groupby('type_of_source')['id'].count().to_dict().items()},
            'bdr_attribution': {k: int(v) for k, v in df.groupby('bdr')['id'].count().to_dict().items()}
        }
        
        # Old pipe (reviving deals)
        old_pipe_data = df[df['stage'].isin(['G Stalled', 'H Lost - can be revived'])]
        old_pipe = {
            'total_stalled_deals': int(len(old_pipe_data)),
            'total_stalled_value': float(old_pipe_data['pipeline'].sum()),
            'companies_to_recontact': int(old_pipe_data['client'].nunique()),
            'revival_opportunities': clean_records(old_pipe_data[['client', 'pipeline', 'stage', 'owner']].to_dict('records'))
        }
        
        # Big numbers recap
        ytd_closed = df[df['stage'].isin(['Closed Won', 'Won', 'Signed'])]
        ytd_revenue = float(ytd_closed['expected_arr'].sum())
        ytd_target = 4500000  # Should be configurable
        
        # Calculate pipe created (YTD)
        current_year = datetime.now().year
        year_start = datetime(current_year, 1, 1)
        year_end = datetime(current_year, 12, 31, 23, 59, 59)
        ytd_pipe_created = df[
            (df['discovery_date'] >= year_start) &
            (df['discovery_date'] <= year_end)
        ]
        total_pipe_created = float(ytd_pipe_created['pipeline'].sum())
        
        # Calculate active deals count (not lost, not inbox, show and relevant)
        active_deals = df[
            ~df['stage'].isin(['I Lost', 'H Lost - can be revived', 'F Inbox']) &
            (df['show_noshow'] == 'Show') &
            (df['relevance'] == 'Relevant')
        ]
        active_deals_count = len(active_deals)
        
        big_numbers_recap = {
            'ytd_revenue': ytd_revenue,
            'ytd_target': ytd_target,
            'remaining_target': float(ytd_target - ytd_revenue),
            'pipe_created': total_pipe_created,
            'active_deals_count': active_deals_count,
            'monthly_breakdown': {str(k): float(v) for k, v in df.groupby(df['discovery_date'].dt.to_period('M'))['pipeline'].sum().to_dict().items()},
            'forecast_gap': bool(ytd_revenue < ytd_target * 0.75)
        }
        
        # Calculate dynamic dashboard blocks based on custom period
        period_duration_days = (custom_end - custom_start).days + 1
        period_duration_months = max(1, round(period_duration_days / 30))
        
        # Base monthly targets
        base_meetings_target = 50  # Total monthly meetings target
        base_intro_target = 45     # Monthly intro target  
        base_poa_target = 18       # Monthly POA target
        base_pipe_target = 2000000 # Monthly pipe target ($2M)
        base_revenue_target = 1080000  # Monthly revenue target
        
        # Dynamic targets based on period duration
        dynamic_meetings_target = base_meetings_target * period_duration_months
        dynamic_intro_target = base_intro_target * period_duration_months
        dynamic_poa_target = base_poa_target * period_duration_months
        dynamic_pipe_target = base_pipe_target * period_duration_months
        dynamic_revenue_target = base_revenue_target * period_duration_months
        
        # Filter data for the custom period
        period_data = df[
            (df['discovery_date'] >= custom_start) & 
            (df['discovery_date'] <= custom_end)
        ]
        
        # Calculate actual values for dashboard blocks
        actual_total_meetings = len(period_data[period_data['discovery_date'].notna()])
        actual_inbound = len(period_data[period_data['type_of_source'] == 'Inbound'])
        actual_outbound = len(period_data[period_data['type_of_source'] == 'Outbound'])
        actual_referral = len(period_data[period_data['type_of_source'].isin(['Internal referral', 'Client referral'])])
        
        # Calculate unassigned meetings (difference between total and sum of sources)
        sum_of_sources_custom = actual_inbound + actual_outbound + actual_referral
        unassigned_custom = max(0, actual_total_meetings - sum_of_sources_custom)
        
        # Intro & POA calculations (using updated definitions)
        actual_intro = len(period_data[period_data['show_noshow'] == 'Show'])
        poa_data = period_data[period_data['stage'].isin(['D POA Booked', 'C Proposal sent', 'B Legals', 'A Closed', 'Closed Won', 'Won', 'Signed', 'Closed Lost', 'I Lost'])]
        actual_poa = len(poa_data)
        
        # Upsells / Cross-sells calculations (Type of deal = "Upsell", "Up-sell", etc.)
        upsells_data = period_data[period_data['type_of_deal'].apply(is_upsell)]
        actual_upsells = len(upsells_data)
        target_upsells = 5 * period_duration_months  # 5 upsells per month
        
        # New Pipe and Revenue calculations
        new_pipe_value = float(period_data['pipeline'].fillna(0).sum()) / 1000000  # Convert to millions
        closed_deals = period_data[period_data['stage'] == 'A Closed']
        actual_revenue = float(closed_deals['expected_arr'].fillna(0).sum())
        
        # Dashboard blocks with dynamic targets
        dashboard_blocks = {
            'block_1_meetings': {
                'title': 'Meetings Generation',
                'period': f"{custom_start.strftime('%b %d')} - {custom_end.strftime('%b %d %Y')}",
                'total_actual': actual_total_meetings,
                'total_target': dynamic_meetings_target,
                'inbound_actual': actual_inbound,
                'inbound_target': 22 * period_duration_months,
                'outbound_actual': actual_outbound,
                'outbound_target': 17 * period_duration_months,
                'referral_actual': actual_referral,
                'referral_target': 11 * period_duration_months,
                'unassigned_actual': unassigned_custom,
                'unassigned_target': 0,  # No target for unassigned
                'show_actual': actual_intro,  # Show count for this period
                'no_show_actual': len(period_data[period_data['show_noshow'] == 'Noshow']),
                'upsells_actual': actual_upsells,
                'upsells_target': target_upsells
            },
            'block_2_intro_poa': {
                'title': 'Intro & POA',
                'period': f"{custom_start.strftime('%b %d')} - {custom_end.strftime('%b %d %Y')}",
                'intro_actual': actual_intro,
                'intro_target': dynamic_intro_target,
                'poa_actual': actual_poa,
                'poa_target': dynamic_poa_target,
                'upsells_actual': actual_upsells,
                'upsells_target': target_upsells
            },
            'block_3_new_pipe': {
                'title': 'New Pipe Created',
                'period': f"{custom_start.strftime('%b %d')} - {custom_end.strftime('%b %d %Y')}",
                'pipe_created': new_pipe_value,
                'target': dynamic_pipe_target / 1000000,  # Convert to millions for display
                'weighted_pipe': float(period_data.apply(lambda row: (row['pipeline'] or 0) * 0.3, axis=1).sum()) / 1000000
            },
            'block_4_revenue': {
                'title': 'Revenue Objective',
                'period': f"{custom_start.strftime('%b %d')} - {custom_end.strftime('%b %d %Y')}",
                'target_revenue': dynamic_revenue_target,
                'closed_revenue': actual_revenue,
                'progress': (actual_revenue / dynamic_revenue_target * 100) if dynamic_revenue_target > 0 else 0
            },
            'block_5_upsells': {
                'title': 'Upsells / Cross-sell',
                'period': f"{custom_start.strftime('%b %d')} - {custom_end.strftime('%b %d %Y')}",
                'closing_actual': len(period_data[
                    period_data['type_of_deal'].apply(is_upsell) &
                    (period_data['stage'] == 'A Closed')
                ]),
                'closing_target': 6 * period_duration_months,  # 6 closing upsells per month × months
                'closing_value': float(period_data[
                    period_data['type_of_deal'].apply(is_upsell) &
                    (period_data['stage'] == 'A Closed')
                ]['expected_arr'].fillna(0).sum())
            }
        }
        
        analytics = WeeklyAnalytics(
            week_start=custom_start,
            week_end=custom_end,
            meeting_generation=meeting_generation,
            meetings_attended=meetings_attended,
            ae_performance=ae_performance,
            attribution=attribution,
            deals_closed=deals_closed,
            pipe_metrics=pipe_metrics,
            old_pipe=old_pipe,
            closing_projections=closing_projections,
            big_numbers_recap=big_numbers_recap,
            dashboard_blocks=dashboard_blocks
        )
        
        return analytics
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating custom analytics: {str(e)}")

@api_router.get("/analytics/upsell-renewals")
async def get_upsell_renewals_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    view_id: str = Query(None)
):
    """
    Generate analytics for Upsells/Cross-sells and Renewals brought by Partners.
    Combines Meeting Generation metrics with Partner Performance tables.
    """
    try:
        # Get data from MongoDB based on view
        if view_id:
            records = await get_sales_data_for_view(view_id)
        else:
            # Fallback to default Organic collection
            records = await db.sales_records.find().to_list(10000)
            
        if not records:
            return {
                "period": "No data",
                "total_meetings": 0,
                "business_partner_meetings": 0,
                "consulting_partner_meetings": 0,
                "partner_performance": [],
                "intros_details": [],
                "poa_details": []
            }
        
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        # Convert date columns
        date_columns = ['discovery_date', 'poa_date', 'billing_start', 'created_at']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Determine date range
        if start_date and end_date:
            period_start = datetime.strptime(start_date, '%Y-%m-%d')
            period_end = datetime.strptime(end_date, '%Y-%m-%d')
            period_str = f"{period_start.strftime('%b %d')} - {period_end.strftime('%b %d %Y')}"
        else:
            # Default to current month
            today = datetime.now()
            period_start, period_end = get_month_range(today, 0)
            period_str = period_start.strftime('%b %Y')
        
        # Calculate period duration for dynamic targets
        period_duration_days = (period_end - period_start).days + 1
        period_duration_months = max(1, round(period_duration_days / 30))
        
        # Base monthly targets for upsells/renewals
        monthly_meetings_target = 11  # 11 intro upsell/renewal meetings per month
        monthly_business_partner_target = 9  # 60% from business partners
        monthly_consulting_partner_target = 6  # 40% from consulting partners
        monthly_poa_target = 8  # 8 POA per month
        monthly_closing_target = 4  # 4 closings per month (upsells/cross-sells)
        monthly_closing_value_target = 200_000  # 200K per month for closing value (based on 4 closings × 60K avg deal size)
        monthly_avg_deal_size = 60_000  # 60K average deal size target
        
        # Dynamic targets
        period_meetings_target = monthly_meetings_target * period_duration_months
        period_business_target = monthly_business_partner_target * period_duration_months
        period_consulting_target = monthly_consulting_partner_target * period_duration_months
        period_poa_target = monthly_poa_target * period_duration_months
        period_closing_target = monthly_closing_target * period_duration_months
        period_closing_value_target = monthly_closing_value_target * period_duration_months
        
        # Filter for Upsells/Renewals (column L: Type of deal)
        upsell_renewal_data = df[
            (df['discovery_date'] >= period_start) & 
            (df['discovery_date'] <= period_end) &
            (df['type_of_deal'].apply(is_upsell) | df['type_of_deal'].apply(is_renewal))
        ]
        
        # Meetings breakdown by partner type
        business_partner_meetings = upsell_renewal_data[
            upsell_renewal_data['type_of_source'].str.lower().str.contains('business', na=False)
        ]
        consulting_partner_meetings = upsell_renewal_data[
            upsell_renewal_data['type_of_source'].str.lower().str.contains('consulting', na=False)
        ]
        
        # Show/No Show breakdown
        show_meetings = upsell_renewal_data[
            upsell_renewal_data['show_noshow'].notna() & 
            upsell_renewal_data['show_noshow'].str.strip().str.lower().str.contains('show', na=False) &
            ~upsell_renewal_data['show_noshow'].str.strip().str.lower().str.contains('noshow|no show', na=False)
        ]
        no_show_meetings = upsell_renewal_data[
            upsell_renewal_data['show_noshow'].notna() & 
            upsell_renewal_data['show_noshow'].str.strip().str.lower().str.contains('noshow|no show', na=False)
        ]
        
        # Upsells vs Renewals breakdown
        upsells_only = upsell_renewal_data[upsell_renewal_data['type_of_deal'].apply(is_upsell)]
        renewals_only = upsell_renewal_data[upsell_renewal_data['type_of_deal'].apply(is_renewal)]
        
        # Partner Performance (equivalent to BDR performance)
        partner_performance = []
        
        # Get unique partners (from BDR field - assuming partners are tracked there)
        unique_partners = upsell_renewal_data['bdr'].dropna().unique()
        
        for partner in unique_partners:
            partner_deals = upsell_renewal_data[upsell_renewal_data['bdr'] == partner]
            
            # Intros attended (Show meetings)
            partner_intros = partner_deals[
                partner_deals['show_noshow'].notna() & 
                partner_deals['show_noshow'].str.strip().str.lower().str.contains('show', na=False) &
                ~partner_deals['show_noshow'].str.strip().str.lower().str.contains('noshow|no show', na=False)
            ]
            
            # POA generated (advanced stages)
            poa_stages = ['D POA Booked', 'C Proposal sent', 'B Legals', 'A Closed']
            partner_poa = partner_deals[partner_deals['stage'].isin(poa_stages)]
            
            # Closed deals
            closed_deals = partner_deals[partner_deals['stage'] == 'A Closed']
            closing_value = float(closed_deals['expected_arr'].fillna(0).sum())
            
            partner_performance.append({
                'partner': fix_ae_name_encoding(partner),
                'intros_attended': len(partner_intros),
                'poa_generated': len(partner_poa),
                'closing': len(closed_deals),
                'closing_value': closing_value,
                'upsells': len(partner_deals[partner_deals['type_of_deal'].apply(is_upsell)]),
                'renewals': len(partner_deals[partner_deals['type_of_deal'].apply(is_renewal)])
            })
        
        # Sort by closing value
        partner_performance.sort(key=lambda x: x['closing_value'], reverse=True)
        
        # Intros details
        intros_list = []
        for _, row in show_meetings.iterrows():
            intros_list.append({
                'date': row['discovery_date'].strftime('%b %d') if pd.notna(row['discovery_date']) else 'N/A',
                'client': str(row.get('client', 'N/A')),
                'partner': fix_ae_name_encoding(row.get('bdr', 'N/A')),
                'owner': fix_ae_name_encoding(row.get('owner', 'N/A')),
                'stage': str(row.get('stage', 'N/A')),
                'type_of_deal': str(row.get('type_of_deal', 'N/A')),
                'expected_arr': float(row.get('expected_arr', 0)) if pd.notna(row.get('expected_arr', 0)) else 0
            })
        
        # POA details (advanced stages)
        poa_stages = ['D POA Booked', 'C Proposal sent', 'B Legals', 'A Closed']
        poa_attended_data = upsell_renewal_data[upsell_renewal_data['stage'].isin(poa_stages)]
        
        poa_attended_list = []
        for _, row in poa_attended_data.iterrows():
            poa_attended_list.append({
                'date': row['poa_date'].strftime('%b %d') if pd.notna(row.get('poa_date')) else 'N/A',
                'client': str(row.get('client', 'N/A')),
                'partner': fix_ae_name_encoding(row.get('bdr', 'N/A')),
                'owner': fix_ae_name_encoding(row.get('owner', 'N/A')),
                'stage': str(row.get('stage', 'N/A')),
                'type_of_deal': str(row.get('type_of_deal', 'N/A')),
                'expected_arr': float(row.get('expected_arr', 0)) if pd.notna(row.get('expected_arr', 0)) else 0
            })
        
        return {
            'period': period_str,
            'period_duration_months': period_duration_months,
            
            # Meeting metrics
            'total_meetings': len(upsell_renewal_data),
            'total_target': period_meetings_target,
            'business_partner_meetings': len(business_partner_meetings),
            'business_partner_target': period_business_target,
            'consulting_partner_meetings': len(consulting_partner_meetings),
            'consulting_partner_target': period_consulting_target,
            
            # Show/No Show
            'show_actual': len(show_meetings),
            'no_show_actual': len(no_show_meetings),
            
            # Upsells vs Renewals
            'upsells_actual': len(upsells_only),
            'renewals_actual': len(renewals_only),
            
            # POA and Closing
            'poa_actual': len(poa_attended_data),
            'poa_target': period_poa_target,
            'closing_actual': len(upsell_renewal_data[upsell_renewal_data['stage'] == 'A Closed']),
            'closing_target': period_closing_target,
            'closing_value': float(upsell_renewal_data[upsell_renewal_data['stage'] == 'A Closed']['expected_arr'].fillna(0).sum()),
            'closing_value_target': period_closing_value_target,
            
            # Performance data
            'partner_performance': partner_performance,
            'intros_details': intros_list,
            'poa_details': poa_attended_list,
            
            # Monthly breakdown
            'monthly_breakdown': {
                'months': [],
                'meetings_attended': [],
                'poa_generated': [],
                'revenue_generated': []
            } if len(upsell_renewal_data) == 0 else {
                'months': [m.strftime('%b %Y') for m in sorted(upsell_renewal_data.groupby(upsell_renewal_data['discovery_date'].dt.to_period('M')).groups.keys())],
                'meetings_attended': [int(len(upsell_renewal_data[(upsell_renewal_data['discovery_date'].dt.to_period('M') == m) & (upsell_renewal_data['show_noshow'].notna()) & (upsell_renewal_data['show_noshow'].str.strip().str.lower().str.contains('show', na=False)) & (~upsell_renewal_data['show_noshow'].str.strip().str.lower().str.contains('noshow|no show', na=False))])) for m in sorted(upsell_renewal_data.groupby(upsell_renewal_data['discovery_date'].dt.to_period('M')).groups.keys())],
                'poa_generated': [int(len(upsell_renewal_data[(upsell_renewal_data['discovery_date'].dt.to_period('M') == m) & (upsell_renewal_data['stage'].isin(['B Legals', 'Legal', 'C Proposal sent', 'Proposal sent', 'D POA Booked', 'POA Booked', 'Closed Won', 'Won', 'Signed', 'A Closed', 'Lost']))])) for m in sorted(upsell_renewal_data.groupby(upsell_renewal_data['discovery_date'].dt.to_period('M')).groups.keys())],
                'revenue_generated': [float(upsell_renewal_data[(upsell_renewal_data['discovery_date'].dt.to_period('M') == m) & (upsell_renewal_data['stage'] == 'A Closed')]['expected_arr'].fillna(0).sum()) for m in sorted(upsell_renewal_data.groupby(upsell_renewal_data['discovery_date'].dt.to_period('M')).groups.keys())]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating upsell/renewal analytics: {str(e)}")

@api_router.get("/analytics/dashboard")
async def get_dashboard_analytics(view_id: str = Query(None)):
    """Generate main dashboard with revenue charts"""
    try:
        # Get view config and targets if view_id provided
        view_config = None
        view_targets = None
        if view_id:
            config_data = await get_view_config_with_defaults(view_id)
            view_config = config_data["view"]
            view_targets = config_data["targets"]
            # Map admin targets to analytics format
            # Targets already mapped in get_view_config_with_defaults
            records = await get_sales_data_for_view(view_id)
        else:
            # Fallback to default Organic collection with default targets
            records = await db.sales_records.find().to_list(10000)
            view_targets = {
                "dashboard": {
                    "objectif_6_mois": 4500000,
                    "deals": 25,
                    "new_pipe_created": 2000000,
                    "weighted_pipe": 800000
                }
            }
            
        if not records:
            raise HTTPException(status_code=404, detail="No sales data found. Please upload data first.")
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(records)
        
        # Convert date strings back to datetime
        date_columns = ['discovery_date', 'poa_date', 'billing_start', 'created_at']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Get monthly targets from back office (revenue_2025) or calculate from 6-month target
        revenue_2025 = view_targets.get("revenue_2025", {})
        objectif_6_mois = view_targets.get("dashboard", {}).get("objectif_6_mois", 4500000)
        
        # Use back office targets if available, otherwise calculate from distribution
        if revenue_2025 and any(revenue_2025.values()):
            # Back office has specific monthly targets - use them!
            monthly_targets_2025 = {
                'Jan 2025': safe_int(revenue_2025.get('jan', 0)),
                'Feb 2025': safe_int(revenue_2025.get('feb', 0)),
                'Mar 2025': safe_int(revenue_2025.get('mar', 0)),
                'Apr 2025': safe_int(revenue_2025.get('apr', 0)),
                'May 2025': safe_int(revenue_2025.get('may', 0)),
                'Jun 2025': safe_int(revenue_2025.get('jun', 0)),
                'Jul 2025': safe_int(revenue_2025.get('jul', 0)),
                'Aug 2025': safe_int(revenue_2025.get('aug', 0)),
                'Sep 2025': safe_int(revenue_2025.get('sep', 0)),
                'Oct 2025': safe_int(revenue_2025.get('oct', 0)),
                'Nov 2025': safe_int(revenue_2025.get('nov', 0)),
                'Dec 2025': safe_int(revenue_2025.get('dec', 0))
            }
        else:
            # Fallback: Calculate from distribution if back office targets not set
            monthly_distribution = {
                'Jul': 0.103, 'Aug': 0.088, 'Sep': 0.122,
                'Oct': 0.24, 'Nov': 0.186, 'Dec': 0.261
            }
            monthly_targets_2025 = {
                'Jan 2025': 0, 'Feb 2025': 0, 'Mar 2025': 0, 
                'Apr 2025': 0, 'May 2025': 0, 'Jun 2025': 0,
                'Jul 2025': int(objectif_6_mois * monthly_distribution['Jul']),
                'Aug 2025': int(objectif_6_mois * monthly_distribution['Aug']),
                'Sep 2025': int(objectif_6_mois * monthly_distribution['Sep']),
                'Oct 2025': int(objectif_6_mois * monthly_distribution['Oct']),
                'Nov 2025': int(objectif_6_mois * monthly_distribution['Nov']),
                'Dec 2025': int(objectif_6_mois * monthly_distribution['Dec'])
            }
        
        # Get current date and analyze data
        today = datetime.now()
        months_data = []
        
        # Focus on July to December 2025 period (H2) - chart data
        base_date = datetime(2025, 7, 1)  # July 2025 as starting point
        target_months = []
        for month_offset in range(6):  # July, Aug, Sep, Oct, Nov, Dec
            target_date = base_date.replace(month=base_date.month + month_offset)
            target_months.append(target_date)
        
        for target_date in target_months:
            month_start, month_end = get_month_range(target_date, 0)
            month_str = target_date.strftime('%b %Y')
            
            # Get targets from monthly_targets_2025 (calculated from view config - Back Office)
            target_revenue = monthly_targets_2025.get(month_str, 0)
            
            # Calculate actual closed revenue from sheet data (stage "A Closed" only)
            closed_deals = df[
                (df['stage'] == 'A Closed') &
                (df['discovery_date'] >= month_start) & 
                (df['discovery_date'] <= month_end) &
                (df['expected_arr'].notna()) & 
                (df['expected_arr'] != 0)
            ]
            closed_revenue = float(closed_deals['expected_arr'].fillna(0).sum())
            
            # Calculate New Weighted Pipe (new deals created in this month) using Excel formula
            new_deals_month = df[
                (df['discovery_date'] >= month_start) & 
                (df['discovery_date'] <= month_end) &
                (df['pipeline'].notna()) & 
                (df['pipeline'] != 0)
            ].copy()
            
            # Apply Excel weighting formula
            new_deals_month['weighted_value'] = new_deals_month.apply(calculate_excel_weighted_value, axis=1)
            new_weighted_pipe = float(new_deals_month['weighted_value'].sum())
            
            # Calculate New Pipe Created (sum of column K - pipeline for new deals in this month)
            new_pipe_created = float(new_deals_month['pipeline'].fillna(0).sum())
            
            # Weighted pipeline for display (not used in chart, kept for compatibility)
            weighted_pipe = new_weighted_pipe
            
            # Aggregate Weighted Pipe (cumulative from July to current month only)
            current_date = datetime.now()
            
            # Only show aggregate weighted pipe for past and current months
            if target_date <= current_date:
                aggregate_weighted_pipe = calculate_cumulative_aggregate_weighted_pipe(df, target_date)
            else:
                # For future months, set to None or 0 so it doesn't display
                aggregate_weighted_pipe = None
            
            months_data.append({
                'month': month_str,
                'target_revenue': target_revenue,
                'closed_revenue': closed_revenue,
                'weighted_pipe': weighted_pipe,
                'new_weighted_pipe': new_weighted_pipe,
                'new_pipe_created': new_pipe_created,  # Add Created Pipe (column K sum)
                'aggregate_weighted_pipe': aggregate_weighted_pipe,
                'is_future': target_date > datetime.now(),
                'deals_count': len(closed_deals)
            })
        
        # Calculate YTD metrics for 2025 (July-December period)
        # YTD closed revenue = sum of expected_arr (colonne J) for deals with stage "A Closed" 
        # with billing_start (colonne R) from July to December 2025
        current_year = datetime.now().year
        year_start = datetime(current_year, 7, 1)  # July 1st
        year_end = datetime(current_year, 12, 31, 23, 59, 59)  # December 31st
        
        ytd_closed_deals = df[
            (df['stage'] == 'A Closed') &
            (df['billing_start'] >= year_start) &
            (df['billing_start'] <= year_end) &
            (df['expected_arr'].notna()) &
            (df['expected_arr'] > 0)
        ]
        ytd_revenue = float(ytd_closed_deals['expected_arr'].fillna(0).sum())
        
        # Annual target 2025 - sum of July-December from back office or use objectif_6_mois
        if revenue_2025 and any(revenue_2025.values()):
            # Sum July to December targets from back office
            annual_target_2025 = float(
                safe_int(revenue_2025.get('jul', 0)) + safe_int(revenue_2025.get('aug', 0)) + 
                safe_int(revenue_2025.get('sep', 0)) + safe_int(revenue_2025.get('oct', 0)) + 
                safe_int(revenue_2025.get('nov', 0)) + safe_int(revenue_2025.get('dec', 0))
            )
        else:
            # Fallback to objectif_6_mois
            annual_target_2025 = float(objectif_6_mois)
        
        # Total pipeline
        active_pipeline = df[~df['stage'].isin(['Closed Won', 'Closed Lost', 'I Lost'])]
        total_pipeline = float(active_pipeline['pipeline'].sum())
        
        # Weighted pipeline using Excel formula
        active_pipeline_copy = active_pipeline.copy()
        active_pipeline_copy['weighted_value'] = active_pipeline_copy.apply(calculate_excel_weighted_value, axis=1)
        total_weighted_pipeline = float(active_pipeline_copy['weighted_value'].sum())
        
        # July to December 2025 targets chart using view-specific targets
        period_targets_2025 = []
        cumulative_target = 0  # Start from zero for H2 period
        cumulative_closed = 0
        
        for month in ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']:
            month_str = f'{month} 2025'
            month_target = monthly_targets_2025.get(month_str, 0)
            
            # Calculate actual closed revenue for this month
            month_date = datetime(2025, {'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}[month], 1)
            month_start, month_end = get_month_range(month_date, 0)
            
            month_closed_deals = df[
                (df['stage'] == 'A Closed') &
                (df['discovery_date'] >= month_start) &
                (df['discovery_date'] <= month_end)
            ]
            month_closed = float(month_closed_deals['expected_arr'].fillna(0).sum())
            
            cumulative_target += month_target
            cumulative_closed += month_closed
            
            period_targets_2025.append({
                'month': month,
                'monthly_target': month_target,
                'monthly_closed': month_closed,
                'cumulative_target': cumulative_target,
                'cumulative_closed': cumulative_closed,
                'gap': cumulative_target - cumulative_closed
            })
        
        # Calculate the 4 additional dashboard blocks (dynamic by selected period)
        
        # Determine the focus period (July-December for H2 view)
        if target_months and len(target_months) > 0:
            # Use the first month in our target_months as the focus
            focus_month = target_months[0]  # This will be July 2025 by default
        else:
            focus_month = datetime(2025, 10, 1)  # Fallback to October
        
        focus_month_num = focus_month.month
        focus_month_str = focus_month.strftime('%b %Y')
        
        # Define date range for focus month
        focus_month_start = focus_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if focus_month_num == 12:
            focus_month_end = focus_month.replace(year=focus_month.year + 1, month=1, day=1) - timedelta(seconds=1)
        else:
            focus_month_end = focus_month.replace(month=focus_month_num + 1, day=1) - timedelta(seconds=1)
        
        # Block 1: Meetings Generation (dynamic by selected month)
        # Get targets from view_targets or use defaults
        meeting_gen = view_targets.get("meeting_generation", {})
        target_inbound = meeting_gen.get("inbound", 22)
        target_outbound = meeting_gen.get("outbound", 17)
        target_referral = meeting_gen.get("referral", meeting_gen.get("referrals", 11))
        target_upsells = meeting_gen.get("upsells_cross", meeting_gen.get("upsells_x", 0))
        
        # Use configured total_target if available, otherwise calculate sum
        if "total_target" in meeting_gen and meeting_gen["total_target"] > 0:
            target_total = meeting_gen["total_target"]
        else:
            target_total = target_inbound + target_outbound + target_referral
        
        # Calculate actual values for the focus month
        focus_month_meetings = df[
            (df['discovery_date'] >= focus_month_start) & 
            (df['discovery_date'] <= focus_month_end)
        ]
        
        actual_inbound = len(focus_month_meetings[focus_month_meetings['type_of_source'] == 'Inbound'])
        actual_outbound = len(focus_month_meetings[focus_month_meetings['type_of_source'] == 'Outbound'])
        # Include all referral types: Referral, Internal referral, Client referral
        referral_types = ['Referral', 'Internal referral', 'Client referral']
        actual_referral = len(focus_month_meetings[focus_month_meetings['type_of_source'].isin(referral_types)])
        
        # Calculate total meetings and unassigned meetings
        actual_total = len(focus_month_meetings)  # Total meetings in the period
        sum_of_sources_monthly = actual_inbound + actual_outbound + actual_referral
        unassigned_monthly = max(0, actual_total - sum_of_sources_monthly)
        
        # Calculate Show and No Show numbers (case insensitive and flexible matching)
        show_meetings = focus_month_meetings[
            focus_month_meetings['show_noshow'].notna() & 
            focus_month_meetings['show_noshow'].str.strip().str.lower().str.contains('show', na=False) &
            ~focus_month_meetings['show_noshow'].str.strip().str.lower().str.contains('noshow|no show', na=False)
        ]
        no_show_meetings = focus_month_meetings[
            focus_month_meetings['show_noshow'].notna() & 
            focus_month_meetings['show_noshow'].str.strip().str.lower().str.contains('noshow|no show', na=False)
        ]
        actual_show = len(show_meetings)
        actual_no_show = len(no_show_meetings)
        
        # Block 2: Intro & POA (filtered for focus month) - use view-specific targets
        target_intro = view_targets.get("meeting_generation", {}).get("intro", 45)
        target_poa = view_targets.get("meeting_attended", {}).get("poa", 18)
        
        # Intro = "Show" (une intro c'est un "show") for the focus month
        intro_data = df[
            (df['discovery_date'] >= focus_month_start) & 
            (df['discovery_date'] <= focus_month_end) &
            (df['show_noshow'] == 'Show')
        ]
        actual_intro = len(intro_data)
        
        # POA = "D POA Booked", "C Proposal sent", "B Legals", closed ou lost for the focus month
        poa_data = df[
            (df['discovery_date'] >= focus_month_start) & 
            (df['discovery_date'] <= focus_month_end) &
            df['stage'].isin(['D POA Booked', 'C Proposal sent', 'B Legals', 'Closed Won', 'Won', 'Signed', 'Closed Lost', 'I Lost'])
        ]
        actual_poa = len(poa_data)
        
        # Upsells / Cross-sells (Type of deal = "Upsell", "Up-sell", etc.) for the focus month
        upsells_data = df[
            (df['discovery_date'] >= focus_month_start) & 
            (df['discovery_date'] <= focus_month_end) &
            df['type_of_deal'].apply(is_upsell)
        ]
        actual_upsells = len(upsells_data)
        # target_upsells removed - using dynamic targets from view config
        
        # Block 3: Pipe creation (for focus month) - use Excel formula from spreadsheet
        new_pipe_focus_month = df[
            (df['discovery_date'] >= focus_month_start) & 
            (df['discovery_date'] <= focus_month_end) &
            (df['pipeline'].notna()) & 
            (df['pipeline'] > 0)
        ].copy()
        new_pipe_created = float(new_pipe_focus_month['pipeline'].sum())
        
        # Weighted pipe created using Excel formula (stage × source × recency)
        new_pipe_focus_month['weighted_value'] = new_pipe_focus_month.apply(calculate_excel_weighted_value, axis=1)
        weighted_pipe_created = float(new_pipe_focus_month['weighted_value'].sum())
        
        # Block 4: Revenue objective vs closed (for focus month)
        focus_month_target = 0
        focus_month_closed = 0
        
        for month_data in months_data:
            if month_data['month'] == focus_month_str:
                focus_month_target = month_data['target_revenue']
                focus_month_closed = month_data['closed_revenue']
                break
        
        # Dashboard blocks data (dynamic based on focus month)
        dashboard_blocks = {
            'block_1_meetings': {
                'title': 'Meetings Generation',
                'period': focus_month_str,
                'total_actual': actual_total,
                'total_target': target_total,
                'inbound_actual': actual_inbound,
                'inbound_target': target_inbound,
                'outbound_actual': actual_outbound,
                'outbound_target': target_outbound,
                'referral_actual': actual_referral,
                'referral_target': target_referral,
                'unassigned_actual': unassigned_monthly,
                'unassigned_target': 0,  # No target for unassigned
                'show_actual': actual_show,
                'no_show_actual': actual_no_show,
                'upsells_actual': actual_upsells,
                'upsells_target': target_upsells
            },
            'block_2_intro_poa': {
                'title': 'Intro & POA',
                'period': focus_month_str,
                'intro_actual': actual_intro,
                'intro_target': target_intro,
                'poa_actual': actual_poa,
                'poa_target': target_poa,
                'upsells_actual': actual_upsells,
                'upsells_target': target_upsells
            },
            'block_3_pipe_creation': {
                'title': 'New Pipe Created',
                'monthly_target': view_targets.get("dashboard", {}).get("new_pipe_created", 2000000),  # Use view-specific monthly target
                'new_pipe_created': new_pipe_created,
                'weighted_pipe_created': weighted_pipe_created,
                'aggregate_weighted_pipe': weighted_pipe_created,  # Use weighted_pipe_created as aggregate for custom period
                'target_pipe_created': view_targets.get("dashboard", {}).get("new_pipe_created", 2000000),
                'target_weighted_pipe': view_targets.get("dashboard", {}).get("weighted_pipe", 800000),
                'target_label': f'${int(view_targets.get("dashboard", {}).get("new_pipe_created", 2000000) / 1000000)}M New Pipe Target/Month',
                'weighted_label': f'Weighted Pipe: ${int(weighted_pipe_created):,}',
                'period': focus_month_str
            },
            'block_4_revenue': {
                'title': 'Monthly Revenue Objective',
                'revenue_target': focus_month_target,
                'closed_revenue': focus_month_closed,
                'target_label': f'Target: ${int(focus_month_target):,}',
                'closed_label': f'Closed: ${int(focus_month_closed):,}',
                'progress': (focus_month_closed / focus_month_target * 100) if focus_month_target > 0 else 0,
                'period': focus_month_str
            }
        }

        # Calculate pipe created (July-December 2025)
        # Sum of colonne K (pipeline) for deals created from July to December
        current_year = datetime.now().year
        year_start = datetime(current_year, 7, 1)  # July 1st
        year_end = datetime(current_year, 12, 31, 23, 59, 59)  # December 31st
        ytd_pipe_created = df[
            (df['discovery_date'] >= year_start) &
            (df['discovery_date'] <= year_end) &
            (df['pipeline'].notna()) &
            (df['pipeline'] > 0)
        ].copy()
        total_pipe_created = float(ytd_pipe_created['pipeline'].sum())
        
        # Calculate weighted pipe created (YTD) using Excel formula (stage × source × recency)
        ytd_pipe_created['weighted_value'] = ytd_pipe_created.apply(calculate_excel_weighted_value, axis=1)
        total_weighted_pipe_created = float(ytd_pipe_created['weighted_value'].sum())
        
        # Calculate active deals count (not lost, not inbox, show and relevant)
        active_deals_count_data = df[
            ~df['stage'].isin(['I Lost', 'H Lost - can be revived', 'F Inbox']) &
            (df['show_noshow'] == 'Show') &
            (df['relevance'] == 'Relevant')
        ]
        active_deals_count = len(active_deals_count_data)

        result = {
            'monthly_revenue_chart': months_data,
            'annual_targets_2025': period_targets_2025,
            'dashboard_blocks': dashboard_blocks,
            'key_metrics': {
                'ytd_revenue': ytd_revenue,
                'ytd_target': annual_target_2025,
                'ytd_progress': (ytd_revenue / annual_target_2025 * 100) if annual_target_2025 > 0 else 0,
                'ytd_remaining': annual_target_2025 - ytd_revenue,
                'total_pipeline': total_pipeline,
                'weighted_pipeline': total_weighted_pipeline,
                'deals_count': active_deals_count,
                'new_pipe_created': total_pipe_created,  # Renamed from pipe_created
                'created_weighted_pipe': total_weighted_pipe_created,  # Added
                'avg_deal_size': float(active_pipeline['pipeline'].mean()) if len(active_pipeline) > 0 else 0,
                'annual_target_2025': cumulative_target,
                'ytd_closed_2025': cumulative_closed
            }
        }
        return convert_numpy_types(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating dashboard analytics: {str(e)}")

@api_router.get("/data/records")
async def get_sales_records(limit: int = 100):
    """Get sales records"""
    records = await db.sales_records.find().limit(limit).to_list(limit)
    return {"records": records, "count": len(records)}

@api_router.get("/data/status")
async def get_data_status(view_id: str = Query(None)):
    """Get current data status and last update info"""
    try:
        # Determine collection based on view_id
        if view_id:
            records = await get_sales_data_for_view(view_id)
            total_records = len(records)
        else:
            # Fallback to Organic
            total_records = await db.sales_records.count_documents({})
        
        # Get last update info from metadata
        query = {"type": "last_update"}
        if view_id:
            query["view_id"] = view_id
        
        last_update_info = await db.data_metadata.find_one(query)
        
        if not last_update_info:
            last_update_info = {
                "last_update": None,
                "source_type": None,
                "source_url": None,
                "records_count": total_records
            }
        
        return {
            "total_records": total_records,
            "last_update": last_update_info.get("last_update"),
            "source_type": last_update_info.get("source_type"),  # "csv" or "google_sheets"
            "source_url": last_update_info.get("source_url"),
            "last_records_count": last_update_info.get("records_count", 0),
            "has_data": total_records > 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting data status: {str(e)}")

@api_router.post("/admin/trigger-auto-refresh")
async def trigger_auto_refresh_manually(
    user: dict = Depends(require_super_admin)
):
    """
    Manually trigger auto-refresh for all views (super admin only)
    Useful for testing the scheduled auto-refresh functionality
    """
    try:
        await auto_refresh_all_views()
        return {
            "message": "Auto-refresh triggered successfully for all views",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering auto-refresh: {str(e)}")

@api_router.get("/admin/auto-refresh-logs")
async def get_auto_refresh_logs(
    limit: int = Query(10, description="Number of logs to retrieve"),
    user: dict = Depends(require_super_admin)
):
    """
    Get auto-refresh logs (super admin only)
    """
    try:
        logs = await db.auto_refresh_logs.find().sort("timestamp", -1).limit(limit).to_list(limit)
        
        # Clean _id field
        for log in logs:
            if '_id' in log:
                del log['_id']
        
        return {
            "logs": logs,
            "count": len(logs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching auto-refresh logs: {str(e)}")

@api_router.post("/data/refresh-google-sheet")
async def refresh_google_sheet(
    view_id: str = Query(None, description="View ID to refresh data for"),
    user: dict = Depends(get_current_user)
):
    """Refresh data from the last used Google Sheet for a specific view"""   
    try:
        # Build metadata query with view_id
        metadata_query = {"type": "last_update"}
        if view_id:
            metadata_query["view_id"] = view_id
        else:
            metadata_query["view_id"] = "organic"  # Default to Organic
        
        # Get last Google Sheet URL from metadata
        last_update_info = await db.data_metadata.find_one(metadata_query)
        
        if not last_update_info or last_update_info.get("source_type") != "google_sheets":
            raise HTTPException(status_code=400, detail=f"No Google Sheet source found for this view. Please upload via Google Sheets first.")
        
        sheet_url = last_update_info.get("source_url")
        sheet_name = last_update_info.get("sheet_name")
        collection_name = last_update_info.get("collection", "sales_records")
        
        if not sheet_url:
            raise HTTPException(status_code=400, detail="No Google Sheet URL found in metadata.")
        
        # Read fresh data from Google Sheet
        df = read_google_sheet(sheet_url, sheet_name)
        
        # Process the data (reuse the processing logic)
        records = []
        valid_records = 0
        
        # Clean column names
        df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('/', '_')
        
        # Debug: Print column names
        print(f"📊 Columns loaded from Google Sheet: {list(df.columns)}")
        
        # Debug: Check if poa_date column exists and has data
        if 'poa_date' in df.columns:
            non_null_count = df['poa_date'].notna().sum()
            print(f"✅ poa_date column found! Non-null values: {non_null_count}/{len(df)}")
            # Show first 5 non-null values
            sample_values = df[df['poa_date'].notna()]['poa_date'].head(5).tolist()
            print(f"📋 Sample poa_date values from sheet: {sample_values}")
        else:
            print(f"❌ poa_date column NOT found! Available columns: {list(df.columns)}")
        
        processed_count = 0
        for idx, row in df.iterrows():
            # Skip empty or summary rows
            if pd.isna(row.get('client')) or str(row.get('client')).strip() == '':
                continue
                
            try:
                # Debug poa_date for first 3 records
                if processed_count < 3:
                    raw_poa = row.get('poa_date')
                    cleaned_poa = clean_date(raw_poa)
                    print(f"🔍 Record {processed_count + 1} - Client: {row.get('client')}, Raw poa_date: {raw_poa}, Cleaned: {cleaned_poa}")
                
                record = SalesRecord(
                    month=str(row.get('month', '')) if not pd.isna(row.get('month')) else None,
                    discovery_date=clean_date(row.get('discovery_date')),
                    client=str(row.get('client', '')).strip(),
                    hubspot_link=str(row.get('hubspot_link', '')) if not pd.isna(row.get('hubspot_link')) else None,
                    stage=str(row.get('stage', '')) if not pd.isna(row.get('stage')) else None,
                    relevance=str(row.get('relevance', '')) if not pd.isna(row.get('relevance')) else None,
                    show_noshow=str(row.get('show_nowshow', '')) if not pd.isna(row.get('show_nowshow')) else None,
                    poa_date=clean_date(row.get('poa_date')),
                    expected_mrr=clean_monetary_value(row.get('expected_mrr')),
                    expected_arr=clean_monetary_value(row.get('expected_arr')),
                    pipeline=clean_monetary_value(row.get('pipeline')),
                    type_of_deal=str(row.get('type_of_deal', '')) if not pd.isna(row.get('type_of_deal')) else None,
                    bdr=str(row.get('bdr', '')) if not pd.isna(row.get('bdr')) else None,
                    type_of_source=str(row.get('type_of_source', '')) if not pd.isna(row.get('type_of_source')) else None,
                    product=str(row.get('product', '')) if not pd.isna(row.get('product')) else None,
                    owner=str(row.get('owner', '')) if not pd.isna(row.get('owner')) else None,
                    supporters=str(row.get('supporters', '')) if not pd.isna(row.get('supporters')) else None,
                    billing_start=clean_date(row.get('billing_start'))
                )
                records.append(record.dict())
                valid_records += 1
                
            except Exception as e:
                print(f"Error processing row: {str(e)}")
                continue
        
        # Replace existing data in correct collection
        if records:
            await db[collection_name].delete_many({})
            await db[collection_name].insert_many(records)
            
            # Update metadata for this specific view
            await db.data_metadata.update_one(
                {"type": "last_update", "view_id": view_id if view_id else "organic"},
                {
                    "$set": {
                        "last_update": datetime.now(timezone.utc),
                        "source_type": "google_sheets",
                        "source_url": sheet_url,
                        "sheet_name": sheet_name,
                        "records_count": valid_records,
                        "collection": collection_name
                    }
                },
                upsert=True
            )
        
        return {
            "message": f"Successfully refreshed {valid_records} sales records from Google Sheet for {collection_name}",
            "records_processed": len(df),
            "records_valid": valid_records,
            "last_update": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing Google Sheet: {str(e)}")

@api_router.delete("/data/clear")
async def clear_data():
    """Clear all sales data"""   
    result = await db.sales_records.delete_many({})
    await db.data_metadata.delete_many({})  # Also clear metadata
    return {"message": f"Deleted {result.deleted_count} records"}

@api_router.post("/upload-google-sheets", response_model=UploadResponse)
async def upload_google_sheets_data(
    request: GoogleSheetsRequest,
    view_id: str = Query(None, description="View ID to associate data with"),
    user: dict = Depends(get_current_user)
):
    """Upload and process sales data from Google Sheets"""
    try:
        # Determine which collection to use
        collection_name = "sales_records"  # Default to Organic
        
        if view_id:
            view = await db.views.find_one({"id": view_id})
            if not view:
                raise HTTPException(status_code=404, detail="View not found")
            
            view_name = view.get("name")
            # Master view cannot upload data (it aggregates from others)
            if view.get("is_master"):
                raise HTTPException(status_code=400, detail="Cannot upload data to Master view. Master aggregates data from other views.")
            
            collection_name = get_collection_for_view(view_name)
        
        # Read data from Google Sheets
        df = read_google_sheet(request.sheet_url, request.sheet_name)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Google Sheet is empty or could not be read")
        
        # Clean column names
        df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('/', '_')
        
        # Process and clean data (same logic as CSV upload)
        records = []
        valid_records = 0
        
        for _, row in df.iterrows():
            # Skip empty or summary rows
            if pd.isna(row.get('client')) or str(row.get('client')).strip() == '':
                continue
                
            try:
                record = SalesRecord(
                    month=str(row.get('month', '')) if not pd.isna(row.get('month')) else None,
                    discovery_date=clean_date(row.get('discovery_date')),
                    client=str(row.get('client', '')).strip(),
                    hubspot_link=str(row.get('hubspot_link', '')) if not pd.isna(row.get('hubspot_link')) else None,
                    stage=str(row.get('stage', '')) if not pd.isna(row.get('stage')) else None,
                    relevance=str(row.get('relevance', '')) if not pd.isna(row.get('relevance')) else None,
                    show_noshow=str(row.get('show_nowshow', '')) if not pd.isna(row.get('show_nowshow')) else None,
                    poa_date=clean_date(row.get('poa_date')),
                    expected_mrr=clean_monetary_value(row.get('expected_mrr')),
                    expected_arr=clean_monetary_value(row.get('expected_arr')),
                    pipeline=clean_monetary_value(row.get('pipeline')),
                    type_of_deal=str(row.get('type_of_deal', '')) if not pd.isna(row.get('type_of_deal')) else None,
                    bdr=str(row.get('bdr', '')) if not pd.isna(row.get('bdr')) else None,
                    type_of_source=str(row.get('type_of_source', '')) if not pd.isna(row.get('type_of_source')) else None,
                    product=str(row.get('product', '')) if not pd.isna(row.get('product')) else None,
                    owner=str(row.get('owner', '')) if not pd.isna(row.get('owner')) else None,
                    supporters=str(row.get('supporters', '')) if not pd.isna(row.get('supporters')) else None,
                    billing_start=clean_date(row.get('billing_start'))
                )
                records.append(record.dict())
                valid_records += 1
                
            except Exception as e:
                print(f"Error processing row: {str(e)}")
                continue
        
        # Store in MongoDB
        if records:
            # Clear existing data for this view's collection
            await db[collection_name].delete_many({})
            # Insert new data
            await db[collection_name].insert_many(records)
            
            # Save metadata for future refresh
            await db.data_metadata.update_one(
                {"type": "last_update", "view_id": view_id if view_id else "organic"},
                {
                    "$set": {
                        "last_update": datetime.now(timezone.utc),
                        "source_type": "google_sheets",
                        "source_url": request.sheet_url,
                        "sheet_name": request.sheet_name,
                        "records_count": valid_records,
                        "collection": collection_name
                    }
                },
                upsert=True
            )
        
        return UploadResponse(
            message=f"Successfully processed {len(records)} sales records from Google Sheets",
            records_processed=len(df),
            records_valid=valid_records
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing Google Sheets data: {str(e)}")

@api_router.get("/projections/hot-deals")
async def get_hot_deals_closing(view_id: str = Query(None)):
    """Get hot deals closing in next 2 weeks to 30 days (legals stage)"""
    try:
        # Get data from MongoDB based on view
        if view_id:
            records = await get_sales_data_for_view(view_id)
        else:
            # Fallback to default Organic collection
            records = await db.sales_records.find().to_list(10000)
            
        if not records:
            return []
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(records)
        
        # Convert date strings back to datetime
        date_columns = ['discovery_date', 'poa_date', 'billing_start', 'created_at']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        hot_deals = calculate_hot_deals_closing(df)
        return hot_deals
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting hot deals: {str(e)}")

@api_router.get("/projections/hot-leads")
async def get_hot_leads(view_id: str = Query(None)):
    """Get additional hot leads for next 3 months (Proposal sent + PoA booked)"""
    try:
        # Get data from MongoDB based on view
        if view_id:
            records = await get_sales_data_for_view(view_id)
        else:
            # Fallback to default Organic collection
            records = await db.sales_records.find().to_list(10000)
            
        if not records:
            return []
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(records)
        
        # Convert date strings back to datetime
        date_columns = ['discovery_date', 'poa_date', 'billing_start', 'created_at']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        hot_leads = calculate_hot_leads(df)
        return hot_leads
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting hot leads: {str(e)}")

@api_router.get("/projections/ae-pipeline-breakdown")
async def get_ae_pipeline_breakdown(view_id: str = Query(None)):
    """Get pipeline breakdown by AE for Next 14, 30, and 60-90 days periods"""
    try:
        # Get data from MongoDB based on view
        if view_id:
            records = await get_sales_data_for_view(view_id)
        else:
            # Fallback to default Organic collection
            records = await db.sales_records.find().to_list(10000)
            
        if not records:
            return []
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(records)
        
        # Convert date strings back to datetime
        date_columns = ['discovery_date', 'poa_date', 'billing_start', 'created_at']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Apply Excel weighting formula
        df['weighted_value'] = df.apply(calculate_excel_weighted_value, axis=1)
        
        # Get all hot deals and hot leads
        hot_deals = df[df['stage'] == 'B Legals'].copy()
        hot_leads = df[df['stage'].isin(['C Proposal sent', 'D POA Booked'])].copy()
        
        # Combine all deals
        all_deals = pd.concat([hot_deals, hot_leads], ignore_index=True)
        
        if all_deals.empty:
            return []
        
        # Assign deals to time periods based on stage
        # Next 14 Days: B Legals
        # Next 30 Days: Could be some other logic, but for now we'll use stage
        # Next 60-90 Days: C Proposal sent, D POA Booked
        
        def assign_period(row):
            stage = row['stage']
            if stage == 'B Legals':
                return 'next14'
            elif stage == 'C Proposal sent':
                return 'next60'
            elif stage == 'D POA Booked':
                return 'next30'
            return 'other'
        
        all_deals['period'] = all_deals.apply(assign_period, axis=1)
        
        # Get all unique AEs
        all_aes = sorted(df['owner'].dropna().unique())
        
        # Build breakdown by AE
        ae_breakdown = []
        
        for ae in all_aes:
            ae_data = {
                'ae': fix_ae_name_encoding(ae),
                'next14': {
                    'pipeline': 0.0,
                    'expected_arr': 0.0,
                    'weighted_value': 0.0
                },
                'next30': {
                    'pipeline': 0.0,
                    'expected_arr': 0.0,
                    'weighted_value': 0.0
                },
                'next60': {
                    'pipeline': 0.0,
                    'expected_arr': 0.0,
                    'weighted_value': 0.0
                },
                'total': {
                    'pipeline': 0.0,
                    'expected_arr': 0.0,
                    'weighted_value': 0.0
                }
            }
            
            # Calculate for each period
            for period in ['next14', 'next30', 'next60']:
                ae_period_deals = all_deals[(all_deals['owner'] == ae) & (all_deals['period'] == period)]
                
                if not ae_period_deals.empty:
                    ae_data[period]['pipeline'] = float(ae_period_deals['pipeline'].fillna(0).sum())
                    ae_data[period]['expected_arr'] = float(ae_period_deals['expected_arr'].fillna(0).sum())
                    ae_data[period]['weighted_value'] = float(ae_period_deals['weighted_value'].fillna(0).sum())
            
            # Calculate totals
            ae_data['total']['pipeline'] = ae_data['next14']['pipeline'] + ae_data['next30']['pipeline'] + ae_data['next60']['pipeline']
            ae_data['total']['expected_arr'] = ae_data['next14']['expected_arr'] + ae_data['next30']['expected_arr'] + ae_data['next60']['expected_arr']
            ae_data['total']['weighted_value'] = ae_data['next14']['weighted_value'] + ae_data['next30']['weighted_value'] + ae_data['next60']['weighted_value']
            
            ae_breakdown.append(ae_data)
        
        return ae_breakdown
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting AE pipeline breakdown: {str(e)}")

@api_router.get("/debug/test-google-sheet-import")
async def test_google_sheet_import():
    """Test what data is actually imported from Google Sheet"""
    try:
        # Get the current Google Sheet URL from metadata
        metadata = await db.data_metadata.find_one({"type": "last_update"})
        if not metadata or "source_url" not in metadata:
            return {"error": "No Google Sheet URL found in metadata"}
        
        # Read fresh data from Google Sheet
        df = read_google_sheet(metadata["source_url"], metadata.get("sheet_name"))
        
        # Clean column names
        df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('/', '_')
        
        # Get info about show_noshow column
        show_noshow_info = {
            "column_exists": "show_noshow" in df.columns,
            "total_rows": len(df),
            "non_null_count": len(df[df['show_noshow'].notna()]) if 'show_noshow' in df.columns else 0,
            "unique_values": df['show_noshow'].unique().tolist() if 'show_noshow' in df.columns else [],
            "sample_rows": df[['client', 'show_noshow']].head(10).to_dict('records') if 'show_noshow' in df.columns else [],
            "all_columns": df.columns.tolist()
        }
        
        return show_noshow_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing Google Sheet import: {str(e)}")

@api_router.get("/projections/performance-summary")
async def get_projections_performance_summary(view_id: str = Query(None)):
    """Get performance summary data for projections tab (same as dashboard)"""
    try:
        # Get data from MongoDB based on view
        if view_id:
            records = await get_sales_data_for_view(view_id)
        else:
            # Fallback to default Organic collection
            records = await db.sales_records.find().to_list(10000)
            
        if not records:
            raise HTTPException(status_code=404, detail="No sales data found")
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(records)
        
        # Convert date strings back to datetime
        date_columns = ['discovery_date', 'poa_date', 'billing_start', 'created_at']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Calculate YTD revenue and targets (same logic as dashboard)
        ytd_closed = df[df['stage'].isin(['Closed Won', 'Won', 'Signed', 'A Closed'])]
        ytd_revenue = float(ytd_closed['expected_arr'].fillna(0).sum())
        ytd_target = 4500000  # Same as dashboard
        
        # Calculate pipe created (YTD)
        current_year = datetime.now().year
        year_start = datetime(current_year, 1, 1)
        year_end = datetime(current_year, 12, 31, 23, 59, 59)
        ytd_pipe_created = df[
            (df['discovery_date'] >= year_start) &
            (df['discovery_date'] <= year_end)
        ]
        total_pipe_created = float(ytd_pipe_created['pipeline'].fillna(0).sum())
        
        # Calculate active deals count (not lost, not inbox, show and relevant)
        active_deals = df[
            ~df['stage'].isin(['I Lost', 'H Lost - can be revived', 'F Inbox']) &
            (df['show_noshow'] == 'Show') &
            (df['relevance'] == 'Relevant')
        ]
        active_deals_count = len(active_deals)
        
        # Calculate dashboard blocks data
        dashboard_blocks = {}
        
        # Get current month data for dashboard blocks
        today = datetime.now()
        current_month_str = today.strftime('%b %Y')
        
        # Filter data for current month
        current_month_data = df[df['discovery_date'].dt.to_period('M') == pd.Timestamp(today).to_period('M')]
        
        # Meeting Generation metrics
        actual_inbound = len(current_month_data[current_month_data['type_of_source'] == 'inbound'])
        actual_outbound = len(current_month_data[current_month_data['type_of_source'] == 'outbound'])
        actual_referral = len(current_month_data[current_month_data['type_of_source'] == 'referral'])
        
        dashboard_blocks['meetings'] = {
            'period': current_month_str,
            'inbound_actual': actual_inbound,
            'inbound_target': 20,
            'outbound_actual': actual_outbound,
            'outbound_target': 15,
            'referral_actual': actual_referral,
            'referral_target': 10
        }
        
        performance_summary = {
            'ytd_revenue': ytd_revenue,
            'ytd_target': ytd_target,
            'remaining_target': float(ytd_target - ytd_revenue),
            'pipe_created': total_pipe_created,
            'active_deals_count': active_deals_count,
            'forecast_gap': bool(ytd_revenue < ytd_target * 0.75),
            'dashboard_blocks': dashboard_blocks
        }
        
        return performance_summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting performance summary: {str(e)}")

@api_router.get("/analytics/comprehensive")
async def get_comprehensive_analytics(view_id: str = Query(None)):
    """Get comprehensive analytics data with all components"""
    try:
        # Get view config and targets if view_id provided
        view_config = None
        view_targets = None
        if view_id:
            config_data = await get_view_config_with_defaults(view_id)
            view_config = config_data["view"]
            view_targets = config_data["targets"]
            # Map admin targets to analytics format
            # Targets already mapped in get_view_config_with_defaults
        else:
            # Default targets for Organic view
            view_targets = {
                "dashboard": {
                    "objectif_6_mois": 4500000,
                    "deals": 25,
                    "new_pipe_created": 2000000,
                    "weighted_pipe": 800000
                },
                "meeting_generation": {
                    "intro": 45,
                    "inbound": 22,
                    "outbound": 17,
                    "referrals": 11
                },
                "meeting_attended": {
                    "poa": 18,
                    "deals_closed": 6
                }
            }

        # Get data from MongoDB based on view
        if view_id:
            records = await get_sales_data_for_view(view_id)
        else:
            # Fallback to default Organic collection
            records = await db.sales_records.find().to_list(10000)
            
        if not records:
            raise HTTPException(status_code=404, detail="No sales data found. Please upload data first.")

        # Convert to DataFrame for analysis
        df = pd.DataFrame(records)
        
        # Convert date strings back to datetime
        date_columns = ['discovery_date', 'poa_date', 'billing_start', 'created_at']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Use current month for analytics
        today = datetime.now()
        month_start, month_end = get_month_range(today, 0)

        # Generate all analytics components
        meeting_generation = calculate_meeting_generation(df, month_start, month_end, view_targets)
        meetings_attended = calculate_meetings_attended(df, month_start, month_end, view_targets)
        ae_performance = calculate_ae_performance(df, month_start, month_end)
        deals_closed = calculate_deals_closed(df, month_start, month_end, view_targets)
        pipe_metrics = calculate_pipe_metrics(df, month_start, month_end, view_targets)
        closing_projections = calculate_closing_projections(df)

        # Attribution analysis
        attribution = {
            'intro_attribution': {k: int(v) for k, v in df.groupby('type_of_source')['id'].count().to_dict().items()},
            'disco_attribution': {k: int(v) for k, v in df[~df['discovery_date'].isna()].groupby('type_of_source')['id'].count().to_dict().items()},
            'bdr_attribution': {k: int(v) for k, v in df.groupby('bdr')['id'].count().to_dict().items()}
        }

        # Dashboard blocks
        dashboard_blocks = {
            'current_month': today.strftime('%b %Y'),
            'total_meetings': len(df[(df['discovery_date'] >= month_start) & (df['discovery_date'] <= month_end)]),
            'total_deals': len(df[df['stage'] == 'A Closed'])
        }

        # Key metrics
        key_metrics = {
            'total_revenue': float(df[df['stage'] == 'A Closed']['expected_arr'].fillna(0).sum()),
            'total_pipeline': float(df['pipeline'].fillna(0).sum()),
            'active_deals': len(df[~df['stage'].isin(['I Lost', 'Closed Lost'])])
        }

        return convert_numpy_types({
            "dashboard_blocks": dashboard_blocks,
            "key_metrics": key_metrics,
            "meeting_generation": meeting_generation,
            "meetings_attended": meetings_attended,
            "ae_performance": ae_performance,
            "deals_closed": deals_closed,
            "deals_closed_current_period": deals_closed,  # Same data, different key for frontend
            "pipe_metrics": pipe_metrics,
            "attribution": attribution,
            "closing_projections": closing_projections
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating comprehensive analytics: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_scheduler():
    """Start the scheduler for auto-refresh tasks"""
    try:
        # Schedule auto-refresh at 12:00 and 20:00 Europe/Paris time
        scheduler.add_job(
            auto_refresh_all_views,
            CronTrigger(hour=12, minute=0, timezone='Europe/Paris'),
            id='auto_refresh_noon',
            name='Auto-refresh Google Sheets at 12:00',
            replace_existing=True
        )
        
        scheduler.add_job(
            auto_refresh_all_views,
            CronTrigger(hour=20, minute=0, timezone='Europe/Paris'),
            id='auto_refresh_evening',
            name='Auto-refresh Google Sheets at 20:00',
            replace_existing=True
        )
        
        scheduler.start()
        print("✅ Scheduler started - Auto-refresh scheduled at 12:00 and 20:00 Europe/Paris")
    except Exception as e:
        print(f"❌ Failed to start scheduler: {str(e)}")

@app.on_event("shutdown")
async def shutdown_scheduler_and_db():
    """Shutdown scheduler and database client"""
    try:
        scheduler.shutdown()
        print("✅ Scheduler stopped")
    except Exception as e:
        print(f"⚠️ Error stopping scheduler: {str(e)}")
    
    client.close()
    print("✅ Database client closed")
