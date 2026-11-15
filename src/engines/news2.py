"""NEWS2 score (Royal College of Physicians, 2017). An EARTH hospital early-warning tool:
we use it as the best available evidence-based scale, and say clearly it is not validated for space.
Each vital sign gets 0-3 points. Diastolic pressure is NOT part of NEWS2, so it never changes the colour."""

LABELS = {"resp_rate": "معدل التنفس", "spo2_pct": "تشبع الأكسجين", "systolic_bp": "الضغط الانقباضي",
          "heart_rate_bpm": "النبض", "temp_c": "الحرارة"}


def points(value, bands):
    for upper, pts in bands:          # bands are sorted: first upper limit that fits wins
        if value <= upper:
            return pts
    return bands[-1][1]


def news2(vitals, R):
    """Return total score, points per vital sign, and the highest single score."""
    parts = {}
    for key, bands in R["news2"].items():
        if vitals.get(key) is not None:
            parts[key] = points(float(vitals[key]), bands)
    total = sum(parts.values())
    return {"total": total, "parts": parts, "max_single": max(parts.values(), default=0)}
