# utils/db.py
import sqlite3
import json
import pickle

def load_global_anime_info(db_path="anilist_global.db"):
    """
    Loads global metadata including quality fields, genres, rankings, and format.
    Returns a dictionary mapping anime_id to a dictionary.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = """
    SELECT id, title_english, title_romaji, title_native, average_score, popularity, genres, rankings, format
    FROM global_media
    """
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    anime_info = {}
    for row in results:
        anime_id = row[0]
        try:
            genres = json.loads(row[6]) if row[6] else []
        except Exception:
            genres = []
        try:
            rankings = json.loads(row[7]) if row[7] else []
        except Exception:
            rankings = []
        format_val = row[8] if row[8] else ""
        anime_info[anime_id] = {
            "title_english": row[1],
            "title_romaji": row[2],
            "title_native": row[3],
            "average_score": row[4],
            "popularity": row[5],
            "genres": genres,
            "rankings": rankings,
            "format": format_val
        }
    return anime_info

def load_embeddings_cache(embeddings_file="embeddings_cache.pkl"):
    with open(embeddings_file, "rb") as f:
        return pickle.load(f)