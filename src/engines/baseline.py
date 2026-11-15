"""Personal baseline: each astronaut is compared with their OWN normal, not a population average."""
from statistics import mean, pstdev

METRICS = ["heart_rate_bpm", "systolic_bp", "spo2_pct", "temp_c", "reaction_ms", "sleep_hours"]


def compute_baseline(rows, days):
    """rows = this astronaut's daily records (dicts). Uses the first `days` mission days."""
    first = [r for r in rows if r["mission_day"] <= days]
    out = {}
    for m in METRICS:
        vals = [float(r[m]) for r in first]
        out[m] = {"mean": round(mean(vals), 1), "sd": round(pstdev(vals), 2) or 0.01}
    return out


def z_score(value, base):
    """How unusual is this value FOR THIS PERSON. |z| >= 2 means unusual."""
    return (value - base["mean"]) / base["sd"]
