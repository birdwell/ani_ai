# Ani_AI

Ani_AI is a personalized anime recommendation engine powered by your AniList data. It analyzes your watching history and preferences to generate tailored anime recommendations, leveraging both your personal lists and the global AniList database.

## Core Components

- `baseline_recommender.py`: Core recommendation engine that analyzes your anime history and generates personalized scores
- `api.py`: FastAPI-based REST API server for accessing recommendations
- `global_ingest.py`: Data ingestion script that maintains a local cache of AniList data

## Features

- **Smart Preference Analysis**: Builds your taste profile based on your completed and rated anime
- **Personalized Scoring**: Ranks anime based on your unique preferences in genres, tags, and themes
- **Planning List Integration**: Automatically prioritizes shows from your Planning list
- **Genre-Based Filtering**: Filter recommendations by specific genres
- **Fast API Access**: Get recommendations quickly through a modern REST API
- **Local Data Caching**: Maintains an efficient local database to avoid API rate limits

## Prerequisites

- Python 3.7+
- Git
- AniList account (for accessing your anime list data)

## Quick Start

1. **Clone and Setup**
```bash
# Clone the repository
git clone https://github.com/yourusername/ani_ai.git
cd ani_ai

# Create and activate virtual environment
python -m venv venv
# For Unix/macOS:
source venv/bin/activate
# For Windows:
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

2. **Run the Recommender**
```bash
# CLI Mode
python baseline_recommender.py

# API Server Mode
uvicorn api:app --reload
```

The API documentation will be available at http://localhost:8000/docs

## Project Structure

- `baseline_recommender.py`: Core recommendation algorithm and CLI interface
- `api.py`: FastAPI server implementation with recommendation endpoints
- `global_ingest.py`: AniList data ingestion and caching system
- `requirements.txt`: Project dependencies
- `anilist_global.db`: Local SQLite cache of AniList data (created on first run)

## API Usage Example

```python
import requests

# Get recommendations
response = requests.get('http://localhost:8000/recommendations')
recommendations = response.json()

# Get recommendations filtered by genre
response = requests.get('http://localhost:8000/recommendations?genre=Action')
action_recommendations = response.json()
```

## Data Updates

The system automatically maintains a local cache of AniList data to ensure fast recommendation generation and avoid API rate limits. The cache is updated periodically when running the recommender or API server.
