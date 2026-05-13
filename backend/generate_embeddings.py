import os
import time
from datetime import datetime
from supabase import create_client
from tqdm import tqdm

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://kzearkcqdlrkxdjgdmoc.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt6ZWFya2NxZGxya3hkamdkbW9jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzNzEwNDUsImV4cCI6MjA5MTk0NzA0NX0.U1ET54nCBIMy3Dh9KJr7zNp7Usb7H1igzOSw9wL4QJU")
TABLE_NAME = "cars"
BATCH_SIZE = 1000
OUTPUT_FILE = "car_descriptions_preview.txt"


def create_car_description(car):
    """Create a descriptive string from car attributes"""
    parts = []
    
    # Basic info
    if car.get('year'):
        parts.append(f"Vehicle: {car['year']}")
    
    if car.get('manufacturer'):
        parts.append(f"{car['manufacturer'].strip()}")
    
    if car.get('model'):
        parts.append(f"{car['model'].strip()}.")
    
    # Condition and status
    if car.get('condition'):
        parts.append(f"Condition: {car['condition'].strip()}.")
    
    if car.get('title_status'):
        parts.append(f"{car['title_status'].strip()} title.")
    
    # Technical specs
    if car.get('cylinders'):
        parts.append(f"Engine: {car['cylinders'].strip()}.")
    
    if car.get('fuel'):
        parts.append(f"Fuel: {car['fuel'].strip()}.")
    
    if car.get('transmission'):
        parts.append(f"Transmission: {car['transmission'].strip()}.")
    
    if car.get('drive'):
        parts.append(f"Drive: {car['drive'].strip()}.")
    
    # Physical characteristics
    if car.get('size'):
        parts.append(f"Size: {car['size'].strip()}.")
    
    if car.get('type'):
        parts.append(f"Type: {car['type'].strip()}.")
    
    if car.get('paint_color'):
        parts.append(f"Color: {car['paint_color'].strip()}.")
    
    # Mileage
    if car.get('odometer'):
        parts.append(f"Mileage: {car['odometer']:,}.")

    
    # Posting date
    if car.get('posting_date'):
        posting_date = str(car['posting_date']).split('T')[0]  # Just the date part
        parts.append(f"Posted: {posting_date}.")
    
    # Join all parts into natural sentence
    description = " ".join(parts)
    return description


def fetch_all_cars(supabase):
    """Fetch all cars from the database with pagination (following seed_db_script pattern)"""
    print("Fetching all cars from database")
    all_cars = []
    
    # Supabase has a hard limit of 1000 rows per request
    page_size = 1000
    offset = 0
    
    while True:
        # Select all relevant columns, exclude embedding for now
        response = supabase.table(TABLE_NAME).select(
            "id", "year", "manufacturer", "model", "condition", "cylinders", 
            "fuel", "odometer", "title_status", "transmission", "drive", 
            "size", "type", "paint_color", "description", "posting_date"
        ).limit(page_size).offset(offset).execute()
        
        if not response.data:
            break
            
        all_cars.extend(response.data)
        fetched = len(response.data)
        offset += fetched
        print(f"  Fetched {len(all_cars)} cars")
        
        # If we got fewer than page_size rows, we've reached the end
        if fetched < page_size:
            break
        break
    
    print(f"Total cars fetched: {len(all_cars):,}")
    return all_cars


def preview_descriptions(cars, num_samples=10):
    """Generate and preview descriptions for a sample of cars"""
    print(f"\n{'='*60}")
    print("PREVIEW MODE - Generating descriptions for sample cars")
    print(f"{'='*60}")
    
    # Take first N cars for preview
    sample_cars = cars[:num_samples]
    
    descriptions = []
    for i, car in enumerate(sample_cars, 1):
        description = create_car_description(car)
        descriptions.append({
            'id': car.get('id'),
            'description': description
        })
        
        print(f"\n--- Car {i} (ID: {car.get('id')}) ---")
        print(f"Description: {description}")
        print(f"Length: {len(description)} characters")
    
    # Save to file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("Car Descriptions Preview\n")
        f.write("=" * 40 + "\n\n")
        
        for i, desc_data in enumerate(descriptions, 1):
            f.write(f"Car {i} (ID: {desc_data['id']})\n")
            f.write(f"Description: {desc_data['description']}\n")
            f.write(f"Length: {len(desc_data['description'])} characters\n")
            f.write("-" * 40 + "\n\n")
    
    print(f"\n✅ Preview saved to: {OUTPUT_FILE}")
    return descriptions


def update_embeddings_batch(supabase, embeddings_batch):
    """Update embeddings for a batch of cars (following seed_db_script pattern)"""
    try:
        # Prepare update data
        update_data = []
        for item in embeddings_batch:
            update_data.append({
                'id': item['id'],
                'embedding': item['embedding']
            })
        
        # Update in batch - using upsert to handle embedding updates
        response = supabase.table(TABLE_NAME).upsert(update_data).execute()
        return len(update_data), None
        
    except Exception as e:
        error_msg = str(e)
        return 0, error_msg


def process_embeddings_batch(cars_batch, error_log):
    """Process embeddings for a batch of cars (placeholder for step 3)"""
    embeddings_batch = []
    
    for car in cars_batch:
        description = create_car_description(car)
        
        # TODO: Step 3 - Generate actual embedding here
        # For now, create a placeholder embedding (1536 dimensions for OpenAI)
        placeholder_embedding = [0.0] * 1536
        
        embeddings_batch.append({
            'id': car.get('id'),
            'description': description,
            'embedding': placeholder_embedding
        })
    
    return embeddings_batch


def generate_all_embeddings(supabase, cars):
    """Generate and update embeddings for all cars with batch processing"""
    print(f"\n{'='*60}")
    print("GENERATING EMBEDDINGS FOR ALL CARS")
    print(f"{'='*60}")
    
    # Setup error logging
    error_log = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_log_file = f"embedding_errors_{timestamp}.log"
    
    # Process in batches following seed_db_script pattern
    batch = []
    processed = 0
    failed = 0
    
    for car in tqdm(cars, desc="Processing embeddings"):
        batch.append(car)
        
        # Process batch when full
        if len(batch) >= BATCH_SIZE:
            embeddings_batch = process_embeddings_batch(batch, error_log)
            
            # Update embeddings in database
            success_count, error_msg = update_embeddings_batch(supabase, embeddings_batch)
            
            if error_msg:
                print(f"\n❌ Batch update failed: {error_msg[:200]}")
                
                # Log each failed record
                for car in batch:
                    error_log.append({
                        'car_id': car.get('id', 'unknown'),
                        'error': error_msg,
                        'car_data': car
                    })
                
                failed += len(batch)
            else:
                processed += success_count
            
            batch = []
            time.sleep(0.05)  # Rate limiting (same as seed_db_script)
    
    # Process remaining batch
    if batch:
        embeddings_batch = process_embeddings_batch(batch, error_log)
        success_count, error_msg = update_embeddings_batch(supabase, embeddings_batch)
        
        if error_msg:
            print(f"\n❌ Final batch update failed: {error_msg[:200]}")
            
            for car in batch:
                error_log.append({
                    'car_id': car.get('id', 'unknown'),
                    'error': error_msg,
                    'car_data': car
                })
            
            failed += len(batch)
        else:
            processed += success_count
    
    # Write error log if there were failures
    if error_log:
        import json
        with open(error_log_file, 'w', encoding='utf-8') as f:
            json.dump(error_log, f, indent=2, default=str)
        print(f"\n⚠️ Error log written to: {error_log_file}")
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"EMBEDDING UPDATE COMPLETE!")
    print(f"{'='*60}")
    print(f"Total cars:         {len(cars):,}")
    print(f"Successfully updated: {processed:,}")
    print(f"Failed:             {failed:,}")
    print(f"{'='*60}")
    
    return processed, failed


def main():
    print("="*60)
    print("Car Embedding Generator")
    print("="*60)
    
    # Initialize Supabase client
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    
    # Step 1: Fetch all cars from database
    cars = fetch_all_cars(supabase)
    
    if not cars:
        print("No cars found in database!")
        return
    
    # Step 2: Preview descriptions for first 10 cars
    preview_descriptions(cars, num_samples=10)
    
    # Step 3: Ask if user wants to process embeddings
    confirm = input(f"\nProcess embeddings for all {len(cars):,} cars? (y/n): ")
    if confirm.lower() == 'y':
        processed, failed = generate_all_embeddings(supabase, cars)
        
        if failed == 0:
            print(f"\n✅ All {processed:,} embeddings updated successfully!")
        else:
            print(f"\n⚠️ {failed:,} cars failed. Check error log for details.")
    else:
        print("Cancelled. Only preview was generated.")


if __name__ == "__main__":
    main()
