import sqlite3
import json
import pickle
from sentence_transformers import SentenceTransformer

def load_global_anime(global_db_path="anilist_global.db"):
    conn = sqlite3.connect(global_db_path)
    cursor = conn.cursor()
    query = """
    SELECT id, title_english, title_romaji, title_native, description, genres, tags
    FROM global_media
    """
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    
    anime_list = []
    for row in results:
        anime_id = row[0]
        title = row[1] or row[2] or row[3] or ""
        description = row[4] if row[4] else ""
        try:
            genres = json.loads(row[5]) if row[5] else []
        except Exception:
            genres = []
        try:
            tags_data = json.loads(row[6]) if row[6] else []
        except Exception:
            tags_data = []
        
        # Extract tag names from tags_data (assuming tags_data is a list of dicts)
        tags = []
        for t in tags_data:
            if isinstance(t, dict):
                tags.append(t.get("name", ""))
            else:
                tags.append(str(t))
        
        # Combine title, description, genres, and tags into one text.
        input_text = f"{title} {description} {' '.join(genres)} {' '.join(tags)}"
        anime_list.append((anime_id, input_text))
    return anime_list

def generate_embeddings(model_name="all-mpnet-base-v2", output_file="embeddings_cache.pkl"):
    print("Loading model...")
    model = SentenceTransformer(model_name)
    print("Loading anime data from global database...")
    anime_list = load_global_anime()
    embeddings = {}
    for anime_id, text in anime_list:
        embedding = model.encode(text, convert_to_numpy=True)
        embeddings[anime_id] = embedding
    with open(output_file, "wb") as f:
        pickle.dump(embeddings, f)
    print(f"Embeddings saved to {output_file}")

if __name__ == "__main__":
    generate_embeddings()