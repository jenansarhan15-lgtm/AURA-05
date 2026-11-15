"""Quick checks: run  python tests/test_engines.py  . Each check is one rule the team must be able to explain."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import main as m

def tri(crew, day, chosen, yes=(), vit=None, alert=True):
    x = m.context(crew, day)
    return m.run_triage(x, list(chosen), list(yes), dict(x["vitals"], **(vit or {})), alert), x

r, x = tri("ASTRO-01", 50, ["headache"]);                 assert r["color"] == "GREEN", r
r, x = tri("ASTRO-02", 76, ["palpitations", "faint"]);    assert r["color"] == "YELLOW" and r["factors"], r
r, x = tri("ASTRO-04", 124, ["chest_pain"]);              assert r["color"] == "RED" and r["emergency"], r
r, x = tri("ASTRO-01", 50, ["headache"], [("headache", 0)]);  assert r["color"] == "RED"          # danger answer wins
r, x = tri("ASTRO-01", 50, ["earache"], [("earache", 0)]);    assert r["level"] == "YELLOW_STRONG"
r, x = tri("ASTRO-01", 50, [], vit={"spo2_pct": 90});         assert r["level"] == "YELLOW_STRONG"  # one vital in red band
r, x = tri("ASTRO-01", 50, [], vit={"spo2_pct": 90, "heart_rate_bpm": 125});  assert r["color"] == "RED"
r, x = tri("ASTRO-01", 50, [], alert=False);                  assert r["color"] == "RED"
r, x = tri("ASTRO-01", 50, [], vit={"diastolic_bp": 40});     assert r["color"] == "GREEN"         # diastolic never decides
# sleep/stress alone never make RED
for c in m.db.crew_list():
    for d in range(15, 181):
        xx = m.context(c["crew_id"], d)
        if not (c["crew_id"] == "ASTRO-04" and d == 124):
            assert xx["rest"]["color"] != "RED", (c, d, xx["rest"])
from collections import Counter
cnt = Counter(m.context(c["crew_id"], d)["rest"]["color"] for c in m.db.crew_list() for d in range(15, 181))
print("resting colours over the mission:", dict(cnt))
s = m.score_session([250] * 30 + [400] * 3, 1, m.R); assert s["valid"] and s["lapses"] == 3
print("All checks passed.")
