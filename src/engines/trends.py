"""Early warning from TRENDS: compares the last few days with the astronaut's own baseline.
This is an early notice that something is drifting. It is NOT a prediction of a disease. Limits are prototype values."""
from statistics import mean
both = lambda en, ar: f"{en} || {ar}"


def early_warning(days, base, R):
    """days = this astronaut's daily rows up to today (oldest first). Returns a list of trend notices."""
    n = R["trend_days"]
    if len(days) < n:
        return []
    last = days[-n:]
    avg = lambda key: mean(d[key] for d in last)
    out = []
    hr_up = avg("heart_rate_bpm") - base["heart_rate_bpm"]["mean"]
    if hr_up >= R["trend_hr_bpm"]:
        out.append(both(f"Resting pulse has been {hr_up:.0f} bpm above your baseline for {n} days",
                        f"نبض الراحة أعلى من طبيعتك بـ {hr_up:.0f} نبضة منذ {n} أيام"))
    if all(d["sleep_hours"] < R["sleep_low_h"] for d in last):
        out.append(both(f"Less than {R['sleep_low_h']:.0f} hours of sleep for {n} nights in a row",
                        f"نوم أقل من {R['sleep_low_h']:.0f} ساعات لـ {n} ليالٍ متتالية"))
    rt_up = (avg("reaction_ms") - base["reaction_ms"]["mean"]) / base["reaction_ms"]["mean"] * 100
    if rt_up >= R["trend_rt_pct"]:
        out.append(both(f"Reaction time has been {rt_up:.0f}% slower than your baseline for {n} days",
                        f"زمن رد الفعل أبطأ من طبيعتك بـ {rt_up:.0f}% منذ {n} أيام"))
    if all(d["stress_self_1to10"] >= R["stress_mid"] for d in last) and last[-1]["stress_self_1to10"] >= last[0]["stress_self_1to10"]:
        out.append(both(f"Stress has stayed raised for {n} days", f"التوتر مرتفع منذ {n} أيام"))
    if base["spo2_pct"]["mean"] - avg("spo2_pct") >= R["trend_spo2"]:
        out.append(both(f"Oxygen saturation has been below your baseline for {n} days", f"تشبع الأكسجين أقل من طبيعتك منذ {n} أيام"))
    return out
