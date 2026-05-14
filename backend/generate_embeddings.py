import os
import time
import json
from datetime import datetime
from supabase import create_client
from openai import OpenAI

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://kzearkcqdlrkxdjgdmoc.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt6ZWFya2NxZGxya3hkamdkbW9jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzNzEwNDUsImV4cCI6MjA5MTk0NzA0NX0.U1ET54nCBIMy3Dh9KJr7zNp7Usb7H1igzOSw9wL4QJU")
TABLE_NAME = "cars"
BATCH_SIZE = 1000
OUTPUT_FILE = "car_descriptions_preview.txt"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "30"))


def create_car_description(car):
    """Create a descriptive string from car attributes"""
    parts = []

    if car.get('year'):
        parts.append(f"Vehicle: {car['year']}")

    if car.get('manufacturer'):
        parts.append(f"{car['manufacturer'].strip()}")

    if car.get('model'):
        parts.append(f"{car['model'].strip()}.")

    if car.get('condition'):
        parts.append(f"Condition: {car['condition'].strip()}.")

    if car.get('title_status'):
        parts.append(f"{car['title_status'].strip()} title.")

    if car.get('cylinders'):
        parts.append(f"Engine: {car['cylinders'].strip()}.")

    if car.get('fuel'):
        parts.append(f"Fuel: {car['fuel'].strip()}.")

    if car.get('transmission'):
        parts.append(f"Transmission: {car['transmission'].strip()}.")

    if car.get('drive'):
        parts.append(f"Drive: {car['drive'].strip()}.")

    if car.get('size'):
        parts.append(f"Size: {car['size'].strip()}.")

    if car.get('type'):
        parts.append(f"Type: {car['type'].strip()}.")

    if car.get('paint_color'):
        parts.append(f"Color: {car['paint_color'].strip()}.")

    if car.get('odometer'):
        parts.append(f"Mileage: {car['odometer']:,}.")

    if car.get('posting_date'):
        posting_date = str(car['posting_date']).split('T')[0]
        parts.append(f"Posted: {posting_date}.")

    return " ".join(parts)


def preview_descriptions(cars, num_samples=10):
    """Generate and preview descriptions for a sample of cars"""
    print(f"\n{'='*60}")
    print("PREVIEW MODE - Generating descriptions for sample cars")
    print(f"{'='*60}")

    sample_cars = cars[:num_samples]
    descriptions = []

    for i, car in enumerate(sample_cars, 1):
        description = create_car_description(car)
        descriptions.append({'id': car.get('id'), 'description': description})

        print(f"\n--- Car {i} (ID: {car.get('id')}) ---")
        print(f"Description: {description}")
        print(f"Length: {len(description)} characters")

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


def process_embeddings_batch(cars_batch, error_log, openai_client):
    """
    Generates embeddings for an entire batch of cars in a single
    OpenAI request. Cars producing empty descriptions are logged
    and skipped rather than failing the whole batch.
    """
    embeddings_batch = []

    descriptions = [create_car_description(car) for car in cars_batch]
    car_ids = [car.get('id') for car in cars_batch]

    if not descriptions:
        return embeddings_batch

    # Debug: identify and log any cars producing empty descriptions
    empty_indices = [i for i, d in enumerate(descriptions) if not d.strip()]
    if empty_indices:
        print(f"\n⚠️  Found {len(empty_indices)} empty description(s) in this batch:")
        error_log.append({
            'error': 'Empty description generated — all fields null or missing',
            'car_ids': [car_ids[i] for i in empty_indices]
        })

    # Filter out empty descriptions before sending to OpenAI
    valid_pairs = [(d, car_ids[i]) for i, d in enumerate(descriptions) if d.strip()]

    if not valid_pairs:
        print("⚠️  Entire batch produced empty descriptions, skipping OpenAI call.")
        return embeddings_batch

    valid_descriptions, valid_ids = zip(*valid_pairs)
    skipped = len(descriptions) - len(valid_descriptions)
    if skipped:
        print(f"⚠️  Skipping {skipped} car(s) with empty descriptions, processing remaining {len(valid_descriptions):,}...")

    try:
        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=list(valid_descriptions),
            dimensions=EMBEDDING_DIMENSIONS
        )

        for data in response.data:
            embeddings_batch.append({
                'id': valid_ids[data.index],
                'embedding': data.embedding
            })

    except Exception as e:
        print(f"\n❌ Batch embedding request failed: {str(e)}")
        error_log.append({
            'error': f"Failed to process block of {len(valid_descriptions)} cars: {str(e)}",
            'car_ids_in_batch': list(valid_ids)
        })

    return embeddings_batch


def update_embeddings_batch(supabase, embeddings_batch, sub_batch_size=100):
    """
    Chunks embedded items into sub-batches of 100 to prevent
    Supabase HTTP timeout / gateway errors.
    """
    if not embeddings_batch:
        return 0, None

    total_written = 0

    for i in range(0, len(embeddings_batch), sub_batch_size):
        sub_batch = embeddings_batch[i:i + sub_batch_size]
        try:
            supabase.table(TABLE_NAME).upsert(sub_batch).execute()
            total_written += len(sub_batch)
            print(f"   .. Progress: wrote sub-chunk ({total_written}/{len(embeddings_batch)})")
        except Exception as e:
            return total_written, f"Sub-batch write failed at index {i}: {str(e)}"

    return total_written, None


def check_embedding_column(supabase):
    """Check if the embedding column exists and has correct dimensions"""
    print("Checking embedding column structure...")
    try:
        response = supabase.table(TABLE_NAME).select("id", "embedding").limit(1).execute()

        if response.data:
            sample_embedding = response.data[0].get('embedding')
            if sample_embedding and isinstance(sample_embedding, list):
                dimensions = len(sample_embedding)
                print(f"✅ Embedding column exists with {dimensions} dimensions")
                return dimensions
            else:
                print("⚠️ No embedding data found in sample row to verify dimensions.")
                return None
        else:
            print("⚠️ No data found in table")
            return None
    except Exception as e:
        print(f"⚠️ Could not check embedding column: {str(e)}")
        return None


def stream_and_process_embeddings(supabase, openai_client, total_preview_cars=10):
    """
    Fetches only NULL-embedding rows in batches, generates embeddings,
    and writes them back. Because processed rows drop out of the NULL
    result set automatically, offset stays at 0 every iteration.
    """
    print(f"\n{'='*60}")
    print("STARTING STREAMED BATCH EMBEDDING PROCESSING")
    print(f"{'='*60}")

    error_log = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_log_file = f"embedding_errors_{timestamp}.log"

    processed_count = 0
    failed_count = 0
    total_fetched = 0
    preview_generated = False

    print("Streaming NULL-embedding rows from database...")

    while True:
        # Only fetch rows where embedding is NULL. No offset needed because
        # successfully processed rows get an embedding written and naturally
        # fall out of this result set on the next iteration.
        response = supabase.table(TABLE_NAME).select(
            "id", "year", "manufacturer", "model", "condition", "cylinders",
            "fuel", "odometer", "title_status", "transmission", "drive",
            "size", "type", "paint_color", "description", "posting_date"
        ).is_("embedding", "null").limit(BATCH_SIZE).execute()

        batch = response.data
        if not batch:
            print("\n🎉 No more unembedded records found. Processing complete!")
            break

        fetched_this_batch = len(batch)
        total_fetched += fetched_this_batch
        print(f"\n📥 Fetched {fetched_this_batch:,} unembedded rows (total so far: {total_fetched:,})...")

        # Optional preview on the very first batch
        if not preview_generated:
            preview_descriptions(batch, num_samples=total_preview_cars)
            confirm = input("\nProceed with generating & writing embeddings for all batches? (y/n): ")
            if confirm.lower() != 'y':
                print("Execution cancelled by user after preview.")
                return processed_count, failed_count
            preview_generated = True

        # Generate embeddings
        print(f"🧠 Generating embeddings for {fetched_this_batch:,} cars...")
        embeddings_batch = process_embeddings_batch(batch, error_log, openai_client)

        # Write to Supabase
        if embeddings_batch:
            print(f"📤 Writing {len(embeddings_batch):,} embeddings to database...")
            success_count, error_msg = update_embeddings_batch(supabase, embeddings_batch)

            if error_msg:
                print(f"❌ Batch update failed: {error_msg[:200]}")
                for car in batch:
                    error_log.append({
                        'car_id': car.get('id', 'unknown'),
                        'error': error_msg,
                        'car_data': car
                    })
                failed_count += fetched_this_batch
            else:
                processed_count += success_count
                print(f"✅ Batch written. Total successfully written: {processed_count:,}")

        del batch
        del embeddings_batch
        time.sleep(0.1)

    if error_log:
        with open(error_log_file, 'w', encoding='utf-8') as f:
            json.dump(error_log, f, indent=2, default=str)
        print(f"\n⚠️ Error log written to: {error_log_file}")

    print(f"\n{'='*60}")
    print(f"STREAMED PROCESS COMPLETE!")
    print(f"{'='*60}")
    print(f"Total rows processed:               {total_fetched:,}")
    print(f"Successfully written:                {processed_count:,}")
    print(f"Failed:                             {failed_count:,}")
    print(f"{'='*60}")

    return processed_count, failed_count


def main():
    print("=" * 60)
    print("Streamed Car Embedding Generator (NULL-filtered Read-Embed-Write Loop)")
    print("=" * 60)

    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY environment variable not set!")
        return

    openai_client = OpenAI(api_key=OPENAI_API_KEY, timeout=OPENAI_TIMEOUT)

    existing_dimensions = check_embedding_column(supabase)
    if existing_dimensions and existing_dimensions != EMBEDDING_DIMENSIONS:
        print(f"⚠️ Existing embeddings have {existing_dimensions} dimensions, but script expects {EMBEDDING_DIMENSIONS}")
        confirm = input("Continue anyway? (y/n): ")
        if confirm.lower() != 'y':
            print("Cancelled.")
            return

    processed, failed = stream_and_process_embeddings(supabase, openai_client, total_preview_cars=10)

    if failed == 0 and processed > 0:
        print(f"\n✅ Migration finished completely clean!")
    elif processed > 0:
        print(f"\n⚠️ Migration completed with some errors. Check the error log.")


if __name__ == "__main__":
    main()