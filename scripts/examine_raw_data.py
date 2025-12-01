#!/usr/bin/env python3
"""
Examine raw MongoDB data to understand show_noshow column values
"""

import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / 'backend' / '.env')

async def examine_show_noshow_data():
    """Examine the raw data in MongoDB to understand show_noshow column"""
    print(f"\n{'='*80}")
    print(f"🔍 EXAMINING RAW MONGODB DATA FOR SHOW_NOSHOW COLUMN")
    print(f"{'='*80}")
    
    try:
        # Connect to MongoDB
        mongo_url = os.environ['MONGO_URL']
        db_name = os.environ['DB_NAME']
        
        print(f"Connecting to MongoDB: {mongo_url}")
        print(f"Database: {db_name}")
        
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Get all records
        records = await db.sales_records.find().to_list(10000)
        print(f"✅ Found {len(records)} total records")
        
        if not records:
            print(f"❌ No records found in database")
            return False
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(records)
        
        # Convert date columns
        date_columns = ['discovery_date', 'poa_date', 'billing_start', 'created_at']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        print(f"\n📊 SHOW_NOSHOW COLUMN ANALYSIS:")
        print(f"{'='*50}")
        
        # Check if show_noshow column exists
        if 'show_noshow' in df.columns:
            print(f"✅ show_noshow column exists")
            
            # Get unique values
            unique_values = df['show_noshow'].unique()
            print(f"\n🎯 UNIQUE VALUES in show_noshow column:")
            print(f"{'='*40}")
            for i, value in enumerate(unique_values, 1):
                count = len(df[df['show_noshow'] == value])
                print(f"{i}. '{value}' (type: {type(value).__name__}) - Count: {count}")
            
            # Check for null/empty values
            null_count = df['show_noshow'].isna().sum()
            empty_count = len(df[df['show_noshow'] == ''])
            print(f"\nNull values: {null_count}")
            print(f"Empty string values: {empty_count}")
            
            # Filter for July-December 2025 data
            july_dec_start = datetime(2025, 7, 1)
            july_dec_end = datetime(2025, 12, 31, 23, 59, 59)
            
            july_dec_data = df[
                (df['discovery_date'] >= july_dec_start) & 
                (df['discovery_date'] <= july_dec_end)
            ]
            
            print(f"\n📅 JULY-DECEMBER 2025 DATA ANALYSIS:")
            print(f"{'='*45}")
            print(f"Total meetings in July-Dec 2025: {len(july_dec_data)}")
            
            if len(july_dec_data) > 0:
                july_dec_show_noshow = july_dec_data['show_noshow'].unique()
                print(f"\nUnique show_noshow values in July-Dec 2025:")
                for i, value in enumerate(july_dec_show_noshow, 1):
                    count = len(july_dec_data[july_dec_data['show_noshow'] == value])
                    print(f"{i}. '{value}' (type: {type(value).__name__}) - Count: {count}")
                
                # Test different filtering approaches
                print(f"\n🔍 TESTING DIFFERENT FILTERING APPROACHES:")
                print(f"{'='*50}")
                
                # Test 1: Exact match 'No Show'
                no_show_exact = july_dec_data[july_dec_data['show_noshow'] == 'No Show']
                print(f"1. Exact match 'No Show': {len(no_show_exact)} records")
                
                # Test 2: Exact match 'NoShow'
                no_show_nospace = july_dec_data[july_dec_data['show_noshow'] == 'NoShow']
                print(f"2. Exact match 'NoShow': {len(no_show_nospace)} records")
                
                # Test 3: Case insensitive contains 'noshow'
                no_show_contains = july_dec_data[
                    july_dec_data['show_noshow'].str.lower().str.contains('noshow', na=False)
                ]
                print(f"3. Contains 'noshow' (case insensitive): {len(no_show_contains)} records")
                
                # Test 4: Case insensitive contains 'no show'
                no_show_contains_space = july_dec_data[
                    july_dec_data['show_noshow'].str.lower().str.contains('no show', na=False)
                ]
                print(f"4. Contains 'no show' (case insensitive): {len(no_show_contains_space)} records")
                
                # Test 5: Show exact match 'Show'
                show_exact = july_dec_data[july_dec_data['show_noshow'] == 'Show']
                print(f"5. Exact match 'Show': {len(show_exact)} records")
                
                # Show some sample records with their show_noshow values
                print(f"\n📋 SAMPLE RECORDS WITH SHOW_NOSHOW VALUES:")
                print(f"{'='*55}")
                sample_records = july_dec_data[['client', 'discovery_date', 'show_noshow']].head(10)
                for idx, row in sample_records.iterrows():
                    date_str = row['discovery_date'].strftime('%Y-%m-%d') if pd.notna(row['discovery_date']) else 'N/A'
                    print(f"Client: {row['client'][:30]:<30} | Date: {date_str} | Show/NoShow: '{row['show_noshow']}'")
                
            else:
                print(f"❌ No meetings found in July-December 2025 period")
        else:
            print(f"❌ show_noshow column does not exist!")
            print(f"Available columns: {list(df.columns)}")
        
        # Close connection
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Error examining data: {str(e)}")
        return False

async def main():
    """Main function"""
    print(f"🚀 Starting Raw Data Examination")
    print(f"Examination Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = await examine_show_noshow_data()
    
    print(f"\n{'='*80}")
    print(f"📋 EXAMINATION SUMMARY")
    print(f"{'='*80}")
    
    if success:
        print(f"✅ Raw data examination completed successfully")
        print(f"\n🎯 KEY INSIGHTS:")
        print(f"1. Check the unique values found in show_noshow column")
        print(f"2. Verify if 'No Show' format matches the filtering logic")
        print(f"3. Confirm if there are actually No Show records in July-Dec 2025")
        print(f"4. Update filtering logic if the format is different")
    else:
        print(f"❌ Raw data examination failed")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)