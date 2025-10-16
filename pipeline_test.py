#!/usr/bin/env python3
"""
Pipeline Data Structure Testing for Sales Analytics Dashboard
Comprehensive inspection of pipeline data structure for Deals & Pipeline tab implementation
"""

import requests
import json
import sys
from datetime import datetime

# Use the production URL from frontend/.env
BASE_URL = "https://revdash-2.preview.emergentagent.com/api"

def test_api_endpoint(endpoint, expected_status=200):
    """Test an API endpoint and return response"""
    try:
        print(f"\n🔍 Testing: {endpoint}")
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != expected_status:
            print(f"❌ Expected status {expected_status}, got {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Response received successfully")
                return data
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response")
                print(f"Response text: {response.text}")
                return None
        else:
            return response.text
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {str(e)}")
        return None

def test_pipeline_data_structure_inspection():
    """
    Comprehensive inspection of pipeline data structure for Deals & Pipeline tab implementation
    Focus on pipeline metrics, stage-based data, POA metrics, and weighted pipeline calculations
    """
    print(f"\n{'='*80}")
    print(f"🔍 PIPELINE DATA STRUCTURE INSPECTION FOR DEALS & PIPELINE TAB")
    print(f"{'='*80}")
    
    pipeline_data_findings = {
        'monthly_pipeline_data': {},
        'yearly_pipeline_data': {},
        'deals_by_stage': {},
        'poa_metrics': {},
        'weighted_pipeline': {},
        'ae_breakdown': {}
    }
    
    # Test 1: GET /api/analytics/monthly - Pipeline Data Structure
    print(f"\n📊 Test 1: GET /api/analytics/monthly - Pipeline Data Inspection")
    print(f"{'='*60}")
    
    monthly_data = test_api_endpoint("/analytics/monthly")
    if monthly_data:
        print(f"✅ Monthly analytics data retrieved successfully")
        
        # Inspect pipeline-related sections
        pipeline_sections = ['pipe_metrics', 'deals_closed', 'closing_projections', 'dashboard_blocks', 'big_numbers_recap']
        
        for section in pipeline_sections:
            if section in monthly_data:
                print(f"\n🔍 Inspecting {section} section:")
                section_data = monthly_data[section]
                
                if section == 'pipe_metrics':
                    pipeline_data_findings['monthly_pipeline_data']['pipe_metrics'] = section_data
                    print(f"  📋 Pipe Metrics Structure:")
                    if isinstance(section_data, dict):
                        for key, value in section_data.items():
                            print(f"    • {key}: {type(value)} - {value if not isinstance(value, (dict, list)) else f'{len(value)} items'}")
                            
                            # Deep dive into created_pipe and total_pipe
                            if key in ['created_pipe', 'total_pipe'] and isinstance(value, dict):
                                print(f"      📊 {key} details:")
                                for sub_key, sub_value in value.items():
                                    print(f"        - {sub_key}: {sub_value}")
                
                elif section == 'deals_closed':
                    pipeline_data_findings['monthly_pipeline_data']['deals_closed'] = section_data
                    print(f"  📋 Deals Closed Structure:")
                    if isinstance(section_data, dict):
                        for key, value in section_data.items():
                            print(f"    • {key}: {value} ({type(value).__name__})")
                
                elif section == 'dashboard_blocks':
                    pipeline_data_findings['monthly_pipeline_data']['dashboard_blocks'] = section_data
                    print(f"  📋 Dashboard Blocks - Pipeline Related:")
                    if isinstance(section_data, dict):
                        for block_name, block_data in section_data.items():
                            if 'pipe' in block_name.lower() or 'deal' in block_name.lower():
                                print(f"    🎯 {block_name}:")
                                if isinstance(block_data, dict):
                                    for key, value in block_data.items():
                                        print(f"      - {key}: {value}")
                
                elif section == 'closing_projections':
                    pipeline_data_findings['monthly_pipeline_data']['closing_projections'] = section_data
                    print(f"  📋 Closing Projections Structure:")
                    if isinstance(section_data, dict):
                        for key, value in section_data.items():
                            print(f"    • {key}: {type(value)} - {len(value) if isinstance(value, (dict, list)) else value}")
                            
                            # Look for deals by timeframe
                            if isinstance(value, dict) and 'deals' in value:
                                deals = value['deals']
                                if isinstance(deals, list) and len(deals) > 0:
                                    print(f"      📊 Sample deal structure:")
                                    sample_deal = deals[0]
                                    for deal_key, deal_value in sample_deal.items():
                                        print(f"        - {deal_key}: {deal_value}")
        
        # Look for stage-based data
        print(f"\n🔍 Searching for stage-based deal data:")
        stage_data_found = search_for_stage_data(monthly_data)
        pipeline_data_findings['deals_by_stage']['monthly'] = stage_data_found
        for finding in stage_data_found[:5]:  # Show first 5 findings
            print(f"  • {finding}")
        
        # Look for POA-related metrics
        print(f"\n🔍 Searching for POA-related metrics:")
        poa_data_found = search_for_poa_data(monthly_data)
        pipeline_data_findings['poa_metrics']['monthly'] = poa_data_found
        for finding in poa_data_found[:5]:  # Show first 5 findings
            print(f"  • {finding}")
        
        # Look for weighted pipeline calculations
        print(f"\n🔍 Searching for weighted pipeline data:")
        weighted_data_found = search_for_weighted_pipeline_data(monthly_data)
        pipeline_data_findings['weighted_pipeline']['monthly'] = weighted_data_found
        for finding in weighted_data_found[:5]:  # Show first 5 findings
            print(f"  • {finding}")
        
    else:
        print(f"❌ Failed to retrieve monthly analytics data")
    
    # Test 2: GET /api/analytics/yearly - Pipeline Data Structure
    print(f"\n📊 Test 2: GET /api/analytics/yearly - Pipeline Data Inspection")
    print(f"{'='*60}")
    
    yearly_data = test_api_endpoint("/analytics/yearly?year=2025")
    if yearly_data:
        print(f"✅ Yearly analytics data retrieved successfully")
        
        # Similar inspection for yearly data
        for section in pipeline_sections:
            if section in yearly_data:
                section_data = yearly_data[section]
                pipeline_data_findings['yearly_pipeline_data'][section] = section_data
        
        # Look for stage-based data in yearly
        stage_data_found = search_for_stage_data(yearly_data)
        pipeline_data_findings['deals_by_stage']['yearly'] = stage_data_found
        
        # Look for POA-related metrics in yearly
        poa_data_found = search_for_poa_data(yearly_data)
        pipeline_data_findings['poa_metrics']['yearly'] = poa_data_found
        
        # Look for weighted pipeline calculations in yearly
        weighted_data_found = search_for_weighted_pipeline_data(yearly_data)
        pipeline_data_findings['weighted_pipeline']['yearly'] = weighted_data_found
        
    else:
        print(f"❌ Failed to retrieve yearly analytics data")
    
    # Test 3: Look for AE breakdown with pipeline data
    print(f"\n📊 Test 3: AE Breakdown with Pipeline Data")
    print(f"{'='*60}")
    
    ae_pipeline_data = search_for_ae_pipeline_breakdown(monthly_data, yearly_data)
    pipeline_data_findings['ae_breakdown'] = ae_pipeline_data
    for finding in ae_pipeline_data[:5]:  # Show first 5 findings
        print(f"  • {finding}")
    
    # Test 4: Specific stage analysis - "Proposal sent" and "Legals"
    print(f"\n📊 Test 4: Specific Stage Analysis - Proposal Sent & Legals")
    print(f"{'='*60}")
    
    proposal_legals_data = analyze_proposal_and_legals_stages(monthly_data, yearly_data)
    pipeline_data_findings['proposal_legals_analysis'] = proposal_legals_data
    
    print(f"📋 Proposal Sent Deals Found:")
    for finding in proposal_legals_data['proposal_sent_deals'][:3]:
        print(f"  • {finding}")
    
    print(f"📋 Legals Deals Found:")
    for finding in proposal_legals_data['legals_deals'][:3]:
        print(f"  • {finding}")
    
    # Summary Report
    print(f"\n{'='*80}")
    print(f"📋 PIPELINE DATA STRUCTURE SUMMARY REPORT")
    print(f"{'='*80}")
    
    print(f"\n🎯 KEY FINDINGS FOR DEALS & PIPELINE TAB IMPLEMENTATION:")
    
    # 1. Deals by Stage Data
    print(f"\n1️⃣ DEALS BY STAGE DATA:")
    if pipeline_data_findings['deals_by_stage']:
        for period, stage_data in pipeline_data_findings['deals_by_stage'].items():
            if stage_data:
                print(f"  ✅ {period.upper()}: Stage-based data available ({len(stage_data)} findings)")
                for stage_info in stage_data[:3]:  # Show first 3 findings
                    print(f"    • {stage_info}")
            else:
                print(f"  ❌ {period.upper()}: No stage-based data found")
    else:
        print(f"  ❌ No stage-based data structure identified")
    
    # 2. POA Metrics
    print(f"\n2️⃣ POA BOOKED METRICS:")
    if pipeline_data_findings['poa_metrics']:
        for period, poa_data in pipeline_data_findings['poa_metrics'].items():
            if poa_data:
                print(f"  ✅ {period.upper()}: POA metrics available ({len(poa_data)} findings)")
                for poa_info in poa_data[:3]:  # Show first 3 findings
                    print(f"    • {poa_info}")
            else:
                print(f"  ❌ {period.upper()}: No POA metrics found")
    else:
        print(f"  ❌ No POA metrics structure identified")
    
    # 3. Weighted Pipeline
    print(f"\n3️⃣ WEIGHTED PIPELINE CALCULATIONS:")
    if pipeline_data_findings['weighted_pipeline']:
        for period, weighted_data in pipeline_data_findings['weighted_pipeline'].items():
            if weighted_data:
                print(f"  ✅ {period.upper()}: Weighted pipeline data available ({len(weighted_data)} findings)")
                for weighted_info in weighted_data[:3]:  # Show first 3 findings
                    print(f"    • {weighted_info}")
            else:
                print(f"  ❌ {period.upper()}: No weighted pipeline data found")
    else:
        print(f"  ❌ No weighted pipeline structure identified")
    
    # 4. AE Breakdown
    print(f"\n4️⃣ AE BREAKDOWN WITH PIPELINE DATA:")
    if pipeline_data_findings['ae_breakdown']:
        print(f"  ✅ AE breakdown data available ({len(pipeline_data_findings['ae_breakdown'])} findings):")
        for ae_info in pipeline_data_findings['ae_breakdown'][:5]:  # Show first 5 findings
            print(f"    • {ae_info}")
    else:
        print(f"  ❌ No AE breakdown with pipeline data found")
    
    # 5. Specific Data Structure Details
    print(f"\n5️⃣ EXACT DATA STRUCTURE AND FIELD NAMES:")
    
    # Extract specific field names and values for user requirements
    print(f"\n📊 DEALS IN 'PROPOSAL SENT' STAGE:")
    proposal_sent_fields = extract_proposal_sent_data(monthly_data, yearly_data)
    for field_info in proposal_sent_fields:
        print(f"  • {field_info}")
    
    print(f"\n📊 DEALS IN 'LEGALS' STAGE:")
    legals_fields = extract_legals_data(monthly_data, yearly_data)
    for field_info in legals_fields:
        print(f"  • {field_info}")
    
    print(f"\n📊 POA BOOKED METRICS:")
    poa_fields = extract_poa_booked_data(monthly_data, yearly_data)
    for field_info in poa_fields:
        print(f"  • {field_info}")
    
    print(f"\n📊 AGGREGATE WEIGHTED PIPELINE:")
    weighted_fields = extract_weighted_pipeline_data(monthly_data, yearly_data)
    for field_info in weighted_fields:
        print(f"  • {field_info}")
    
    print(f"\n📊 CURRENT MONTH PIPELINE CREATION:")
    current_pipeline_fields = extract_current_pipeline_data(monthly_data)
    for field_info in current_pipeline_fields:
        print(f"  • {field_info}")
    
    print(f"\n📊 PER-AE PIPELINE BREAKDOWN:")
    ae_pipeline_fields = extract_ae_pipeline_data(monthly_data, yearly_data)
    for field_info in ae_pipeline_fields:
        print(f"  • {field_info}")
    
    # 6. Recommendations
    print(f"\n6️⃣ RECOMMENDATIONS FOR DEALS & PIPELINE TAB:")
    
    # Check if we have the required data for the user's requirements
    has_proposal_sent = any('proposal sent' in str(finding).lower() for findings in pipeline_data_findings['deals_by_stage'].values() for finding in findings)
    has_legals = any('legals' in str(finding).lower() for findings in pipeline_data_findings['deals_by_stage'].values() for finding in findings)
    has_poa_booked = any('poa' in str(finding).lower() for findings in pipeline_data_findings['poa_metrics'].values() for finding in findings)
    has_weighted_pipe = any('weighted' in str(finding).lower() for findings in pipeline_data_findings['weighted_pipeline'].values() for finding in findings)
    
    if has_proposal_sent:
        print(f"  ✅ 'Proposal sent' stage data: Available for pipeline metrics")
    else:
        print(f"  ⚠️  'Proposal sent' stage data: May need custom filtering")
    
    if has_legals:
        print(f"  ✅ 'Legals' stage data: Available for pipeline metrics")
    else:
        print(f"  ⚠️  'Legals' stage data: May need custom filtering")
    
    if has_poa_booked:
        print(f"  ✅ POA booked metrics: Available")
    else:
        print(f"  ⚠️  POA booked metrics: May need custom calculation")
    
    if has_weighted_pipe:
        print(f"  ✅ Weighted pipeline: Available")
    else:
        print(f"  ⚠️  Weighted pipeline: May need custom calculation")
    
    return len([f for f in [has_proposal_sent, has_legals, has_poa_booked, has_weighted_pipe] if f]) >= 3

def search_for_stage_data(data, path=""):
    """Search for stage-based deal data in the response"""
    stage_findings = []
    
    def recursive_search(obj, current_path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{current_path}.{key}" if current_path else key
                
                # Look for stage-related keys
                if 'stage' in key.lower():
                    stage_findings.append(f"Stage field found: {new_path} = {value}")
                
                # Look for specific stages
                if isinstance(value, str) and any(stage in value.lower() for stage in ['proposal sent', 'legals', 'poa booked']):
                    stage_findings.append(f"Target stage found: {new_path} = {value}")
                
                # Recursive search
                if isinstance(value, (dict, list)):
                    recursive_search(value, new_path)
                    
        elif isinstance(obj, list):
            for i, item in enumerate(obj[:5]):  # Check first 5 items
                recursive_search(item, f"{current_path}[{i}]")
    
    recursive_search(data)
    return stage_findings

def search_for_poa_data(data):
    """Search for POA-related metrics in the response"""
    poa_findings = []
    
    def recursive_search(obj, current_path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{current_path}.{key}" if current_path else key
                
                # Look for POA-related keys
                if 'poa' in key.lower():
                    poa_findings.append(f"POA field found: {new_path} = {value}")
                
                # Look for POA in values
                if isinstance(value, str) and 'poa' in value.lower():
                    poa_findings.append(f"POA reference found: {new_path} = {value}")
                
                # Recursive search
                if isinstance(value, (dict, list)):
                    recursive_search(value, new_path)
                    
        elif isinstance(obj, list):
            for i, item in enumerate(obj[:5]):  # Check first 5 items
                recursive_search(item, f"{current_path}[{i}]")
    
    recursive_search(data)
    return poa_findings

def search_for_weighted_pipeline_data(data):
    """Search for weighted pipeline calculations in the response"""
    weighted_findings = []
    
    def recursive_search(obj, current_path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{current_path}.{key}" if current_path else key
                
                # Look for weighted-related keys
                if 'weighted' in key.lower():
                    weighted_findings.append(f"Weighted field found: {new_path} = {value}")
                
                # Look for probability or percentage fields (often used in weighted calculations)
                if 'probability' in key.lower() or 'percent' in key.lower():
                    weighted_findings.append(f"Probability field found: {new_path} = {value}")
                
                # Look for aggregate pipeline
                if 'aggregate' in key.lower() and 'pipe' in key.lower():
                    weighted_findings.append(f"Aggregate pipeline found: {new_path} = {value}")
                
                # Recursive search
                if isinstance(value, (dict, list)):
                    recursive_search(value, new_path)
                    
        elif isinstance(obj, list):
            for i, item in enumerate(obj[:5]):  # Check first 5 items
                recursive_search(item, f"{current_path}[{i}]")
    
    recursive_search(data)
    return weighted_findings

def search_for_ae_pipeline_breakdown(monthly_data, yearly_data):
    """Search for AE breakdown with pipeline data"""
    ae_findings = []
    
    datasets = [("monthly", monthly_data), ("yearly", yearly_data)]
    
    for period_name, data in datasets:
        if not data:
            continue
            
        # Look for AE performance sections
        if 'ae_performance' in data:
            ae_perf = data['ae_performance']
            ae_findings.append(f"{period_name}: ae_performance section found with {len(ae_perf) if isinstance(ae_perf, dict) else 'unknown'} entries")
            
            # Check structure
            if isinstance(ae_perf, dict):
                for key, value in list(ae_perf.items())[:3]:  # Check first 3
                    ae_findings.append(f"{period_name}: ae_performance.{key} = {value}")
        
        # Look for pipe_metrics with AE breakdown
        if 'pipe_metrics' in data:
            pipe_metrics = data['pipe_metrics']
            if isinstance(pipe_metrics, dict) and 'ae_breakdown' in pipe_metrics:
                ae_breakdown = pipe_metrics['ae_breakdown']
                ae_findings.append(f"{period_name}: pipe_metrics.ae_breakdown found with {len(ae_breakdown) if isinstance(ae_breakdown, list) else 'unknown'} AEs")
                
                # Check structure of AE breakdown
                if isinstance(ae_breakdown, list) and len(ae_breakdown) > 0:
                    sample_ae = ae_breakdown[0]
                    if isinstance(sample_ae, dict):
                        ae_findings.append(f"{period_name}: AE breakdown structure: {list(sample_ae.keys())}")
    
    return ae_findings

def analyze_proposal_and_legals_stages(monthly_data, yearly_data):
    """Analyze specific data for Proposal sent and Legals stages"""
    analysis = {
        'proposal_sent_deals': [],
        'legals_deals': [],
        'stage_counts': {},
        'stage_values': {}
    }
    
    datasets = [("monthly", monthly_data), ("yearly", yearly_data)]
    
    for period_name, data in datasets:
        if not data:
            continue
        
        # Look through all sections for deals with these stages
        def find_deals_by_stage(obj, target_stages, current_path=""):
            deals_found = []
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{current_path}.{key}" if current_path else key
                    
                    # Check if this is a deal with stage information
                    if key == 'stage' and isinstance(value, str):
                        for target_stage in target_stages:
                            if target_stage.lower() in value.lower():
                                deals_found.append(f"{period_name}: Deal with {value} stage found at {current_path}")
                    
                    # Recursive search
                    if isinstance(value, (dict, list)):
                        deals_found.extend(find_deals_by_stage(value, target_stages, new_path))
                        
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    deals_found.extend(find_deals_by_stage(item, target_stages, f"{current_path}[{i}]"))
            
            return deals_found
        
        # Search for Proposal sent and Legals deals
        target_stages = ['proposal sent', 'legals', 'c proposal sent', 'b legals']
        deals_found = find_deals_by_stage(data, target_stages)
        
        for deal in deals_found:
            if 'proposal' in deal.lower():
                analysis['proposal_sent_deals'].append(deal)
            if 'legals' in deal.lower():
                analysis['legals_deals'].append(deal)
    
    return analysis

def extract_proposal_sent_data(monthly_data, yearly_data):
    """Extract specific data for Proposal sent stage deals"""
    findings = []
    
    datasets = [("monthly", monthly_data), ("yearly", yearly_data)]
    
    for period_name, data in datasets:
        if not data:
            continue
        
        # Look in closing_projections for deals
        if 'closing_projections' in data:
            projections = data['closing_projections']
            for timeframe, timeframe_data in projections.items():
                if isinstance(timeframe_data, dict) and 'deals' in timeframe_data:
                    deals = timeframe_data['deals']
                    if isinstance(deals, list):
                        proposal_deals = [deal for deal in deals if isinstance(deal, dict) and 
                                        deal.get('stage', '').lower() in ['c proposal sent', 'proposal sent']]
                        if proposal_deals:
                            findings.append(f"{period_name}.closing_projections.{timeframe}.deals: {len(proposal_deals)} 'Proposal sent' deals")
                            if proposal_deals:
                                sample = proposal_deals[0]
                                findings.append(f"  Sample fields: {list(sample.keys())}")
        
        # Look in pipe_metrics for AE breakdown
        if 'pipe_metrics' in data and 'ae_breakdown' in data['pipe_metrics']:
            ae_breakdown = data['pipe_metrics']['ae_breakdown']
            if isinstance(ae_breakdown, list):
                findings.append(f"{period_name}.pipe_metrics.ae_breakdown: Pipeline data by AE available")
    
    return findings

def extract_legals_data(monthly_data, yearly_data):
    """Extract specific data for Legals stage deals"""
    findings = []
    
    datasets = [("monthly", monthly_data), ("yearly", yearly_data)]
    
    for period_name, data in datasets:
        if not data:
            continue
        
        # Look in closing_projections for deals
        if 'closing_projections' in data:
            projections = data['closing_projections']
            for timeframe, timeframe_data in projections.items():
                if isinstance(timeframe_data, dict) and 'deals' in timeframe_data:
                    deals = timeframe_data['deals']
                    if isinstance(deals, list):
                        legals_deals = [deal for deal in deals if isinstance(deal, dict) and 
                                      deal.get('stage', '').lower() in ['b legals', 'legals']]
                        if legals_deals:
                            findings.append(f"{period_name}.closing_projections.{timeframe}.deals: {len(legals_deals)} 'Legals' deals")
                            if legals_deals:
                                sample = legals_deals[0]
                                findings.append(f"  Sample fields: {list(sample.keys())}")
    
    return findings

def extract_poa_booked_data(monthly_data, yearly_data):
    """Extract POA booked metrics"""
    findings = []
    
    datasets = [("monthly", monthly_data), ("yearly", yearly_data)]
    
    for period_name, data in datasets:
        if not data:
            continue
        
        # Look in dashboard_blocks
        if 'dashboard_blocks' in data:
            blocks = data['dashboard_blocks']
            for block_name, block_data in blocks.items():
                if isinstance(block_data, dict):
                    poa_fields = [k for k in block_data.keys() if 'poa' in k.lower()]
                    if poa_fields:
                        findings.append(f"{period_name}.dashboard_blocks.{block_name}: POA fields {poa_fields}")
                        for field in poa_fields:
                            findings.append(f"  {field}: {block_data[field]}")
        
        # Look in meetings_attended
        if 'meetings_attended' in data:
            meetings = data['meetings_attended']
            if isinstance(meetings, dict):
                poa_fields = [k for k in meetings.keys() if 'poa' in k.lower()]
                if poa_fields:
                    findings.append(f"{period_name}.meetings_attended: POA fields {poa_fields}")
    
    return findings

def extract_weighted_pipeline_data(monthly_data, yearly_data):
    """Extract weighted pipeline calculations"""
    findings = []
    
    datasets = [("monthly", monthly_data), ("yearly", yearly_data)]
    
    for period_name, data in datasets:
        if not data:
            continue
        
        # Look in dashboard_blocks
        if 'dashboard_blocks' in data:
            blocks = data['dashboard_blocks']
            for block_name, block_data in blocks.items():
                if isinstance(block_data, dict):
                    weighted_fields = [k for k in block_data.keys() if 'weighted' in k.lower() or 'aggregate' in k.lower()]
                    if weighted_fields:
                        findings.append(f"{period_name}.dashboard_blocks.{block_name}: Weighted fields {weighted_fields}")
                        for field in weighted_fields:
                            findings.append(f"  {field}: {block_data[field]}")
        
        # Look in pipe_metrics
        if 'pipe_metrics' in data:
            pipe_metrics = data['pipe_metrics']
            if isinstance(pipe_metrics, dict):
                weighted_fields = [k for k in pipe_metrics.keys() if 'weighted' in k.lower()]
                if weighted_fields:
                    findings.append(f"{period_name}.pipe_metrics: Weighted fields {weighted_fields}")
    
    return findings

def extract_current_pipeline_data(monthly_data):
    """Extract current month pipeline creation data"""
    findings = []
    
    if not monthly_data:
        return findings
    
    # Look in dashboard_blocks for pipe creation
    if 'dashboard_blocks' in monthly_data:
        blocks = monthly_data['dashboard_blocks']
        for block_name, block_data in blocks.items():
            if 'pipe' in block_name.lower() and isinstance(block_data, dict):
                findings.append(f"monthly.dashboard_blocks.{block_name}: Pipeline creation block")
                for key, value in block_data.items():
                    if 'pipe' in key.lower() or 'created' in key.lower():
                        findings.append(f"  {key}: {value}")
    
    # Look in pipe_metrics
    if 'pipe_metrics' in monthly_data:
        pipe_metrics = monthly_data['pipe_metrics']
        if isinstance(pipe_metrics, dict):
            findings.append(f"monthly.pipe_metrics: Pipeline metrics available")
            for key, value in pipe_metrics.items():
                if 'created' in key.lower():
                    findings.append(f"  {key}: {value}")
    
    return findings

def extract_ae_pipeline_data(monthly_data, yearly_data):
    """Extract per-AE pipeline breakdown data"""
    findings = []
    
    datasets = [("monthly", monthly_data), ("yearly", yearly_data)]
    
    for period_name, data in datasets:
        if not data:
            continue
        
        # Look in pipe_metrics for AE breakdown
        if 'pipe_metrics' in data and 'ae_breakdown' in data['pipe_metrics']:
            ae_breakdown = data['pipe_metrics']['ae_breakdown']
            if isinstance(ae_breakdown, list) and len(ae_breakdown) > 0:
                findings.append(f"{period_name}.pipe_metrics.ae_breakdown: {len(ae_breakdown)} AEs with pipeline data")
                sample_ae = ae_breakdown[0]
                if isinstance(sample_ae, dict):
                    findings.append(f"  AE fields: {list(sample_ae.keys())}")
                    for key, value in sample_ae.items():
                        findings.append(f"    {key}: {value}")
        
        # Look in ae_performance
        if 'ae_performance' in data:
            ae_perf = data['ae_performance']
            if isinstance(ae_perf, dict) and 'ae_performance' in ae_perf:
                ae_list = ae_perf['ae_performance']
                if isinstance(ae_list, list) and len(ae_list) > 0:
                    findings.append(f"{period_name}.ae_performance.ae_performance: {len(ae_list)} AEs with performance data")
                    sample_ae = ae_list[0]
                    if isinstance(sample_ae, dict):
                        findings.append(f"  AE performance fields: {list(sample_ae.keys())}")
    
    return findings

def main():
    """Run pipeline data structure inspection"""
    print(f"🚀 Starting Pipeline Data Structure Inspection")
    print(f"Backend URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run the comprehensive pipeline inspection
    success = test_pipeline_data_structure_inspection()
    
    if success:
        print(f"\n🎉 PIPELINE DATA STRUCTURE INSPECTION COMPLETED SUCCESSFULLY!")
        print(f"✅ Found sufficient pipeline data for Deals & Pipeline tab implementation")
    else:
        print(f"\n⚠️  PIPELINE DATA STRUCTURE INSPECTION COMPLETED WITH LIMITATIONS")
        print(f"❌ Some required pipeline data may need custom implementation")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)