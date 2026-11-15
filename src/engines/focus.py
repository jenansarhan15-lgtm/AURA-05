"""Focus engine: scores the 3-minute reaction game (a build of NASA's short PVT-B test).
The game measures vigilant attention, not all of cognition. It can raise GREEN to YELLOW, never lower RED."""
from statistics import mean


def score_session(rts, false_starts, R):
    """rts = valid reaction times in ms (false starts already removed by the browser)."""
    if not rts:
        return {"valid": False, "n_trials": 0, "false_starts": false_starts}
    speeds = [1000.0 / rt for rt in rts]                       # responses per second: the main metric
    k = max(1, len(speeds) // 10)
    slowest10 = mean(sorted(speeds)[:k])                       # the slowest 10 percent of responses
    lapses = sum(1 for rt in rts if rt >= R["lapse_ms"])       # 355 ms in NASA's short version
    valid = len(rts) >= R["min_trials"] and false_starts <= R["max_false_starts"]
    return {"valid": valid, "n_trials": len(rts), "mean_rt": round(mean(rts)),
            "mean_speed": round(mean(speeds), 3), "slowest10_speed": round(slowest10, 3),
            "lapses": lapses, "false_starts": false_starts}


def focus_status(session, base_speed, base_lapses, self_alertness, R):
    """Compare this session with the SAME person's baseline, and with how they said they feel."""
    if not session["valid"]:
        return {"status": "REPEAT"}
    if base_speed is None:
        return {"status": "BASELINE", "note": "Still learning your normal (need 2 valid sessions)."}

    drop_pct = round((base_speed - session["mean_speed"]) / base_speed * 100, 1)
    low = drop_pct >= R["focus_drop_pct"] or session["lapses"] >= base_lapses + R["lapse_plus"]

    measured10 = max(0, min(10, round(10 - max(0, drop_pct) / 5)))   # every 5% slower = one point
    gap = self_alertness - measured10                                 # positive = feels better than measured
    return {"status": "LOW" if low else "OK", "drop_pct": drop_pct, "measured10": measured10,
            "felt10": self_alertness, "gap": gap, "blind_spot": gap >= R["gap_points"]}
