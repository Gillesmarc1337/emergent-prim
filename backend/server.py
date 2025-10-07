from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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
    attribution: Dict[str, Any]
    deals_closed: Dict[str, Any]
    pipe_metrics: Dict[str, Any]
    old_pipe: Dict[str, Any]
    closing_projections: Dict[str, Any]
    big_numbers_recap: Dict[str, Any]

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

def calculate_meeting_generation(df, start_date, end_date):
    """Calculate meeting generation metrics for specified period"""
    period_data = df[
        (df['discovery_date'] >= start_date) & 
        (df['discovery_date'] <= end_date)
    ]
    
    # Split by source type
    inbound = period_data[period_data['type_of_source'] == 'Inbound']
    outbound = period_data[period_data['type_of_source'] == 'Outbound']
    referrals = period_data[period_data['type_of_source'].isin(['Internal referral', 'Client referral'])]
    
    # Relevance analysis
    relevant = period_data[period_data['relevance'] == 'Relevant']
    question_mark = period_data[period_data['relevance'].isin(['Question mark', 'Maybe'])]
    not_relevant = period_data[period_data['relevance'] == 'Not relevant']
    
    # BDR level detail
    bdr_stats = period_data.groupby('bdr').agg({
        'id': 'count',
        'relevance': lambda x: (x == 'Relevant').sum()
    }).rename(columns={'id': 'total_meetings', 'relevance': 'relevant_meetings'})
    
    # Convert numpy types to Python native types
    total_intros = int(len(period_data))
    target = 50
    
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
            'relevant_meetings': int(v['relevant_meetings'])
        } for k, v in bdr_stats.to_dict('index').items()} if not bdr_stats.empty else {},
        'target': target,
        'on_track': bool(total_intros >= target)
    }

def calculate_meetings_attended(df, week_start, week_end):
    """Calculate meetings attended metrics"""
    week_data = df[
        (df['discovery_date'] >= week_start) & 
        (df['discovery_date'] <= week_end)
    ]
    
    attended = week_data[week_data['show_noshow'] == 'Show']
    discoveries = week_data[~week_data['discovery_date'].isna()]
    poa_meetings = week_data[~week_data['poa_date'].isna()]
    
    # AE level performance
    ae_stats = week_data.groupby('owner').agg({
        'id': 'count',
        'show_noshow': lambda x: (x == 'Show').sum(),
        'poa_date': lambda x: x.notna().sum()
    }).rename(columns={
        'id': 'total_scheduled',
        'show_noshow': 'attended',
        'poa_date': 'poa_generated'
    })
    
    # Convert numpy types to Python native types
    attended_count = int(len(attended))
    scheduled_count = int(len(week_data))
    discoveries_count = int(len(discoveries))
    poa_count = int(len(poa_meetings))
    
    return {
        'intro_metrics': {
            'target': 40,
            'attended': attended_count,
            'scheduled': scheduled_count,
            'attendance_rate': float(attended_count / scheduled_count * 100 if scheduled_count > 0 else 0)
        },
        'discovery_metrics': {
            'target': 30,
            'completed': discoveries_count,
            'conversion_rate': float(discoveries_count / attended_count * 100 if attended_count > 0 else 0)
        },
        'poa_metrics': {
            'target': 15,
            'generated': poa_count,
            'conversion_rate': float(poa_count / discoveries_count * 100 if discoveries_count > 0 else 0)
        },
        'ae_performance': {k: {
            'total_scheduled': int(v['total_scheduled']),
            'attended': int(v['attended']),
            'poa_generated': int(v['poa_generated'])
        } for k, v in ae_stats.to_dict('index').items()} if not ae_stats.empty else {},
        'on_track': bool(attended_count >= 40 and poa_count >= 15)
    }

def calculate_deals_closed(df, week_start, week_end):
    """Calculate deals closed metrics"""
    closed_deals = df[
        (df['billing_start'] >= week_start) & 
        (df['billing_start'] <= week_end) &
        (df['stage'].isin(['Closed Won', 'Won', 'Signed']))
    ]
    
    # Convert numpy types to Python native types
    deals_count = int(len(closed_deals))
    arr_sum = float(closed_deals['expected_arr'].sum())
    mrr_sum = float(closed_deals['expected_mrr'].sum())
    avg_deal = float(closed_deals['expected_arr'].mean() if len(closed_deals) > 0 else 0)
    
    return {
        'deals_closed': deals_count,
        'target_deals': 5,
        'arr_closed': arr_sum,
        'target_arr': 300000,
        'mrr_closed': mrr_sum,
        'avg_deal_size': avg_deal,
        'on_track': bool(deals_count >= 5 and arr_sum >= 300000),
        'deals_detail': clean_records(closed_deals[['client', 'expected_arr', 'owner', 'type_of_deal']].to_dict('records'))
    }

def calculate_pipe_metrics(df, week_start, week_end):
    """Calculate pipeline metrics"""
    # New pipe created last 7 days
    new_pipe = df[
        (df['discovery_date'] >= week_start) & 
        (df['discovery_date'] <= week_end) &
        (df['relevance'] == 'Relevant')
    ]
    
    # Hot pipe deals
    hot_stages = ['C Proposal sent', 'D Negotiation', 'E Verbal commit']
    hot_pipe = df[df['stage'].isin(hot_stages)]
    
    # Total aggregate pipe
    active_pipe = df[~df['stage'].isin(['Closed Won', 'Closed Lost', 'I Lost'])]
    
    # Convert numpy types to Python native types
    new_pipe_value = float(new_pipe['pipeline'].sum())
    hot_pipe_value = float(hot_pipe['pipeline'].sum())
    active_pipe_value = float(active_pipe['pipeline'].sum())
    
    return {
        'new_pipe_created': {
            'value': new_pipe_value,
            'count': int(len(new_pipe)),
            'target': 500000,
            'on_track': bool(new_pipe_value >= 500000)
        },
        'hot_pipe': {
            'value': hot_pipe_value,
            'count': int(len(hot_pipe)),
            'target': 1000000,
            'deals': clean_records(hot_pipe[['client', 'pipeline', 'stage', 'owner']].to_dict('records'))
        },
        'total_aggregate_pipe': {
            'value': active_pipe_value,
            'count': int(len(active_pipe)),
            'target': 2000000,
            'on_track': bool(active_pipe_value >= 2000000)
        }
    }

def calculate_closing_projections(df):
    """Calculate closing projections"""
    today = datetime.now()
    next_7_days = today + timedelta(days=7)
    end_of_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    end_of_quarter = today.replace(month=((today.month - 1) // 3 + 1) * 3, day=31)
    
    # Probability mapping based on stage
    stage_probabilities = {
        'E Verbal commit': 90,
        'D Negotiation': 70,
        'C Proposal sent': 50,
        'B Discovery completed': 30,
        'A Discovery scheduled': 10
    }
    
    # Add probability column
    df['probability'] = df['stage'].map(stage_probabilities).fillna(0)
    df['weighted_value'] = df['pipeline'] * df['probability'] / 100
    
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
        'ae_projections': {k: {
            'weighted_value': float(v['weighted_value']),
            'pipeline': float(v['pipeline'])
        } for k, v in ae_projections.to_dict('index').items()} if not ae_projections.empty else {}
    }

# API Endpoints
@api_router.get("/")
async def root():
    return {"message": "Sales Analytics API", "version": "1.0.0"}

@api_router.post("/upload-data", response_model=UploadResponse)
async def upload_sales_data(file: UploadFile = File(...)):
    """Upload and process sales data CSV file"""
    try:
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
                    show_noshow=str(row.get('show_noshow', '')) if not pd.isna(row.get('show_noshow')) else None,
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
            # Clear existing data
            await db.sales_records.delete_many({})
            # Insert new data
            await db.sales_records.insert_many(records)
        
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

@api_router.get("/analytics/monthly")
async def get_monthly_analytics(month_offset: int = 0):
    """Generate monthly analytics report"""
    try:
        # Calculate month range
        month_start, month_end = get_month_range(month_offset=month_offset)
        
        # Get data from MongoDB
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
        
        # Generate all analytics sections
        meeting_generation = calculate_meeting_generation(df, week_start, week_end)
        meetings_attended = calculate_meetings_attended(df, week_start, week_end)
        deals_closed = calculate_deals_closed(df, week_start, week_end)
        pipe_metrics = calculate_pipe_metrics(df, week_start, week_end)
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
        ytd_target = 3600000  # Should be configurable
        big_numbers_recap = {
            'ytd_revenue': ytd_revenue,
            'ytd_target': ytd_target,
            'remaining_target': float(ytd_target - ytd_revenue),
            'monthly_breakdown': {str(k): float(v) for k, v in df.groupby(df['discovery_date'].dt.to_period('M'))['pipeline'].sum().to_dict().items()},
            'forecast_gap': bool(ytd_revenue < ytd_target * 0.75)
        }
        
        analytics = WeeklyAnalytics(
            week_start=week_start,
            week_end=week_end,
            meeting_generation=meeting_generation,
            meetings_attended=meetings_attended,
            attribution=attribution,
            deals_closed=deals_closed,
            pipe_metrics=pipe_metrics,
            old_pipe=old_pipe,
            closing_projections=closing_projections,
            big_numbers_recap=big_numbers_recap
        )
        
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating analytics: {str(e)}")

@api_router.get("/analytics/custom")
async def get_custom_analytics(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format")
):
    """Generate analytics report for custom date range"""
    try:
        # Parse dates
        try:
            custom_start = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
            custom_end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Get data from MongoDB
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
        meeting_generation = calculate_meeting_generation(df, custom_start, custom_end)
        meetings_attended = calculate_meetings_attended(df, custom_start, custom_end)
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
        ytd_target = 3600000  # Should be configurable
        big_numbers_recap = {
            'ytd_revenue': ytd_revenue,
            'ytd_target': ytd_target,
            'remaining_target': float(ytd_target - ytd_revenue),
            'monthly_breakdown': {str(k): float(v) for k, v in df.groupby(df['discovery_date'].dt.to_period('M'))['pipeline'].sum().to_dict().items()},
            'forecast_gap': bool(ytd_revenue < ytd_target * 0.75)
        }
        
        analytics = WeeklyAnalytics(
            week_start=custom_start,
            week_end=custom_end,
            meeting_generation=meeting_generation,
            meetings_attended=meetings_attended,
            attribution=attribution,
            deals_closed=deals_closed,
            pipe_metrics=pipe_metrics,
            old_pipe=old_pipe,
            closing_projections=closing_projections,
            big_numbers_recap=big_numbers_recap
        )
        
        return analytics
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating custom analytics: {str(e)}")

@api_router.get("/data/records")
async def get_sales_records(limit: int = 100):
    """Get sales records"""
    records = await db.sales_records.find().limit(limit).to_list(limit)
    return {"records": records, "count": len(records)}

@api_router.delete("/data/clear")
async def clear_data():
    """Clear all sales data"""
    result = await db.sales_records.delete_many({})
    return {"message": f"Deleted {result.deleted_count} records"}

@api_router.post("/upload-google-sheets", response_model=UploadResponse)
async def upload_google_sheets_data(request: GoogleSheetsRequest):
    """Upload and process sales data from Google Sheets"""
    try:
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
                    show_noshow=str(row.get('show_noshow', '')) if not pd.isna(row.get('show_noshow')) else None,
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
            # Clear existing data
            await db.sales_records.delete_many({})
            # Insert new data
            await db.sales_records.insert_many(records)
        
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
