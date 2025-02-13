import os
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
from dotenv import load_dotenv
import requests
import sqlite3
import json
import webbrowser
from requests_oauthlib import OAuth2Session

# Load environment variables
load_dotenv()

# --------------------------
# Configuration / Constants
# --------------------------

# Replace these with your actual AniList application credentials.
CLIENT_ID = os.environ.get('ANILIST_CLIENT_ID')
CLIENT_SECRET = os.environ.get('ANILIST_CLIENT_SECRET')
REDIRECT_URI = os.environ.get('ANILIST_REDIRECT_URI')

if not all([CLIENT_ID, CLIENT_SECRET, REDIRECT_URI]):
    raise ValueError("Missing AniList credentials. Please check your .env file.")

# AniList OAuth2 endpoints
AUTHORIZATION_BASE_URL = 'https://anilist.co/api/v2/oauth/authorize'
TOKEN_URL = 'https://anilist.co/api/v2/oauth/token'

# AniList GraphQL API endpoint
ANILIST_API_URL = "https://graphql.anilist.co"

# GraphQL query to fetch the user's anime lists and details about each media item.
GRAPHQL_QUERY = '''
query ($username: String) {
  MediaListCollection(userName: $username, type: ANIME) {
    lists {
      name
      entries {
        status
        score
        progress
        repeat
        media {
          id
          title {
            romaji
            english
            native
          }
          episodes
          genres
          tags {
            name
          }
          description(asHtml: false)
        }
      }
    }
  }
}
'''

# --------------------------
# OAuth2 Flow
# --------------------------

def oauth2_authenticate():
    """
    Perform the OAuth2 authentication with AniList.
    This function will:
      1. Create an OAuth2Session.
      2. Generate an authorization URL.
      3. Open the URL in the default browser.
      4. Prompt the user for the full redirect URL.
      5. Exchange the code for an access token.
    Returns:
        A token dictionary containing the access token.
    """
    anilist_session = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI)
    authorization_url, state = anilist_session.authorization_url(AUTHORIZATION_BASE_URL)

    print("Please go to the following URL and authorize access:")
    print(authorization_url)
    webbrowser.open(authorization_url)

    # After the user authorizes, AniList will redirect to your redirect URI.
    # The user should copy the full redirect URL (which contains a code) and paste it here.
    redirect_response = input("Paste the full redirect URL here: ")

    # Exchange the authorization code for an access token.
    token = anilist_session.fetch_token(
        TOKEN_URL,
        client_secret=CLIENT_SECRET,
        authorization_response=redirect_response
    )
    return token

# --------------------------
# AniList Data Fetching
# --------------------------

def fetch_anilist_data(token, username):
    """
    Fetches AniList data for the given username using the GraphQL API and OAuth2 token.
    
    Args:
        token (dict): The OAuth2 token containing the access token.
        username (str): The AniList username.
        
    Returns:
        dict: The JSON response from AniList.
    """
    variables = {
        "username": username
    }
    headers = {
        'Authorization': f'Bearer {token["access_token"]}',
        'Content-Type': 'application/json',
    }
    response = requests.post(
        ANILIST_API_URL,
        json={'query': GRAPHQL_QUERY, 'variables': variables},
        headers=headers
    )
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed with status code {response.status_code}: {response.text}")

# --------------------------
# Database Setup and Storage
# --------------------------

def init_db(db_path="anilist_data.db"):
    """
    Initializes the SQLite database and creates the necessary tables if they do not exist.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Table to store unique media (anime) information
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY,
            title_romaji TEXT,
            title_english TEXT,
            title_native TEXT,
            episodes INTEGER,
            description TEXT,
            genres TEXT,
            tags TEXT
        )
    ''')
    
    # Table to store user-specific list entries (which list the media belongs to, status, score, etc.)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS media_list_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_id INTEGER,
            list_name TEXT,
            status TEXT,
            score REAL,
            progress INTEGER,
            repeat INTEGER,
            FOREIGN KEY (media_id) REFERENCES media (id)
        )
    ''')
    
    conn.commit()
    return conn

def store_data_to_db(data, conn):
    """
    Parses the fetched AniList JSON data and stores it in the SQLite database.
    """
    cursor = conn.cursor()
    lists = data.get('data', {}).get('MediaListCollection', {}).get('lists', [])
    
    for list_item in lists:
        list_name = list_item.get('name', 'Unknown')
        entries = list_item.get('entries', [])
        
        for entry in entries:
            media = entry.get('media', {})
            media_id = media.get('id')
            
            # Check if this media entry is already in the database
            cursor.execute('SELECT id FROM media WHERE id=?', (media_id,))
            if not cursor.fetchone():
                title = media.get('title', {})
                title_romaji = title.get('romaji')
                title_english = title.get('english')
                title_native = title.get('native')
                episodes = media.get('episodes')
                description = media.get('description')
                genres = media.get('genres', [])
                
                # Extract tag names
                tags_list = media.get('tags', [])
                tags = [tag.get('name') for tag in tags_list if tag.get('name')]
                
                # Store genres and tags as JSON strings so they can be easily retrieved later.
                genres_json = json.dumps(genres)
                tags_json = json.dumps(tags)
                
                cursor.execute('''
                    INSERT INTO media (id, title_romaji, title_english, title_native, episodes, description, genres, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (media_id, title_romaji, title_english, title_native, episodes, description, genres_json, tags_json))
            
            # Insert the list entry for the media item.
            status = entry.get('status')
            score = entry.get('score')
            progress = entry.get('progress')
            repeat = entry.get('repeat')
            cursor.execute('''
                INSERT INTO media_list_entries (media_id, list_name, status, score, progress, repeat)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (media_id, list_name, status, score, progress, repeat))
    
    conn.commit()

# --------------------------
# Main Execution Flow
# --------------------------

def main():
    try:
        print("Starting OAuth2 authentication with AniList...")
        token = oauth2_authenticate()
        print("OAuth2 authentication successful.\n")
        
        # Prompt for the AniList username (you may also extract this from the token if desired)
        username = input("Enter your AniList username: ")
        
        print("Fetching data from AniList...")
        data = fetch_anilist_data(token, username)
        print("Data fetched successfully.\n")
        
        print("Initializing database...")
        conn = init_db()
        print("Storing data into the database...")
        store_data_to_db(data, conn)
        print("Data stored successfully in 'anilist_data.db'")
        conn.close()
    except Exception as e:
        print("An error occurred:", e)

if __name__ == '__main__':
    main()