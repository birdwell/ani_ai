# routers/query.py
from fastapi import APIRouter, Query
from typing import Optional, List
from pydantic import BaseModel
import numpy as np
from sentence_transformers import SentenceTransformer

from utils.db import load_global_anime_info, load_embeddings_cache
from utils.retrieval import retrieve_similar_anime
from utils.reranker import rerank_candidates_with_gemini
from utils.quality import compute_quality_score
from utils.titles import get_english_title

router = APIRouter()

class Recommendation(BaseModel):
    id: int
    title: str
    confidence: float

# Load global metadata and embeddings once.
global_anime_info = load_global_anime_info()
embeddings_cache = load_embeddings_cache()

# Use the same model that was used to generate the FAISS index.
model = SentenceTransformer("all-mpnet-base-v2")

def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

@router.get("/", response_model=List[Recommendation])
def query_recommendations(
    q: str = Query(..., description="Your natural language query for anime recommendations"),
    top_n: int = Query(10, description="Number of recommendations to return")
):
    # (1) Retrieve candidate anime IDs from FAISS.
    candidate_ids = retrieve_similar_anime(q, top_k=top_n * 5)
    print("DEBUG: Candidate IDs from FAISS:", candidate_ids)
    
    # (2) Build candidate details from global metadata.
    candidates = []
    for cid in candidate_ids:
        info = global_anime_info.get(cid, {})
        candidates.append({
            "id": cid,
            "title": get_english_title(info),
            "format": info.get("format", ""),
            "average_score": info.get("average_score", 0),
            "popularity": info.get("popularity", 0)
        })
    
    # (3) Use Gemini to re-rank these candidates.
    reranked_ids = rerank_candidates_with_gemini(q, candidates)
    print("DEBUG: Reranked candidate IDs from Gemini:", reranked_ids)
    
    # (4) Re-order candidates based on Gemini’s re-ranking.
    id_to_candidate = {c["id"]: c for c in candidates}
    reranked_candidates = [id_to_candidate[cid] for cid in reranked_ids if cid in id_to_candidate]
    if not reranked_candidates:
        reranked_candidates = candidates  # Fallback
    
    # (5) Optionally, adjust scores based on quality if needed.
    # For example, you could re-compute a final score:
    final_candidates = sorted(
        reranked_candidates,
        key=lambda c: compute_quality_score(global_anime_info.get(c["id"], {})),
        reverse=True
    )[:top_n]
    
    # (6) Build and return the response.
    response_list = []
    for candidate in final_candidates:
        confidence = compute_quality_score(global_anime_info.get(candidate["id"], {})) * 100
        response_list.append(Recommendation(id=candidate["id"], title=candidate["title"], confidence=confidence))
    
    return response_list