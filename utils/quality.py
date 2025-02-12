# utils/quality.py

def compute_quality_score(info: dict) -> float:
    """
    Computes a quality score from the anime's metadata.
    - Normalizes average_score (0 to 1) and popularity (assumes 1,000,000 as high).
    - For TV shows, multiplies the base quality by 1.5 and adds a bonus based on TV ranking.
    - For movies, uses a multiplier of 1.0.
    - For other formats (OVA, ONA, SPECIAL), uses a multiplier of 0.5.
    - For TV_SHORT, uses a very low multiplier (0.1) so they are unlikely to rank high.
    
    Ranking bonus for TV: bonus = max(0, (100 - rank) / 100)
    """
    avg = info.get("average_score") or 0  # Typically out of 100.
    pop = info.get("popularity") or 0       # Raw number.
    normalized_avg = avg / 100.0            # Range: 0 to 1.
    normalized_pop = pop / 1_000_000.0      # Adjust denominator as needed.
    
    # Base quality score.
    base_quality = (normalized_avg * 2) + normalized_pop

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
        quality_multiplier = 1.0  # Movies get baseline treatment.
        return base_quality * quality_multiplier

    elif fmt in {"OVA", "ONA", "SPECIAL"}:
        quality_multiplier = 0.5  # Penalize these formats moderately.
        return base_quality * quality_multiplier

    elif fmt == "TV_SHORT":
        quality_multiplier = 0.1  # Heavily penalize TV shorts.
        return base_quality * quality_multiplier

    else:
        # If format is unknown, just return the base quality.
        return base_quality