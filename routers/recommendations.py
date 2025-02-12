# routers/recommendations.py
from fastapi import APIRouter, Query
from typing import Optional, List
from pydantic import BaseModel
from baseline_recommender import recommend_top_media, normalize_recommendations
from utils.titles import get_english_title
from utils.db import load_global_anime_info

router = APIRouter()

class Recommendation(BaseModel):
    id: int
    title: str
    confidence: float

@router.get("/", response_model=List[Recommendation])
def recommendations_endpoint(
    desired_genre: Optional[str] = Query(None, description="Filter recommendations by a desired genre"),
    top_n: int = Query(10, description="Number of recommendations to return")
):
    # Use your baseline recommendation logic.
    raw_recommendations = recommend_top_media(top_n=top_n, desired_genre=desired_genre)
    normalized_recs = normalize_recommendations(raw_recommendations)
    
    # Load global anime metadata to get titles.
    global_anime_info = load_global_anime_info()
    
    response_list = []
    for media, confidence in normalized_recs:
        info = global_anime_info.get(media["id"], {})
        title = get_english_title(info)
        response_list.append(Recommendation(id=media["id"], title=title, confidence=confidence))
    
    return response_list