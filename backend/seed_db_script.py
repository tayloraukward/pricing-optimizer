import os
import csv
import time
from datetime import datetime
from supabase import create_client
from tqdm import tqdm

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://kzearkcqdlrkxdjgdmoc.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt6ZWFya2NxZGxya3hkamdkbW9jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzNzEwNDUsImV4cCI6MjA5MTk0NzA0NX0.U1ET54nCBIMy3Dh9KJr7zNp7Usb7H1igzOSw9wL4QJU")
CSV_PATH = "/Users/tayloraukward/Downloads/vehicles.csv"
TABLE_NAME = "cars"  # Adjust if your table name differs
BATCH_SIZE = 1000  # Insert in batches to avoid rate limits


def inspect_table_schema(supabase):
    """Fetch first 100 rows to understand schema and existing data"""
    print("Fetching existing data from Supabase to understand schema...")
    response = supabase.table(TABLE_NAME).select("*").limit(100).execute()
    
    if response.data:
        print(f"\n✅ Table '{TABLE_NAME}' exists with {len(response.data)} sample rows")
        print(f"Columns: {list(response.data[0].keys())}")
        print(f"\nSample row:")
        for key, val in response.data[0].items():
            print(f"  {key}: {val}")
    else:
        print(f"⚠️ No data found in table '{TABLE_NAME}'")
    
    return response.data


def get_existing_ids(supabase):
    """Fetch all existing IDs for deduplication"""
    print("Fetching existing IDs for deduplication...")
    existing_ids = set()
    
    # Supabase has a hard limit of 1000 rows per request
    page_size = 1000
    offset = 0
    
    while True:
        # Use explicit limit with range to ensure we get full pages
        response = supabase.table(TABLE_NAME).select("id").limit(page_size).offset(offset).execute()
        
        if not response.data:
            break
            
        for row in response.data:
            existing_ids.add(str(row['id']))
        
        fetched = len(response.data)
        offset += fetched
        print(f"  Fetched {len(existing_ids)} existing IDs...")
        
        # If we got fewer than page_size rows, we've reached the end
        if fetched < page_size:
            break
    
    print(f"Total existing records: {len(existing_ids)}")
    return existing_ids


def parse_value(value, column):
    """Parse and clean CSV values based on column type"""
    if value is None or value.strip() == '':
        return None
    
    value = value.strip()
    
    # Numeric fields
    if column in ['id', 'price', 'year', 'odometer']:
        try:
            # Handle floats for price/odometer, ints for id/year
            if column in ['price', 'odometer']:
                return float(value) if '.' in value else int(value)
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    # Date field
    if column == 'posting_date' and value:
        try:
            # Parse ISO format date
            return value
        except:
            return None
    
    # Float fields (lat, long)
    if column in ['lat', 'long']:
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    return value


def preview_csv(existing_ids):
    """Preview CSV data without importing (READ-ONLY MODE)"""
    print(f"\n{'='*60}")
    print("PREVIEW MODE - No writes will be performed")
    print(f"{'='*60}")
    print(f"CSV file: {CSV_PATH}")
    
    # Count total rows
    print("\nCounting CSV rows...")
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        total_rows = sum(1 for _ in f) - 1
    
    print(f"Total CSV rows: {total_rows}")
    print(f"Existing records in DB: {len(existing_ids)}")
    
    # Preview first 5 records that would be imported
    print(f"\n{'='*60}")
    print("Sample records that would be imported (first 5 new records):")
    print(f"{'='*60}")
    
    new_records = []
    skipped = 0
    
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            row_id = row.get('id', '').strip()
            if row_id in existing_ids:
                skipped += 1
                continue
            
            record = {}
            for key, value in row.items():
                parsed = parse_value(value, key)
                if parsed is not None:
                    record[key] = parsed
            
            if record:
                new_records.append(record)
                if len(new_records) >= 5:
                    break
    
    for i, rec in enumerate(new_records, 1):
        print(f"\n--- Record {i} ---")
        for key, val in rec.items():
            print(f"  {key}: {val}")
    
    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"  - Total CSV rows: {total_rows}")
    print(f"  - Existing in DB (will skip): ~{len(existing_ids)}")
    print(f"  - New records to import: ~{total_rows - len(existing_ids)}")
    print(f"{'='*60}")
    print("\n✅ This was a preview only. No data was written.")
    print("To enable writes, uncomment the import_csv call in main().")


def import_csv(supabase, existing_ids):
    """Import CSV data with deduplication and error logging"""
    print(f"\n{'='*60}")
    print("IMPORT MODE - Writing to Supabase")
    print(f"{'='*60}")
    print(f"CSV file: {CSV_PATH}")
    
    # Setup error logging
    error_log = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_log_file = f"import_errors_{timestamp}.log"
    
    # Count total rows
    print("\nCounting CSV rows...")
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        total_rows = sum(1 for _ in f) - 1
    
    print(f"Total CSV rows: {total_rows}")
    print(f"Existing records in DB (will skip): {len(existing_ids)}")
    
    # Process CSV
    batch = []
    imported = 0
    skipped = 0
    failed = 0
    
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in tqdm(reader, total=total_rows, desc="Importing"):
            row_id = row.get('id', '').strip()
            
            # Deduplication check
            if row_id in existing_ids:
                skipped += 1
                continue
            
            # Build record
            record = {}
            for key, value in row.items():
                parsed = parse_value(value, key)
                if parsed is not None:
                    record[key] = parsed
            
            if not record:
                failed += 1
                error_log.append({
                    'csv_id': row_id,
                    'error': 'Empty record after parsing',
                    'raw_data': row
                })
                continue
            
            batch.append(record)
            
            # Batch insert
            if len(batch) >= BATCH_SIZE:
                try:
                    response = supabase.table(TABLE_NAME).insert(batch).execute()
                    imported += len(batch)
                    
                    # Update existing_ids with newly imported records
                    for r in batch:
                        if 'id' in r:
                            existing_ids.add(str(r['id']))
                    
                    batch = []
                    time.sleep(0.05)  # Rate limiting
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"\n❌ Batch insert failed: {error_msg[:200]}")
                    
                    # Log each failed record
                    for record in batch:
                        error_log.append({
                            'csv_id': record.get('id', 'unknown'),
                            'error': error_msg,
                            'record': record
                        })
                    
                    failed += len(batch)
                    batch = []
    
    # Insert remaining batch
    if batch:
        try:
            response = supabase.table(TABLE_NAME).insert(batch).execute()
            imported += len(batch)
            
            for r in batch:
                if 'id' in r:
                    existing_ids.add(str(r['id']))
                    
        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ Final batch insert failed: {error_msg[:200]}")
            
            for record in batch:
                error_log.append({
                    'csv_id': record.get('id', 'unknown'),
                    'error': error_msg,
                    'record': record
                })
            
            failed += len(batch)
    
    # Write error log if there were failures
    if error_log:
        import json
        with open(error_log_file, 'w', encoding='utf-8') as f:
            json.dump(error_log, f, indent=2, default=str)
        print(f"\n⚠️ Error log written to: {error_log_file}")
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"IMPORT COMPLETE!")
    print(f"{'='*60}")
    print(f"Total CSV rows:     {total_rows:,}")
    print(f"Skipped (exists):   {skipped:,}")
    print(f"Successfully imported: {imported:,}")
    print(f"Failed:             {failed:,}")
    print(f"{'='*60}")


def main():
    print("="*60)
    print("Supabase Vehicle Data Import Script")
    print("="*60)
    
    # Initialize Supabase client
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    
    # Step 1: Inspect table schema
    sample_data = inspect_table_schema(supabase)
    
    if not sample_data:
        print("\n⚠️ WARNING: No sample data found. Please verify the table name.")
        return
    
    # Step 2: Get existing IDs for deduplication
    existing_ids = get_existing_ids(supabase)
    
    # Step 3: Preview what would be imported
    print("\nRunning preview of CSV data...")
    preview_csv(existing_ids)
    
    # Step 4: Confirm and import
    # Calculate new records to import
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        total_csv = sum(1 for _ in f) - 1
    new_to_import = total_csv - len(existing_ids)
    
    confirm = input(f"\nReady to import {new_to_import:,} new records ({len(existing_ids):,} existing will be skipped). Continue? (y/n): ")
    if confirm.lower() == 'y':
        import_csv(supabase, existing_ids)
    else:
        print("Import cancelled.")


if __name__ == "__main__":
    main()