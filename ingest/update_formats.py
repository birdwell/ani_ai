import sqlite3
import requests
import time

ANILIST_API_URL = "https://graphql.anilist.co"

def fetch_formats_from_anilist_batch(ids, retries: int = 3, initial_backoff: float = 5.0) -> dict:
    """
    Given a list of anime IDs, hit the AniList GraphQL API in a single request and
    return a dictionary mapping each anime ID to its format.
    Implements retry logic with exponential backoff.
    """
    query = '''
    query ($ids: [Int]) {
      Page(page: 1, perPage: 50) {  # using max perPage
        media(id_in: $ids, type: ANIME) {
          id
          format
        }
      }
    }
    '''
    variables = {"ids": ids}
    backoff = initial_backoff

    for attempt in range(retries):
        try:
            response = requests.post(ANILIST_API_URL, json={"query": query, "variables": variables})
            if response.status_code == 200:
                data = response.json()
                media_list = data["data"]["Page"]["media"]
                result = {}
                for media in media_list:
                    result[media["id"]] = media.get("format", "")
                print(f"Fetched formats for batch {ids} successfully.")
                return result
            elif response.status_code == 429:
                print(f"Rate limited for batch {ids} on attempt {attempt+1}/{retries}. Waiting {backoff} seconds...")
                time.sleep(backoff)
                backoff *= 2  # exponential backoff
            else:
                print(f"Error fetching formats for batch {ids}: {response.status_code} {response.text}")
                return {}
        except Exception as e:
            print(f"Exception for batch {ids} on attempt {attempt+1}/{retries}: {e}")
            time.sleep(backoff)
            backoff *= 2

    return {}

def update_formats(db_path="anilist_global.db", batch_size: int = 50):
    """
    Connects to the global database, loads only the IDs, and then updates each record's
    format by fetching data from the AniList API in batches.
    Uses a larger batch size and waits 10 seconds between each batch.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Ensure the table has a 'format' column.
    try:
        cursor.execute("ALTER TABLE global_media ADD COLUMN format TEXT")
        conn.commit()
        print("Added 'format' column to global_media.")
    except sqlite3.OperationalError as e:
        print("Column 'format' already exists, continuing with update.")
    
    # Load only the IDs.
    cursor.execute("SELECT id FROM global_media")
    records = cursor.fetchall()
    all_ids = [record[0] for record in records]
    total_records = len(all_ids)
    print(f"Found {total_records} records to update.")
    
    updated = 0
    total_batches = (total_records + batch_size - 1) // batch_size
    for i in range(0, total_records, batch_size):
        batch_ids = all_ids[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        print(f"Processing batch {batch_num} of {total_batches}: IDs {batch_ids}")
        formats = fetch_formats_from_anilist_batch(batch_ids)
        for anime_id in batch_ids:
            fmt = formats.get(anime_id, "")
            cursor.execute("UPDATE global_media SET format = ? WHERE id = ?", (fmt, anime_id))
            updated += 1
        conn.commit()
        print(f"Batch {batch_num} complete. Total updated so far: {updated}")
        # Wait 10 seconds between batches to reduce rate limiting.
        time.sleep(10)
    
    conn.close()
    print(f"Updated format for {updated} records out of {total_records}.")

if __name__ == "__main__":
    update_formats()