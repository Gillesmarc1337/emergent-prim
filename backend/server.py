from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Query, Request, Response, Cookie, Depends
from fastapi.responses import JSONResponse
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

async def get_view_config_with_defaults(view_id: str):
    """
    Get view configuration with default targets if not set
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
    
    # Merge view targets with defaults
    view_targets = view.get("targets", {})
    if not view_targets:
        view_targets = default_targets
    
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
    # Referrals include: Internal referral, External referral, Client referral
    referrals = period_data[period_data['type_of_source'].isin(['Internal referral', 'External referral', 'Client referral'])]
    
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
    bdr_list = ['Xavier', 'Selma', 'Kenny', 'Marie']
    monthly_bdr_meeting_target = 6  # 6 meetings per month per BDR
    
    # Get targets from view_targets if provided, otherwise use defaults
    if view_targets:
        meeting_gen = view_targets.get("meeting_generation", {})
        monthly_inbound_target = meeting_gen.get("inbound", 22)
        monthly_outbound_target = meeting_gen.get("outbound", 17)
        monthly_referral_target = meeting_gen.get("referral", meeting_gen.get("referrals", 11))
        monthly_total_target = monthly_inbound_target + monthly_outbound_target + monthly_referral_target
    else:
        # Default targets
        monthly_inbound_target = 22
        monthly_outbound_target = 17 
        monthly_referral_target = 11
        monthly_total_target = 50
    
    # Dynamic targets based on period duration
    inbound_target = monthly_inbound_target * period_duration_months
    outbound_target = monthly_outbound_target * period_duration_months
    referral_target = monthly_referral_target * period_duration_months
    total_target = monthly_total_target * period_duration_months
    
    # Convert numpy types to Python native types
    total_intros = int(len(period_data))
    
    # Detailed meetings list for table display (matching meetings_attended format)
    meetings_list = []
    for _, row in period_data.iterrows():
        meetings_list.append({
            'date': row['discovery_date'].strftime('%b %d') if pd.notna(row['discovery_date']) else 'N/A',
            'client': str(row.get('client', 'N/A')),
            'bdr': str(row.get('bdr', 'N/A')),
            'source': str(row.get('type_of_source', 'N/A')),
            'relevance': str(row.get('relevance', 'N/A')),
            'owner': str(row.get('owner', 'N/A')),  # AE owner
            'stage': str(row.get('stage', 'N/A'))  # Deal stage
        })
    
    return {
        'total_new_intros': total_intros,
        'inbound': int(len(inbound)),
        'outbound': int(len(outbound)),
        'referrals': int(len(referrals)),
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
        'on_track': bool(total_intros >= total_target)
    }

def calculate_meetings_attended(df, start_date, end_date):
    """Calculate meetings attended metrics"""
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
    
    # Deals Closed = A Closed stage only (as per user requirement)
    deals_closed_stages = ['A Closed']
    deals_closed = period_data[period_data['stage'].isin(deals_closed_stages)]
    
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
    
    # Base monthly targets
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
        
        # Closing value calculation (sum of expected_arr for closed won deals)
        closed_won = ae_poas[ae_poas['stage'] == 'A Closed']
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

def calculate_deals_closed(df, start_date, end_date):
    """Calculate deals closed metrics"""
    # Improved logic to detect closed deals from your actual data structure
    # Look for deals that have Expected ARR/MRR values and are in advanced stages
    potential_closed_deals = df[
        (
            (df['expected_arr'].notna()) & 
            (df['expected_arr'] > 0)
        ) | (
            (df['expected_mrr'].notna()) & 
            (df['expected_mrr'] > 0)
        )
    ]
    
    # Filter by date range (use discovery_date if billing_start is not available)
    date_filtered = potential_closed_deals[
        (
            (potential_closed_deals['billing_start'] >= start_date) & 
            (potential_closed_deals['billing_start'] <= end_date)
        ) | (
            (potential_closed_deals['discovery_date'] >= start_date) & 
            (potential_closed_deals['discovery_date'] <= end_date) &
            (potential_closed_deals['stage'].isin(['B Legals', 'C Proposal sent', 'D POA Booked']))
        )
    ]
    
    # Consider deals with stage "A Closed" as closed deals
    closed_deals = date_filtered[
        date_filtered['stage'] == 'A Closed'
    ]
    
    # Monthly breakdown for chart
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
            'arr_closed': float(month_deals['expected_arr'].sum()),
            'mrr_closed': float(month_deals['expected_mrr'].sum())
        })
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    # Convert numpy types to Python native types
    deals_count = int(len(closed_deals))
    arr_sum = float(closed_deals['expected_arr'].sum())
    mrr_sum = float(closed_deals['expected_mrr'].sum())
    avg_deal = float(closed_deals['expected_arr'].mean() if len(closed_deals) > 0 else 0)
    
    # Calculate period length to adjust targets
    period_days = (end_date - start_date).days
    monthly_target_deals = 6  # 6 deals per month target
    
    # Monthly ARR target: 750K per month
    monthly_target_arr = 750000  # 750K per month base target
    
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
        'monthly_closed': monthly_closed
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

def calculate_pipe_metrics(df, start_date, end_date):
    """Calculate pipeline metrics with Excel-exact weighted pipe logic"""
    
    # Apply centralized Excel weighting formula to each row
    df['weighted_value'] = df.apply(calculate_excel_weighted_value, axis=1)
    
    # Calculate dynamic targets based on period duration
    period_duration_days = (end_date - start_date).days + 1
    period_duration_months = max(1, round(period_duration_days / 30))
    
    # Base monthly targets
    monthly_new_pipe_target = 2_000_000  # $2M per month
    monthly_weighted_pipe_target = 800_000  # $800K per month
    monthly_total_pipe_target = 5_000_000  # $5M (this is overall, not scaled by period)
    monthly_total_weighted_target = 1_500_000  # $1.5M (this is overall, not scaled by period)
    
    # Dynamic targets for created pipe (scales with period)
    created_pipe_target = monthly_new_pipe_target * period_duration_months
    created_weighted_target = monthly_weighted_pipe_target * period_duration_months
    
    # New pipe created in period (Excel logic: ALL deals created in period, including Closed/Lost/Not Relevant)
    new_pipe = df[
        (df['discovery_date'] >= start_date) & 
        (df['discovery_date'] <= end_date)
        # Note: Excel includes ALL stages for "Created" metrics
    ]
    
    # Total active pipeline (Excel logic: exclude A Closed, I Lost, H not relevant)
    active_pipe = df[~df['stage'].isin(['A Closed', 'I Lost', 'H not relevant'])]
    
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
        'pipe_details': clean_records(active_pipe[['client', 'pipeline', 'weighted_value', 'stage', 'owner']].to_dict('records'))
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
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to update targets")
    
    return {"message": "Targets updated successfully", "targets": targets}

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
        meetings_attended = calculate_meetings_attended(df, july_dec_start, july_dec_end)
        ae_performance = calculate_ae_performance(df, july_dec_start, july_dec_end)
        deals_closed = calculate_deals_closed(df, july_dec_start, july_dec_end)
        pipe_metrics = calculate_pipe_metrics(df, july_dec_start, july_dec_end)
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
        monthly_upsell_target = view_targets.get("meeting_attended", {}).get("deals_closed", 6)
        july_dec_upsell_target = monthly_upsell_target * months_in_july_dec_period
        
        # New pipe created for July-Dec period
        new_pipe_july_dec = july_dec_meetings['pipeline'].sum()
        
        # Calculate target pipe created from view config
        monthly_pipe_target = view_targets.get("dashboard", {}).get("new_pipe_created", 2000000)
        target_pipe_july_dec = monthly_pipe_target * months_in_july_dec_period
        
        # Calculate weighted pipe properly for July-Dec period
        stage_probabilities = {
            'E Verbal commit': 90, 'D Negotiation': 70, 'C Proposal sent': 50,
            'B Discovery completed': 30, 'A Discovery scheduled': 10,
            'D POA Booked': 30, 'B Legals': 70, 'A Closed': 100
        }
        
        july_dec_weighted_data = df[
            (df['discovery_date'] >= july_dec_start) & 
            (df['discovery_date'] <= july_dec_end)
        ].copy()
        
        july_dec_weighted_data['probability'] = july_dec_weighted_data['stage'].map(stage_probabilities).fillna(0)
        july_dec_weighted_data['weighted_value'] = july_dec_weighted_data['pipeline'] * july_dec_weighted_data['probability'] / 100.0
        weighted_pipe_july_dec = july_dec_weighted_data['weighted_value'].sum()
        
        # Calculate aggregate weighted pipe (all active deals, not just July-Dec created)
        # This includes all deals regardless of when they were created
        all_active_deals = df[
            ~df['stage'].isin(['I Lost', 'H Lost - can be revived', 'F Inbox', 'A Closed']) &
            (df['show_noshow'] == 'Show') &
            (df['relevance'] == 'Relevant')
        ].copy()
        
        all_active_deals['probability'] = all_active_deals['stage'].map(stage_probabilities).fillna(0)
        all_active_deals['weighted_value'] = all_active_deals['pipeline'] * all_active_deals['probability'] / 100.0
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
            'week_start': year_start,  # Use year_start for compatibility
            'week_end': year_end,      # Use year_end for compatibility
            'meeting_generation': meeting_generation,
            'meetings_attended': meetings_attended,
            'ae_performance': ae_performance,
            'attribution': attribution,
            'deals_closed': deals_closed,
            'pipe_metrics': pipe_metrics,
            'old_pipe': old_pipe,
            'closing_projections': closing_projections,
            'big_numbers_recap': big_numbers_recap,
            'dashboard_blocks': dashboard_blocks
        }
        
        return analytics
        
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
        meetings_attended = calculate_meetings_attended(df, month_start, month_end)
        ae_performance = calculate_ae_performance(df, month_start, month_end)
        deals_closed = calculate_deals_closed(df, month_start, month_end)
        pipe_metrics = calculate_pipe_metrics(df, month_start, month_end)
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
        target_upsells = 5  # 5 upsells per month
        
        # Block 3: Pipe creation
        new_pipe_focus_month = df[
            (df['discovery_date'] >= month_start) & 
            (df['discovery_date'] <= month_end) &
            (df['pipeline'].notna()) & 
            (df['pipeline'] > 0)
        ]
        new_pipe_created = float(new_pipe_focus_month['pipeline'].sum())
        
        stage_probabilities = {
            'D POA Booked': 70, 'C Proposal sent': 50, 'B Legals': 80,
            'E Verbal commit': 90, 'A Discovery scheduled': 20
        }
        new_pipe_focus_month['probability'] = new_pipe_focus_month['stage'].map(stage_probabilities).fillna(10)
        new_pipe_focus_month['weighted_value'] = new_pipe_focus_month['pipeline'] * new_pipe_focus_month['probability'] / 100
        weighted_pipe_created = float(new_pipe_focus_month['weighted_value'].sum())
        
        # Calculate aggregate weighted pipe (all active deals)
        all_active_deals_monthly = df[
            ~df['stage'].isin(['I Lost', 'H Lost - can be revived', 'F Inbox', 'A Closed']) &
            (df['show_noshow'] == 'Show') &
            (df['relevance'] == 'Relevant')
        ].copy()
        
        all_active_deals_monthly['probability'] = all_active_deals_monthly['stage'].map(stage_probabilities).fillna(10)
        all_active_deals_monthly['weighted_value'] = all_active_deals_monthly['pipeline'] * all_active_deals_monthly['probability'] / 100
        aggregate_weighted_pipe_monthly = float(all_active_deals_monthly['weighted_value'].sum())
        
        # Block 4: Revenue objective vs closed - calculate from view-specific 6-month target
        objectif_6_mois = view_targets.get("dashboard", {}).get("objectif_6_mois", 4500000)
        
        # Monthly distribution percentages for July-December
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
            'pipe_metrics': pipe_metrics,
            'old_pipe': old_pipe,
            'closing_projections': closing_projections,
            'big_numbers_recap': big_numbers_recap,
            'dashboard_blocks': dashboard_blocks
        }
        
        return analytics
        
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
        meetings_attended = calculate_meetings_attended(df, custom_start, custom_end)
        ae_performance = calculate_ae_performance(df, custom_start, custom_end)
        deals_closed = calculate_deals_closed(df, custom_start, custom_end)
        pipe_metrics = calculate_pipe_metrics(df, custom_start, custom_end)
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
            'poa_details': poa_attended_list
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
                'Jan 2025': int(revenue_2025.get('jan', 0)),
                'Feb 2025': int(revenue_2025.get('feb', 0)),
                'Mar 2025': int(revenue_2025.get('mar', 0)),
                'Apr 2025': int(revenue_2025.get('apr', 0)),
                'May 2025': int(revenue_2025.get('may', 0)),
                'Jun 2025': int(revenue_2025.get('jun', 0)),
                'Jul 2025': int(revenue_2025.get('jul', 0)),
                'Aug 2025': int(revenue_2025.get('aug', 0)),
                'Sep 2025': int(revenue_2025.get('sep', 0)),
                'Oct 2025': int(revenue_2025.get('oct', 0)),
                'Nov 2025': int(revenue_2025.get('nov', 0)),
                'Dec 2025': int(revenue_2025.get('dec', 0))
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
                'aggregate_weighted_pipe': aggregate_weighted_pipe,
                'is_future': target_date > datetime.now(),
                'deals_count': len(closed_deals)
            })
        
        # Calculate YTD metrics for 2025 (July-December period)
        # YTD closed revenue = sum of expected_arr for all deals with stage "A Closed" from July to December 2025
        current_year = datetime.now().year
        year_start = datetime(current_year, 7, 1)  # July 1st
        year_end = datetime(current_year, 12, 31, 23, 59, 59)  # December 31st
        
        ytd_closed_deals = df[
            (df['stage'] == 'A Closed') &
            (df['discovery_date'] >= year_start) &
            (df['discovery_date'] <= year_end)
        ]
        ytd_revenue = float(ytd_closed_deals['expected_arr'].fillna(0).sum())
        
        # Annual target 2025 from view config (July-December H2 target)
        annual_target_2025 = float(objectif_6_mois)  # Use view-specific 6-month target
        
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
        # Fixed targets as per user requirements: 20 inbound, 15 outbound, 10 referral per month
        target_inbound = 20
        target_outbound = 15
        target_referral = 10
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
        target_upsells = 5  # 5 upsells per month
        
        # Block 3: Pipe creation (for focus month)
        new_pipe_focus_month = df[
            (df['discovery_date'] >= focus_month_start) & 
            (df['discovery_date'] <= focus_month_end) &
            (df['pipeline'].notna()) & 
            (df['pipeline'] > 0)
        ]
        new_pipe_created = float(new_pipe_focus_month['pipeline'].sum())
        
        # Weighted pipe created (probability adjusted)
        stage_probabilities = {
            'D POA Booked': 70, 'C Proposal sent': 50, 'B Legals': 80,
            'E Verbal commit': 90, 'A Discovery scheduled': 20
        }
        new_pipe_focus_month['probability'] = new_pipe_focus_month['stage'].map(stage_probabilities).fillna(10)
        new_pipe_focus_month['weighted_value'] = new_pipe_focus_month['pipeline'] * new_pipe_focus_month['probability'] / 100
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

        # Calculate pipe created (YTD)
        current_year = datetime.now().year
        year_start = datetime(current_year, 1, 1)
        year_end = datetime(current_year, 12, 31, 23, 59, 59)
        ytd_pipe_created = df[
            (df['discovery_date'] >= year_start) &
            (df['discovery_date'] <= year_end)
        ]
        total_pipe_created = float(ytd_pipe_created['pipeline'].sum())
        
        # Calculate weighted pipe created (YTD)
        total_weighted_pipe_created = float(ytd_pipe_created['weighted_value'].sum()) if 'weighted_value' in ytd_pipe_created.columns else 0
        
        # Calculate active deals count (not lost, not inbox, show and relevant)
        active_deals_count_data = df[
            ~df['stage'].isin(['I Lost', 'H Lost - can be revived', 'F Inbox']) &
            (df['show_noshow'] == 'Show') &
            (df['relevance'] == 'Relevant')
        ]
        active_deals_count = len(active_deals_count_data)

        return {
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

@api_router.post("/data/refresh-google-sheet")
async def refresh_google_sheet():
    """Refresh data from the last used Google Sheet"""   
    try:
        # Get last Google Sheet URL from metadata
        last_update_info = await db.data_metadata.find_one({"type": "last_update"})
        
        if not last_update_info or last_update_info.get("source_type") != "google_sheets":
            raise HTTPException(status_code=400, detail="No Google Sheet source found. Please upload via Google Sheets first.")
        
        sheet_url = last_update_info.get("source_url")
        sheet_name = last_update_info.get("sheet_name")
        
        if not sheet_url:
            raise HTTPException(status_code=400, detail="No Google Sheet URL found in metadata.")
        
        # Read fresh data from Google Sheet
        df = read_google_sheet(sheet_url, sheet_name)
        
        # Process the data (reuse the processing logic)
        records = []
        valid_records = 0
        
        # Clean column names
        df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('/', '_')
        
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
        
        # Replace existing data
        if records:
            await db.sales_records.delete_many({})
            await db.sales_records.insert_many(records)
            
            # Update metadata
            await db.data_metadata.update_one(
                {"type": "last_update"},
                {
                    "$set": {
                        "last_update": datetime.utcnow(),
                        "source_type": "google_sheets",
                        "source_url": sheet_url,
                        "sheet_name": sheet_name,
                        "records_count": valid_records
                    }
                },
                upsert=True
            )
        
        return {
            "message": f"Successfully refreshed {valid_records} sales records from Google Sheet",
            "records_processed": len(df),
            "records_valid": valid_records,
            "last_update": datetime.utcnow().isoformat()
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
                        "last_update": datetime.utcnow(),
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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
