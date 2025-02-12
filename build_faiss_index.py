import sqlite3
import numpy as np
import faiss
import pickle
import json
import logging
import faulthandler
from sentence_transformers import SentenceTransformer

# Enable faulthandler for segmentation fault debugging.
faulthandler.enable()

# Configure logging.
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Database and file paths.
DB_PATH = "anilist_global.db"
EMBEDDINGS_FILE = "embeddings_cache.pkl"
VECTOR_DB_PATH = "anime_vectors.index"

def extract_filtered_tags(tags_json, threshold=60):
    """
    Extract tag names from a JSON-encoded string, filtering by the given threshold.
    
    Parameters:
      tags_json (str): A JSON-encoded list of tag objects.
      threshold (int): The minimum importance/rank required for a tag to be included.
    
    Returns:
      str: A space-separated, alphabetically sorted string of tag names that meet the threshold.
           Returns an empty string if no tags qualify or if parsing fails.
    """
    if not tags_json:
        return ""
    try:
        tags_list = json.loads(tags_json)
        # Check for 'importance'; if missing, use 'rank'
        filtered_tags = [
            tag["name"] 
            for tag in tags_list 
            if tag.get("importance", tag.get("rank", 0)) >= threshold
        ]
        # Remove duplicates and sort the results.
        return " ".join(sorted(set(filtered_tags)))
    except Exception as e:
        logging.warning(f"Error parsing tags: {e}")
        return ""

def load_anime_data():
    """
    Load anime data from the SQLite database.

    For each record, we load:
      - id
      - a preferred title (using title_english if available, then title_romaji, then title_native)
      - genres (stored as JSON in the database) which we convert into a single string.
      - tags (stored as JSON in the database) which we filter by an importance threshold and convert into a string.

    Returns:
      A list of tuples: (anime_id, text) where text is the combination of the title, genres, and filtered tags.
    """
    logging.info("Connecting to the database...")
    try:
        conn = sqlite3.connect(DB_PATH)
    except Exception as e:
        logging.error(f"Error connecting to database: {e}")
        raise

    cursor = conn.cursor()
    # Updated query to also retrieve tags.
    query = "SELECT id, title_english, title_romaji, title_native, genres, tags FROM global_media"
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        logging.info(f"Fetched {len(results)} records from the database.")
    except Exception as e:
        logging.error(f"Error executing query: {e}")
        results = []
    finally:
        conn.close()
    
    anime_data = []
    for row in results:
        anime_id = row[0]
        title = row[1] or row[2] or row[3] or "Unknown Title"
        
        try:
            genres_list = json.loads(row[4]) if row[4] else []
            genres = " ".join(sorted(set(genres_list)))
        except Exception as e:
            logging.warning(f"Error parsing genres for anime_id {anime_id}: {e}")
            genres = ""
        
        # Use the extracted function for tags.
        tags_text = extract_filtered_tags(row[5], threshold=60)
        # logging.debug(f"Tags extracted {anime_id}: {tags_text}")
        
        # Combine title, genres, and filtered tags into one text string.
        text = f"Title: {title}. Genres: {genres}. Important tags: {tags_text}"
        # logging.debug(f"Created text entry for anime_id {anime_id}: {text}")
        anime_data.append((anime_id, text))
    
    logging.debug("Completed loading anime data.")  
    return anime_data

def build_faiss_index():
    logging.info("Loading SentenceTransformer model 'all-mpnet-base-v2'...")
    try:
        model = SentenceTransformer("all-mpnet-base-v2")
    except Exception as e:
        logging.error(f"Error loading SentenceTransformer model: {e}")
        raise

    logging.info("Loading anime data from database...")
    anime_data = load_anime_data()
    logging.info(f"Building embeddings for {len(anime_data)} anime entries...")
    
    ids = []
    embeddings = []
    for i, (anime_id, text) in enumerate(anime_data, start=1):
        try:
            emb = model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        except Exception as e:
            logging.error(f"Error encoding text for anime_id {anime_id}: {e}")
            continue
        embeddings.append(emb)
        ids.append(anime_id)
        
        if i % 100 == 0:
            logging.debug(f"Processed {i} entries...")
    
    if not embeddings:
        logging.error("No embeddings were generated; aborting index build.")
        return

    embeddings = np.array(embeddings).astype("float32")
    logging.info(f"Embeddings array shape: {embeddings.shape}")

    logging.info("Creating FAISS index...")
    try:
        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(embeddings)
        logging.info("FAISS index created and embeddings added.")
    except Exception as e:
        logging.error(f"Error building FAISS index: {e}")
        raise

    logging.info(f"Saving FAISS index to {VECTOR_DB_PATH}...")
    try:
        faiss.write_index(index, VECTOR_DB_PATH)
    except Exception as e:
        logging.error(f"Error saving FAISS index: {e}")
        raise

    logging.info(f"Saving embeddings mapping to {EMBEDDINGS_FILE}...")
    try:
        with open(EMBEDDINGS_FILE, "wb") as f:
            pickle.dump({"ids": ids, "embeddings": embeddings}, f)
    except Exception as e:
        logging.error(f"Error saving embeddings mapping: {e}")
        raise
    
    logging.info(f"Saved FAISS index with {len(ids)} entries.")

if __name__ == "__main__":
    try:
        build_faiss_index()
    except Exception as err:
        logging.exception("An error occurred during FAISS index building:")