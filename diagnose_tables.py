"""
Diagnostic test to check what tables are in the system.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from api.json_exporter import JSONExporter
from objects import Group, Table, Column

def diagnose_tables():
    """Check what tables are actually being stored."""
    
    # Let's recreate the structure that should have 1 mart, 1 stg, 3 src tables
    groups = {
        'src': Group('src'),
        'stg': Group('stg'), 
        'mart': Group('mart')
    }
    
    # Create 3 source tables
    src_customers = Table('src', 'customers', description='Source customer data')
    src_orders = Table('src', 'orders', description='Source order data')
    src_products = Table('src', 'products', description='Source product data')
    
    # Create 1 staging table
    stg_enriched = Table('stg', 'enriched_data', description='Enriched data')
    
    # Create 1 mart table
    mart_summary = Table('mart', 'business_summary', description='Business summary')
    
    # The key here is how the tables dictionary is structured
    # Let's check both ways of keying tables
    
    print("=== TESTING DIFFERENT TABLE DICTIONARY STRUCTURES ===")
    
    # Method 1: Key by table name only
    tables_by_name = {
        'customers': src_customers,
        'orders': src_orders, 
        'products': src_products,
        'enriched_data': stg_enriched,
        'business_summary': mart_summary
    }
    
    print("\n--- Method 1: Tables keyed by name only ---")
    print(f"Total tables in dictionary: {len(tables_by_name)}")
    for key, table in tables_by_name.items():
        print(f"  {key} -> {table.group}.{table.name}")
    
    # Method 2: Key by full name (group.table)
    tables_by_full_name = {
        'src.customers': src_customers,
        'src.orders': src_orders,
        'src.products': src_products, 
        'stg.enriched_data': stg_enriched,
        'mart.business_summary': mart_summary
    }
    
    print("\n--- Method 2: Tables keyed by full name ---")
    print(f"Total tables in dictionary: {len(tables_by_full_name)}")
    for key, table in tables_by_full_name.items():
        print(f"  {key} -> {table.group}.{table.name}")
    
    # Test both with JSONExporter
    columns = {}  # Empty for this test
    
    print("\n=== TESTING JSON EXPORTER OUTPUT ===")
    
    # Test method 1
    exporter1 = JSONExporter(groups, tables_by_name, columns)
    result1 = exporter1.to_json()
    
    print("\n--- Method 1 Results ---")
    for group in result1['groups']:
        print(f"Group '{group['group']}' has {len(group['tables'])} tables: {group['tables']}")
    
    # Test method 2  
    exporter2 = JSONExporter(groups, tables_by_full_name, columns)
    result2 = exporter2.to_json()
    
    print("\n--- Method 2 Results ---")
    for group in result2['groups']:
        print(f"Group '{group['group']}' has {len(group['tables'])} tables: {group['tables']}")
    
    print(f"\n=== EXPECTED: src=3, stg=1, mart=1 ===")

if __name__ == '__main__':
    diagnose_tables()
