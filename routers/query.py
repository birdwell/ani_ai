# routers/query.py
from fastapi import APIRouter, Query
from typing import Optional, List
from pydantic import BaseModel
import numpy as np
from sentence_transformers import SentenceTransformer
from utils.db import load_global_anime_info, load_embeddings_cache
from utils.quality import compute_quality_score
from utils.titles import get_english_title
from gemini_utils import refine_query_with_gemini

router = APIRouter()

class Recommendation(BaseModel):
    id: int
    title: str
    confidence: float

def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

# Load global metadata and embeddings
global_anime_info = load_global_anime_info()
embeddings_cache = load_embeddings_cache()

# Use the same model used to generate embeddings.
model = SentenceTransformer("all-mpnet-base-v2")

@router.get("/", response_model=List[Recommendation])
def query_recommendations(
    q: str = Query(..., description="Your natural language query for anime recommendations"),
    top_n: int = Query(10, description="Number of recommendations to return")
):
    # Extract keywords via Gemini.
    extracted_keywords = refine_query_with_gemini(q)
    print(f"Extracted keywords from Gemini: {extracted_keywords}")
    
    # Remove generic keywords.
    generic_keywords = {"anime", "manga", "series", "show"}
    refined_keywords = [kw for kw in extracted_keywords if kw.lower() not in generic_keywords]
    print(f"DEBUG: Refined keywords after filtering generic terms: {refined_keywords}")
    
    query_embedding = model.encode(q, convert_to_numpy=True)
    
    semantic_results = []
    for anime_id, embedding in embeddings_cache.items():
        sim = cosine_similarity(query_embedding, embedding)
        semantic_results.append((anime_id, sim))
    
    semantic_results.sort(key=lambda x: x[1], reverse=True)
    candidate_pool = semantic_results[:top_n * 5]
    
    if refined_keywords:
        filtered_pool = []
        for anime_id, sim in candidate_pool:
            info = global_anime_info.get(anime_id, {})
            genres = info.get("genres", [])
            genres_lower = [g.lower() for g in genres]
            if any(keyword.lower() in genres_lower for keyword in refined_keywords):
                filtered_pool.append((anime_id, sim))
        if filtered_pool:
            candidate_pool = filtered_pool
    
    combined_results = []
    for anime_id, sim in candidate_pool:
        info = global_anime_info.get(anime_id, {})
        quality = compute_quality_score(info)
        final_score = sim * (1 + quality)
        combined_results.append((anime_id, final_score))
    
    combined_results.sort(key=lambda x: x[1], reverse=True)
    final_results = combined_results[:top_n]
    
    response_list = []
    for anime_id, final in final_results:
        info = global_anime_info.get(anime_id, {})
        title = get_english_title(info)
        confidence = final * 100
        response_list.append(Recommendation(id=anime_id, title=title, confidence=confidence))
    return response_list