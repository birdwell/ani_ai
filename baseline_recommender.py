import sqlite3
import json

def get_user_preferences(personal_db_path="anilist_data.db"):
    """
    Extracts user preferences by reading completed shows (with ratings) from the personal database.
    Builds a weighted dictionary based on genres and tags.
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
        try:
            genres = json.loads(genres_json) if genres_json else []
        except Exception:
            genres = []
        try:
            tags = json.loads(tags_json) if tags_json else []
        except Exception:
            tags = []
        # Use the score as a weight for the genres and tags
        for genre in genres:
            preference[genre] = preference.get(genre, 0) + score
        for tag in tags:
            preference[tag] = preference.get(tag, 0) + score
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
    # print("Planned IDs:", planned_ids)  # Debug print
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
    Computes a simple similarity score between a media item and the user's preferences.
    The score is the sum of weights for matching genres and tags.
    """
    score = 0
    for genre in media["genres"]:
        if genre in preference:
            score += preference[genre]
    for tag in media["tags"]:
        if tag in preference:
            score += preference[tag]
    return score

def recommend_top_media(top_n=10, desired_genre=None):
    """
    Computes and returns the top N recommendations based on similarity scores.
    If a desired_genre is provided, media items that contain that genre (or tag) are boosted.
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
        sim = compute_similarity(media, preference)
        
        if desired_genre:
            # Boost the score if the desired genre is present (case-insensitive)
            genres_lower = [g.lower() for g in media["genres"]]
            tags_lower = [t.lower() for t in media["tags"]]
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