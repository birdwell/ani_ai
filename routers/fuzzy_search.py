from fastapi import APIRouter, HTTPException, Query
import sqlite3
from rapidfuzz import process, fuzz, utils
from functools import lru_cache

router = APIRouter()

@lru_cache(maxsize=1)
def get_all_titles() -> list:
    """
    Load all anime titles from the global database and cache them.
    Each entry is a tuple: (anime_id, title), where title is chosen as:
      title_english > title_romaji > title_native.
    """
    try:
        conn = sqlite3.connect("anilist_global.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title_romaji, title_english, title_native
            FROM global_media
        """)
        rows = cursor.fetchall()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    titles = []
    for row in rows:
        title = row["title_english"] or row["title_romaji"] or row["title_native"]
        if title:
            titles.append((row["id"], title))
    return titles

@router.get("/fuzzy",
    summary="Fuzzy search anime titles",
    description="Search for anime titles using fuzzy string matching. Returns top N matches sorted by similarity score.",
    response_description="List of matched anime titles with their similarity scores")
def fuzzy(
    q: str = Query(..., description="Query string to fuzzy-match against titles", min_length=1),
    limit: int = Query(10, description="Number of results to return"),
    min_score: float = Query(45, description="Minimum fuzzy score threshold")
):
    # Retrieve cached titles: list of (id, title)
    candidates = get_all_titles()
    if not candidates:
        return {"results": []}
    
    # Extract just the titles into a list for fuzzy matching.
    title_texts = [title for (_, title) in candidates]
    
    try:
        # Use RapidFuzz's process.extract with a scorer.
        matches = process.extract(
            q,
            title_texts,
            scorer=fuzz.token_set_ratio,  # Try fuzz.WRatio if needed for better accuracy.
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    results = []
    for matched_title, score, idx in matches:
        if score < min_score:
            continue
        anime_id, _ = candidates[idx]
        results.append({
            "id": anime_id,
            "title": matched_title,
            "fuzzy_score": score
        })
    
    return {"results": results}