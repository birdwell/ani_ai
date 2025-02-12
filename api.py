from fastapi import FastAPI, Query
from typing import Optional, List
from pydantic import BaseModel
import uvicorn

# Import the recommendation function from your recommender module.
# If both files are in the same directory, you can use:
from baseline_recommender import recommend_top_media

# Define a response model for clarity.
class Recommendation(BaseModel):
    id: int
    title: str
    similarity_score: float

app = FastAPI(title="AniList Recommender API")

@app.get("/recommendations", response_model=List[Recommendation])
def get_recommendations(
    desired_genre: Optional[str] = Query(None, description="Filter recommendations by a desired genre"),
    top_n: int = Query(10, description="Number of recommendations to return")
):
    recommendations = recommend_top_media(top_n=top_n, desired_genre=desired_genre)
    response = []
    for media, score in recommendations:
        title = media.get("title_english") or media.get("title_romaji") or media.get("title_native")
        response.append(Recommendation(id=media["id"], title=title, similarity_score=score))
    return response

if __name__ == "__main__":
    # Run the API with uvicorn on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)