# utils/titles.py

def get_english_title(info: dict) -> str:
    if info.get("title_english") and info.get("title_english").strip():
        return info.get("title_english").strip()
    elif info.get("title_romaji") and info.get("title_romaji").strip():
        return info.get("title_romaji").strip()
    elif info.get("title_native") and info.get("title_native").strip():
        return info.get("title_native").strip()
    else:
        return "Unknown Title"