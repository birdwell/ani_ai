# main.py
from fastapi import FastAPI
from routers import query, recommendations, fuzzy_search

app = FastAPI(title="AniList Recommender API")

# Include the query endpoint router
app.include_router(query.router, prefix="/query", tags=["query"])

# Include the recommendations endpoint router
app.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])

# Include the fuzzy search endpoint router
app.include_router(fuzzy_search.router, prefix="/search", tags=["fuzzy_search"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)