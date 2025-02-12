# routers/query.py
from fastapi import APIRouter, Query
from typing import Optional, List
from pydantic import BaseModel
import numpy as np
from sentence_transformers import SentenceTransformer
from utils.db import load_global_anime_info, load_embeddings_cache
from utils.quality import compute_quality_score
from utils.titles import get_english_title
from gemini_utils import refine_query_with_gemini, rerank_candidates_with_gemini

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
    # (1) Compute the query embedding.
    query_embedding = model.encode(q, convert_to_numpy=True)
    
    # (2) Compute cosine similarity for each anime in the embeddings cache.
    semantic_results = []
    for anime_id, embedding in embeddings_cache.items():
        sim = cosine_similarity(query_embedding, embedding)
        semantic_results.append((anime_id, sim))
    semantic_results.sort(key=lambda x: x[1], reverse=True)
    
    # (3) Build a candidate pool from the top (top_n * 5) results.
    candidate_pool = semantic_results[:top_n * 5]
    candidates = []
    for anime_id, sim in candidate_pool:
        info = global_anime_info.get(anime_id, {})
        candidates.append({
            "id": anime_id,  # we expect these to be ints
            "title": get_english_title(info),
            "format": info.get("format", ""),
            "average_score": info.get("average_score", 0),
            "popularity": info.get("popularity", 0),
            "sim": sim  # keep the semantic similarity for reference
        })
    
    # Debug: Print candidate IDs from our pool.
    candidate_ids_pool = [c["id"] for c in candidates]
    print("DEBUG: Candidate IDs from pool:", candidate_ids_pool)
    
    # (4) Use Gemini to re-rank these candidates.
    reranked_ids = rerank_candidates_with_gemini(q, candidates)
    print("DEBUG: Reranked IDs from Gemini:", reranked_ids)
    
    # (5) Re-order candidates based on reranked_ids.
    # Ensure we compare integers: convert Gemini's IDs to int if needed.
    id_to_candidate = {c["id"]: c for c in candidates}
    reranked_candidates = []
    for cid in reranked_ids:
        try:
            cid_int = int(cid)
        except Exception:
            continue
        if cid_int in id_to_candidate:
            reranked_candidates.append(id_to_candidate[cid_int])
    print("DEBUG: Reranked candidates after matching:", reranked_candidates)
    
    # (6) If re-ranking produced no matches, fall back to the original candidate pool.
    if not reranked_candidates:
        print("DEBUG: No matching candidates from Gemini re-ranking; falling back to original candidate pool.")
        reranked_candidates = candidates
    
    # (7) Take the top_n candidates from the re-ranked list.
    final_candidates = reranked_candidates[:top_n]
    
    # (8) Build the final response.
    response_list = []
    for candidate in final_candidates:
        confidence = candidate.get("sim", 0) * 100  # Optionally use the original semantic similarity.
        response_list.append(Recommendation(id=candidate["id"], title=candidate["title"], confidence=confidence))
    
    return response_list