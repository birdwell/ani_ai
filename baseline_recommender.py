import sqlite3
import json

import sqlite3
import json

def transform_rating(score):
    if score < 7:
        return 0
    return score - 6  # Mapping: 7->1, 8->2, 9->3, 10->4

def get_user_preferences(personal_db_path="anilist_data.db"):
    """
    Extracts user preferences by reading completed shows (with ratings) from the personal database.
    Builds a weighted dictionary based on genres and tags, with ratings transformed to emphasize good shows.
    """
    conn = sqlite3.connect(personal_db_path)
    cursor = conn.cursor()
    query = """
        SELECT m.genres, m.tags, mle.score
        FROM media m
        JOIN media_list_entries mle ON m.id = mle.media_id
        WHERE mle.status = 'COMPLETED' AND mle.score IS NOT NULL
    """
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    
    preference = {}
    for genres_json, tags_json, score in results:
        weight = transform_rating(score)
        try:
            genres = json.loads(genres_json) if genres_json else []
        except Exception:
            genres = []
        try:
            tags = json.loads(tags_json) if tags_json else []
        except Exception:
            tags = []
        # Use the transformed weight
        for genre in genres:
            preference[genre] = preference.get(genre, 0) + weight
        for tag in tags:
            if isinstance(tag, dict):
                tag_name = tag.get("name", "")
            else:
                tag_name = tag
            preference[tag_name] = preference.get(tag_name, 0) + weight
    return preference

def get_global_media(global_db_path="anilist_global.db"):
    """
    Reads the global media data from the global database and returns a list of media items.
    """
    conn = sqlite3.connect(global_db_path)
    cursor = conn.cursor()
    query = """
        SELECT id, title_romaji, title_english, title_native, genres, tags
        FROM global_media
    """
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    
    media_list = []
    for row in results:
        media = {
            "id": row[0],
            "title_romaji": row[1],
            "title_english": row[2],
            "title_native": row[3],
            "genres": json.loads(row[4]) if row[4] else [],
            "tags": json.loads(row[5]) if row[5] else []
        }
        media_list.append(media)
    return media_list

def get_user_planned_media_ids(personal_db_path="anilist_data.db"):
    """
    Retrieves the set of media IDs that are in the user's 'PLANNING' list.
    """
    conn = sqlite3.connect(personal_db_path)
    cursor = conn.cursor()
    query = "SELECT DISTINCT media_id FROM media_list_entries WHERE status = 'PLANNING'"
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    planned_ids = {row[0] for row in results}
    return planned_ids

def get_user_watched_media_ids(personal_db_path="anilist_data.db"):
    """
    Retrieves the set of media IDs for shows that the user has in any list other than 'PLANNING'.
    These are considered as already watched or otherwise engaged.
    """
    conn = sqlite3.connect(personal_db_path)
    cursor = conn.cursor()
    query = "SELECT DISTINCT media_id FROM media_list_entries WHERE status != 'PLANNING'"
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    watched_ids = {row[0] for row in results}
    return watched_ids

def compute_similarity(media, preference):
    """
    Computes a similarity score between a media item and the user's preferences.
    Incorporates:
      - Matching genres (weighted by the accumulated user score)
      - Matching tags weighted by the tag's rank (importance)
      - A fraction of the average score
      - A normalized boost from popularity
    """
    score = 0.0

    # Base score from matching genres.
    for genre in media.get("genres", []):
        if genre in preference:
            score += preference[genre]
    
    # Process each tag, handling both dictionary and string representations.
    for tag in media.get("tags", []):
        if isinstance(tag, dict):
            tag_name = tag.get("name", "")
            tag_rank = tag.get("rank", 1)  # Default to 1 if no rank is provided.
        else:
            tag_name = tag
            tag_rank = 1
        if tag_name in preference:
            # Now, give a boost based on tag rank:
            # For example, a tag with rank 100 contributes 2x its base weight.
            score += preference[tag_name] * (1 + tag_rank / 100.0)
    
    # Incorporate average score (e.g., add a fraction of the average score).
    average_score = media.get("average_score") or 0
    score += average_score * 0.1  # Adjust multiplier as needed.

    # Incorporate popularity as a normalized boost.
    popularity = media.get("popularity") or 0
    score += popularity / 1000000.0  # Adjust as needed.

    return score

def recommend_top_media(top_n=10, desired_genre=None):
    """
    Computes and returns the top N recommendations based on similarity scores.
    If a desired_genre is provided, only media items that actually include that genre (or tag)
    are considered, and their similarity score is boosted.
    Additionally, if a media item is in the user's planned list, its score is boosted.
    """
    preference = get_user_preferences()
    global_media = get_global_media()
    planned_ids = get_user_planned_media_ids()
    watched_ids = get_user_watched_media_ids()
    
    recommendations = []
    for media in global_media:
        # Skip media that the user has already engaged with (excluding planned)
        if media["id"] in watched_ids:
            continue

        # If a desired genre is provided, filter out media that don't include it
        if desired_genre:
            genres_lower = [g.lower() for g in media["genres"]]
            tags_lower = [tag.get("name", "").lower() if isinstance(tag, dict) else tag.lower() for tag in media["tags"]]
            if desired_genre.lower() not in genres_lower and desired_genre.lower() not in tags_lower:
                continue

        sim = compute_similarity(media, preference)
        
        # If a desired genre is provided and found, apply a boost
        if desired_genre:
            genres_lower = [g.lower() for g in media["genres"]]
            tags_lower = [tag.get("name", "").lower() if isinstance(tag, dict) else tag.lower() for tag in media["tags"]]
            if desired_genre.lower() in genres_lower:
                sim *= 1.2  # boost factor for genres
            elif desired_genre.lower() in tags_lower:
                sim *= 1.1  # slightly smaller boost for tags
        
        # If the media is in the planned list, boost it further
        if media["id"] in planned_ids:
            sim *= 1.5  # additional boost for planned shows
        
        recommendations.append((media, sim))
    
    recommendations.sort(key=lambda x: x[1], reverse=True)
    return recommendations[:top_n]

def normalize_recommendations(recommendations):
    """
    Normalizes the raw similarity scores so that the highest score is mapped to 100%.
    """
    if not recommendations:
        return []
    
    max_score = max(score for _, score in recommendations)
    normalized = []
    for media, score in recommendations:
        confidence = (score / max_score) * 100  # Scale to percentage
        normalized.append((media, confidence))
    return normalized

def main():
    desired_genre = input("Enter a genre filter (or press enter to skip): ").strip()
    if desired_genre == "":
        desired_genre = None
    recommendations = recommend_top_media(top_n=10, desired_genre=desired_genre)
    print("Top Recommendations:")
    for media, score in recommendations:
        # Choose a title preference order: English > Romaji > Native
        title = media.get("title_english") or media.get("title_romaji") or media.get("title_native")
        print(f"{title} (Similarity Score: {score:.2f})")

if __name__ == '__main__':
    main()