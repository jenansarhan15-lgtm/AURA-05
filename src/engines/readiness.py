"""Readiness engine: one number (0-100) per crew member for TODAY, used to share hard tasks fairly.
Privacy rule: other crew members see only the band (ready / needs rest / not available), never the reasons."""


def readiness(sleep, stress, focus_drop_pct, color_today):
    score, why = 100, []
    if sleep["status"] == "LOW":
        score -= 30; why.append("Short sleep || نوم قليل")
    elif sleep["status"] == "WATCH":
        score -= 12; why.append("Less sleep than needed || نوم أقل من المطلوب")
    if stress["status"] == "PERSISTENT":
        score -= 20; why.append("Stress for several days || توتر مستمر")
    elif stress["status"] == "HIGH":
        score -= 12; why.append("High stress || توتر عالٍ")
    if focus_drop_pct is not None and focus_drop_pct > 0:
        score -= min(35, round(focus_drop_pct * 2)); why.append(f"Focus {focus_drop_pct}% slower than normal || التركيز أبطأ {focus_drop_pct}% من الطبيعي")
    if color_today == "RED":
        score = min(score, 20); why.append("Red health status today || حالة صحية حمراء اليوم")
    elif color_today == "YELLOW":
        score = min(score, 65); why.append("Yellow status today || حالة صفراء اليوم")
    score = max(0, score)
    band = "GREEN" if score >= 75 else "YELLOW" if score >= 50 else "RED"
    return {"score": score, "band": band, "why": why}


en = lambda t: t.split(' || ')[0]
ar = lambda t: t.split(' || ')[-1]


def suggest_swaps(tasks, ready):
    """For every HIGH-risk task whose owner is not green, propose the most ready crew member instead."""
    out = []
    best = sorted(ready.items(), key=lambda kv: -kv[1]["score"])
    for t in tasks:
        r = ready[t["crew_id"]]
        if t["risk"] == "high" and r["band"] != "GREEN":
            alt = next((cid for cid, rr in best if cid != t["crew_id"] and rr["band"] != "RED"
                        and rr["score"] >= r["score"] + 10), None)       # clearly more ready than the owner
            out.append({"task": t, "to": alt,
                        "text": ((f"Suggest moving \"{en(t['title'])}\" from {t['crew_id']} to {alt} (most ready today) || "
                                  f"يُقترح تبديل «{ar(t['title'])}» من {t['crew_id']} إلى {alt} (الأكثر جاهزية اليوم)") if alt else
                                 (f"No crewmate is clearly more ready: suggest postponing \"{en(t['title'])}\" || "
                                  f"لا يوجد زميل أكثر جاهزية: يُقترح تأجيل «{ar(t['title'])}»"))})
    return out
