"""
Script to upload Google Sheets data for each view (Signal, Full Funnel, Market)
"""
import asyncio
import os
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import json

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'sales_analytics')]

# Google Sheets URLs
SHEETS_CONFIG = {
    "Signal": {
        "url": "https://docs.google.com/spreadsheets/d/1HJSHVRBKbwJ199VxJCioSOTz4gI9KrSniXKwAjcU3bI/edit?usp=drive_link",
        "collection": "sales_records_signal"
    },
    "Full Funnel": {
        "url": "https://docs.google.com/spreadsheets/d/12vOjTGZKoBNiodDMb-dFNH7r7aUOrPdFs5whMFjDKZo/edit?usp=drive_link",
        "collection": "sales_records_fullfunnel"
    },
    "Market": {
        "url": "https://docs.google.com/spreadsheets/d/1BJ_thepAfcZ7YQY1aWFoPbuBIakzd65hoMfbCJCDSlk/edit?usp=drive_link",
        "collection": "sales_records_market"
    }
}

def clean_date(date_val):
    """Clean date values"""
    if pd.isna(date_val) or str(date_val).strip() == '':
        return None
    try:
        return pd.to_datetime(date_val).isoformat()
    except:
        return None

def clean_monetary_value(val):
    """Clean monetary values"""
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    try:
        clean_val = str(val).replace('€', '').replace('$', '').replace(',', '').replace(' ', '').strip()
        return float(clean_val) if clean_val else 0.0
    except:
        return 0.0

async def upload_sheet_data(view_name, sheet_url, collection_name):
    """Upload data from Google Sheet to MongoDB collection"""
    print(f"\n📊 Processing {view_name} view...")
    print(f"   Sheet URL: {sheet_url}")
    print(f"   Collection: {collection_name}")
    
    try:
        # Setup Google Sheets credentials
        google_creds_json = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
        if not google_creds_json:
            print(f"   ❌ GOOGLE_SHEETS_CREDENTIALS not found in environment")
            return False
        
        # Parse credentials
        credentials_info = json.loads(google_creds_json)
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        creds = Credentials.from_service_account_info(credentials_info, scopes=scopes)
        gc = gspread.authorize(creds)
        
        # Extract sheet ID from URL
        sheet_id = sheet_url.split('/d/')[1].split('/')[0]
        
        # Open the sheet
        spreadsheet = gc.open_by_key(sheet_id)
        worksheet = spreadsheet.get_worksheet(0)  # First sheet
        
        # Get all records
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        print(f"   📋 Found {len(df)} rows in sheet")
        
        if len(df) == 0:
            print(f"   ⚠️  No data found in sheet")
            return False
        
        # Clean column names
        df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('/', '_')
        
        # Process records
        records = []
        for _, row in df.iterrows():
            # Skip empty rows
            if pd.isna(row.get('client')) or str(row.get('client')).strip() == '':
                continue
            
            try:
                record = {
                    'id': f"{view_name.lower().replace(' ', '_')}_{len(records)}_{int(datetime.now(timezone.utc).timestamp())}",
                    'month': str(row.get('month', '')) if not pd.isna(row.get('month')) else None,
                    'discovery_date': clean_date(row.get('discovery_date')),
                    'client': str(row.get('client', '')).strip(),
                    'hubspot_link': str(row.get('hubspot_link', '')) if not pd.isna(row.get('hubspot_link')) else None,
                    'stage': str(row.get('stage', '')) if not pd.isna(row.get('stage')) else None,
                    'relevance': str(row.get('relevance', '')) if not pd.isna(row.get('relevance')) else None,
                    'show_noshow': str(row.get('show_noshow', '')) if not pd.isna(row.get('show_noshow')) else None,
                    'poa_date': clean_date(row.get('poa_date')),
                    'expected_mrr': clean_monetary_value(row.get('expected_mrr')),
                    'expected_arr': clean_monetary_value(row.get('expected_arr')),
                    'pipeline': clean_monetary_value(row.get('pipeline')),
                    'type_of_deal': str(row.get('type_of_deal', '')) if not pd.isna(row.get('type_of_deal')) else None,
                    'bdr': str(row.get('bdr', '')) if not pd.isna(row.get('bdr')) else None,
                    'type_of_source': str(row.get('type_of_source', '')) if not pd.isna(row.get('type_of_source')) else None,
                    'product': str(row.get('product', '')) if not pd.isna(row.get('product')) else None,
                    'owner': str(row.get('owner', '')) if not pd.isna(row.get('owner')) else None,
                    'supporters': str(row.get('supporters', '')) if not pd.isna(row.get('supporters')) else None,
                    'billing_start': clean_date(row.get('billing_start')),
                    'created_at': datetime.now(timezone.utc)
                }
                records.append(record)
            except Exception as e:
                print(f"   ⚠️  Error processing row: {str(e)}")
                continue
        
        print(f"   ✅ Processed {len(records)} valid records")
        
        # Store in MongoDB
        if records:
            # Clear existing data
            await db[collection_name].delete_many({})
            # Insert new data
            await db[collection_name].insert_many(records)
            print(f"   ✅ Uploaded {len(records)} records to {collection_name}")
            return True
        else:
            print(f"   ⚠️  No valid records to upload")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

async def main():
    """Main function to upload all view data"""
    print("🚀 Starting Google Sheets data upload for all views...\n")
    
    success_count = 0
    total_count = len(SHEETS_CONFIG)
    
    for view_name, config in SHEETS_CONFIG.items():
        result = await upload_sheet_data(view_name, config["url"], config["collection"])
        if result:
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"📊 Upload Complete: {success_count}/{total_count} views uploaded successfully")
    print(f"{'='*60}")
    
    if success_count == total_count:
        print("✅ All views data uploaded successfully!")
    else:
        print(f"⚠️  {total_count - success_count} view(s) failed to upload")

if __name__ == "__main__":
    asyncio.run(main())
