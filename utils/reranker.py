# utils/reranker.py
from google import genai
import json

# Configure Gemini API with your API key.
client = genai.Client(api_key="AIzaSyBaQ4nuea3UMJvJJdRTw97bFR3_-brs4hM")  # Replace with your actual API key.

def rerank_candidates_with_gemini(query: str, candidates: list) -> list:
    """
    Given the user query and a list of candidate dictionaries (each containing details such as:
    'id', 'title', 'format', 'average_score', and 'popularity'),
    use Gemini to re-rank the candidates.
    Returns a list of candidate IDs (as integers) in the new ranked order.
    """
    candidate_lines = []
    for candidate in candidates:
        candidate_lines.append(
            f"ID: {candidate['id']}, Title: {candidate['title']}, Format: {candidate['format']}, "
            f"Score: {candidate['average_score']}, Popularity: {candidate['popularity']}"
        )
    candidates_text = "\n".join(candidate_lines)
    
    prompt = (
        "You are an expert anime recommender. Given the following candidate anime details and the user query, "
        "please re-rank the candidates so that high-quality TV series (with high average scores and popularity) "
        "are prioritized, while penalizing formats like TV_SHORT, OVA, ONA, or SPECIAL.\n\n"
        f"User Query: {query}\n\n"
        "Candidates:\n"
        f"{candidates_text}\n\n"
        "Return your answer as valid JSON with a single key 'candidate_ids' mapping to an array of anime IDs in the desired order."
    )
    
    response = client.models.generate_content(
        model="gemini-1.5-flash-8b",
        contents=prompt,
        config={"response_mime_type": "application/json"}
    )
    
    # Debug: print raw response.
    print("DEBUG: Gemini re-ranking response text:", response.text)
    
    try:
        parsed = json.loads(response.text)
        candidate_ids = parsed.get("candidate_ids", [])
        return [int(cid) for cid in candidate_ids]
    except Exception as e:
        print("DEBUG: Error parsing Gemini re-ranking response:", e)
        # Fallback: return candidate IDs in original order.
        return [c["id"] for c in candidates]