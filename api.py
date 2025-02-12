from fastapi import FastAPI, Query
from typing import Optional, List
from pydantic import BaseModel
import uvicorn
from baseline_recommender import recommend_top_media, normalize_recommendations

class Recommendation(BaseModel):
    id: int
    title: str
    confidence: float

app = FastAPI(title="AniList Recommender API")

@app.get("/recommendations", response_model=List[Recommendation])
def get_recommendations(
    desired_genre: Optional[str] = Query(None, description="Filter recommendations by a desired genre"),
    top_n: int = Query(10, description="Number of recommendations to return")
):
    raw_recommendations = recommend_top_media(top_n=top_n, desired_genre=desired_genre)
    normalized_recs = normalize_recommendations(raw_recommendations)
    response = []
    for media, confidence in normalized_recs:
        title = media.get("title_english") or media.get("title_romaji") or media.get("title_native")
        response.append(Recommendation(id=media["id"], title=title, confidence=confidence))
    return response

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)