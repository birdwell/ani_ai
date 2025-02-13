# Ani_AI

Ani_AI is a sophisticated anime recommendation engine powered by your AniList data. It combines traditional content-based filtering with advanced AI features to deliver highly personalized anime recommendations. The system analyzes your watching history, preferences, and natural language queries to suggest anime that truly match your interests.

## Core Features

- **Smart Preference Analysis**: Builds your taste profile based on your completed and rated anime
- **AI-Powered Search**: Uses Gemini AI for natural language understanding and semantic search
- **Embedding-Based Recommendations**: Leverages sentence transformers for deep content understanding
- **Multi-Language Support**: Handles queries and content in multiple languages
- **Quality-Aware Scoring**: Considers popularity, ratings, and community feedback
- **Planning List Integration**: Automatically prioritizes shows from your Planning list
- **Fast API Access**: Get recommendations quickly through a modern REST API

## Prerequisites

- Python 3.7+
- Git
- AniList account
- Google Cloud API key (for Gemini AI features)

## Dependency Management

This project uses `pip-tools` for dependency management. Here's how to work with dependencies:

1. **Install pip-tools**
```bash
pip install pip-tools
```

2. **Add New Dependencies**
- Add new packages to `requirements.in`
- Run `pip-compile` to generate `requirements.txt`:
```bash
pip-compile requirements.in
```

3. **Install Dependencies**
```bash
pip-sync requirements.txt
```

4. **Update Dependencies**
```bash
# Update all dependencies to their latest versions
pip-compile --upgrade requirements.in

# Update specific packages
pip-compile --upgrade-package package_name requirements.in
```

> Note: Always use `pip-sync` instead of `pip install -r requirements.txt` to ensure your environment exactly matches the requirements.

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

2. **Configure Environment**
- Set up your Google Cloud API key for Gemini AI features
- Ensure your AniList account is properly configured

## Environment Setup

1. **API Keys and Secrets**
```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your actual API keys
nano .env
```

Required environment variables:
- `GEMINI_API_KEY`: Your Google Gemini AI key
- `ANILIST_CLIENT_ID`: Your AniList application client ID
- `ANILIST_CLIENT_SECRET`: Your AniList application client secret
- `ANILIST_REDIRECT_URI`: Your Anilist application redirect URI

3. **Run the System**
```bash
# Generate embeddings (first time setup)
python generate_embeddings.py

# Run the baseline recommender (CLI)
python baseline_recommender.py

# Start the API server
uvicorn main:app --reload
```

The API documentation will be available at http://localhost:8000/docs

## Project Structure

### Core Components
- `main.py`: FastAPI application entry point
- `baseline_recommender.py`: Traditional content-based recommendation engine
- `generate_embeddings.py`: Creates and caches anime embeddings
- `gemini_utils.py`: Gemini AI integration utilities

### Routers
- `routers/`
  - `recommendations.py`: Recommendation endpoints
  - `query.py`: Natural language query processing

### Utils
- `utils/`
  - `db.py`: Database operations and management
  - `quality.py`: Anime quality scoring utilities
  - `titles.py`: Title processing and normalization

### Data Management
- `ingest/`: Data ingestion and format management
- `migrate_db.py`: Database schema migration utilities

## API Usage Examples

```python
import requests

# Get basic recommendations
response = requests.get('http://localhost:8000/recommendations')
recommendations = response.json()

# Natural language query
response = requests.get(
    'http://localhost:8000/query',
    params={'q': 'Show me some psychological thrillers like Death Note'}
)
recommendations = response.json()

# Get recommendations with specific genre
response = requests.get(
    'http://localhost:8000/recommendations',
    params={'genre': 'Action'}
)
action_recommendations = response.json()
```

## Data Management

The system uses several data stores:
- `anilist_global.db`: Global anime database cache
- `anilist_data.db`: Personal anime list data
- `embeddings_cache.pkl`: Cached anime embeddings for fast similarity search

Data is automatically maintained and updated to ensure fresh recommendations while respecting API rate limits.
