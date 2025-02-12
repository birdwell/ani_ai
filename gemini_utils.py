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

# Example usage:
if __name__ == "__main__":
    test_query = "I want a romance isekai anime"
    keywords = refine_query_with_gemini(test_query)
    print("Extracted Keywords:", keywords)