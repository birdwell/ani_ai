# utils/quality.py

def compute_quality_score(info: dict) -> float:
    """
    Computes a quality score from the anime's metadata.
    
    - Normalizes average_score (0 to 1) and popularity (assumes 1,000,000 as high).
    - Gives higher weight to average_score and popularity by multiplying them by 4 and 3 respectively.
    - For TV shows, applies a multiplier of 1.5 and adds a ranking bonus based on TV rankings.
    - For MOVIE, uses a multiplier of 1.0.
    - For other formats (OVA, ONA, SPECIAL), uses a multiplier of 0.5.
    - For TV_SHORT, uses a multiplier of 0.1.
    
    Ranking bonus for TV: bonus = max(0, (100 - rank) / 100)
    """
    # Get the average score (assumed to be out of 100) and popularity.
    avg = info.get("average_score") or 0
    pop = info.get("popularity") or 0
    
    # Normalize values.
    normalized_avg = avg / 100.0            # Range: 0 to 1.
    normalized_pop = pop / 1_000_000.0      # Assuming 1,000,000 is a high popularity.
    
    # Increase weights: for example, multiply average score by 4 and popularity by 3.
    base_quality = (normalized_avg * 4) + (normalized_pop * 3)
    
    fmt = info.get("format", "").upper()
    
    if fmt == "TV":
        quality_multiplier = 1.5  # TV shows get a boost.
        bonus = 0.0
        rankings = info.get("rankings")
        if rankings and isinstance(rankings, list):
            for r in rankings:
                if r.get("type", "").upper() == "TV":
                    rank_value = r.get("rank")
                    if rank_value and isinstance(rank_value, int) and rank_value > 0:
                        bonus = max(bonus, (100 - rank_value) / 100.0)
        return base_quality * quality_multiplier + bonus

    elif fmt == "MOVIE":
        quality_multiplier = 1.0  # Movies use baseline quality.
        return base_quality * quality_multiplier

    elif fmt in {"OVA", "ONA", "SPECIAL"}:
        quality_multiplier = 0.5  # Penalize these formats moderately.
        return base_quality * quality_multiplier

    elif fmt == "TV_SHORT":
        quality_multiplier = 0.1  # Heavily penalize TV shorts.
        return base_quality * quality_multiplier

    else:
        # If format is unknown, simply return the base quality.
        return base_quality