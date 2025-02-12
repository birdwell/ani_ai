from google import genai
from pydantic import BaseModel
from typing import List
import json

# Define a Pydantic model for the expected JSON response.
class KeywordsResponse(BaseModel):
    keywords: List[str]

# Configure the Gemini API with your API key.
client = genai.Client(api_key="AIzaSyBaQ4nuea3UMJvJJdRTw97bFR3_-brs4hM")  # Replace with your actual API key.

def refine_query_with_gemini(query: str) -> List[str]:
    """
    Uses the Google Generative AI (Gemini) to extract relevant keywords from the user's query.
    Returns a list of keywords.
    """
    prompt = (
        "Extract three to five key genres or themes from the following anime recommendation query.\n"
        "Use this JSON schema exactly:\n"
        'KeywordsResponse = {"keywords": list[str]}\n'
        "Return your answer as a JSON object with no extra commentary.\n"
        f"Query: {query}"
    )

    response = client.models.generate_content(
        model="gemini-1.5-flash-8b",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": KeywordsResponse,
        },
    )

    # Debug: Print the raw response text.
    print("DEBUG: Response text:", response.text)

    # Attempt to use the parsed response from Gemini.
    parsed = response.parsed
    if parsed and hasattr(parsed, "keywords"):
        return parsed.keywords
    else:
        # Fallback: if parsed response isn't available, split the raw text by commas.
        fallback_keywords = [word.strip() for word in response.text.split(",") if word.strip()]
        return fallback_keywords

def rerank_candidates_with_gemini(query: str, candidates: List[dict]) -> List[int]:
    """
    Given the original query and a list of candidate dictionaries (each containing details),
    uses Gemini to re-rank the candidates.
    
    Each candidate dictionary should include keys: 'id', 'title', 'format',
    'average_score', and 'popularity'.
    
    Returns a list of candidate IDs in the new ranked order.
    """
    # Build a candidate details string. For each candidate, include relevant fields.
    candidate_lines = []
    for candidate in candidates:
        candidate_lines.append(
            f"ID: {candidate['id']}, Title: {candidate['title']}, Format: {candidate['format']}, "
            f"Average Score: {candidate['average_score']}, Popularity: {candidate['popularity']}"
        )
    candidate_str = "\n".join(candidate_lines)
    
    prompt = (
        "You are an expert anime recommender. Given the following candidate anime details and the user query, "
        "re-rank the candidates so that high-quality TV series (not TV shorts, OVAs, ONAs, or specials) are prioritized. "
        "Consider the following:\n"
        "- Format: Only TV shows should be highly ranked; penalize non-TV formats.\n"
        "- Quality: Higher average scores and popularity should boost the ranking.\n"
        "Return the new ranking as a JSON object with one key 'candidate_ids' mapping to an array of anime IDs in the desired order.\n\n"
        f"User Query: {query}\n\n"
        "Candidates:\n"
        f"{candidate_str}\n\n"
        "Return your answer as valid JSON."
    )
    
    response = genai.Client(api_key="AIzaSyBaQ4nuea3UMJvJJdRTw97bFR3_-brs4hM").models.generate_content(
        model="gemini-1.5-flash-8b", 
        contents=prompt,
        config={
            "response_mime_type": "application/json",
        }
    )
    
    # Debug: print raw response
    print("DEBUG: Gemini re-ranking response text:", response.text)
    
    try:
        parsed = json.loads(response.text)
        candidate_ids = parsed.get("candidate_ids", [])
        if candidate_ids and isinstance(candidate_ids, list):
            return candidate_ids
        else:
            # Fallback: if Gemini doesn't return candidate_ids, return original order.
            return [c["id"] for c in candidates]
    except Exception as e:
        print("DEBUG: Error parsing Gemini re-ranking response:", e)
        # Fallback: return original candidate IDs.
        return [c["id"] for c in candidates]

# Example usage:
if __name__ == "__main__":
    test_query = "I want a romance isekai anime"
    keywords = refine_query_with_gemini(test_query)
    print("Extracted Keywords:", keywords)