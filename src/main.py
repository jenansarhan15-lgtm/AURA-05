"""AURA-5  -  PROTOTYPE astronaut health companion (NASA Space Apps 2026).
This file only connects pages to engines. The logic lives in engines/, the knowledge in data/*.json.
Every text is stored as 'English || Arabic' and the page shows the language chosen in the corner (English by default).
Run:  python main.py   then open http://localhost:5000
"""
import json, os, random, time, secrets
from flask import Flask, Response, jsonify, redirect, render_template, request, session, url_for

import storage as db
from engines.baseline import compute_baseline
from engines.sleep import sleep_status
from engines.stress import stress_status
from engines.focus import score_session, focus_status
from engines.news2 import news2
from engines.triage import triage, LABELS
from engines.readiness import readiness, suggest_swaps
from engines.plan import tomorrow_plan
from engines.trends import early_warning

HERE = os.path.dirname(os.path.abspath(__file__))
load = lambda name: json.load(open(os.path.join(HERE, "data", name), encoding="utf-8"))
R, KB, SUP = load("rules.json"), load("knowledge.json"), load("support.json")
for sid, s in KB["symptoms"].items():                 # heart question (sex-aware safety net) + keywords
    if s.get("heart"):
        s["q"].insert(0, [KB["heart_q"], "red"])
    s["keywords"] = KB["keywords"][sid]
VITALS = ["heart_rate_bpm", "resp_rate", "spo2_pct", "systolic_bp", "diastolic_bp", "temp_c"]
VLABEL = dict(LABELS, diastolic_bp="Diastolic pressure || الضغط الانبساطي")
VUNIT = {"heart_rate_bpm": "bpm", "resp_rate": "/min", "spo2_pct": "%", "systolic_bp": "mmHg", "diastolic_bp": "mmHg", "temp_c": "°C"}
ROLE = {"Commander": "Commander || القائد", "Pilot": "Pilot || الطيار", "Medical Officer": "Medical Officer || المسؤول الطبي", "Engineer": "Engineer || المهندس"}
EVENT = {"Cargo arrival week": "أسبوع وصول الشحنة", "Departure preparation": "التحضير للمغادرة", "Spacewalk day": "يوم المشي الفضائي",
         "Spacewalk preparation": "التحضير للمشي الفضائي", "System repair": "إصلاح نظام"}
PROFILE = {"ASTRO-01": "M", "ASTRO-02": "F", "ASTRO-03": "F", "ASTRO-04": "M"}      # simulated crew profiles
MISSION_DAYS = 180
B = lambda en, ar: f"{en} || {ar}"

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Local demo only: sessions reset after restart.
db.init_db()


# ------------------------------------------------------------------ language
def lang():
    return session.get("lang", "en")


def loc(obj, lg=None):
    """Pick the current language from 'English || Arabic' texts, anywhere inside lists and dictionaries."""
    lg = lg or lang()
    if isinstance(obj, str):
        return obj.split(" || ")[0 if lg == "en" else -1] if " || " in obj else obj
    if isinstance(obj, list):
        return [loc(x, lg) for x in obj]
    if isinstance(obj, dict):
        return {k: loc(v, lg) for k, v in obj.items()}
    return obj


app.jinja_env.globals["_"] = loc
app.jinja_env.filters["loc"] = loc


@app.route("/lang/<code>")
def set_lang(code):
    session["lang"] = "ar" if code == "ar" else "en"
    return redirect(request.args.get("next") or request.referrer or url_for("home"))


# ------------------------------------------------------------------ helpers
def state():
    """Who is using the system, which mission day, and how far the ship is from Earth."""
    return (session.get("crew", "ASTRO-02"), int(session.get("day", 76)), session.get("loc", "mars_far"))


def get_vitals(crew_id, day, today):
    """THE ONE DOOR for vital signs. Sources in order: MANUAL entry > SIM device feed.
    A real sensor (suit, Bio-Monitor shirt, watch) would plug in here as a third source called DEVICE."""
    manual = db.get_manual_vitals(crew_id, day)
    values, source = {}, {}
    for k in VITALS:
        values[k], source[k] = (manual[k], "MANUAL") if k in manual else (today[k], "SIM")
    return values, source


def context(crew_id, day):
    """Everything the system knows about one astronaut on one day."""
    rows = db.crew_rows(crew_id)
    upto = [dict(r) for r in rows if r["mission_day"] <= day]
    today = upto[-1]
    ci = db.get_checkins(crew_id, day)
    m, e = ci.get("morning", {}), ci.get("evening", {})
    for src, dst in (("sleep_hours", "sleep_hours"), ("sleep_problem", "sleep_problem"), ("alertness", "alertness_self_1to10")):
        if src in m: today[dst] = m[src]
    for src, dst in (("stress", "stress_self_1to10"), ("mood", "mood_self_1to10"), ("workload", "workload_1to10"),
                     ("lonely", "loneliness_1to10"), ("team", "team_1to5")):
        if src in e: today[dst] = e[src]
    vitals, vsrc = get_vitals(crew_id, day, today)
    base = compute_baseline(rows, R["baseline_days"])
    nights = [r["sleep_hours"] for r in upto[-7:]]
    sleep = sleep_status(nights, R)
    stress = stress_status(today["stress_self_1to10"], vitals["heart_rate_bpm"], base["heart_rate_bpm"]["mean"],
                           [r["stress_self_1to10"] for r in upto[-3:-1]], R)
    # focus: a REAL game played today wins; otherwise the simulated reaction time
    focus = {"src": "SIM", "drop_pct": round((today["reaction_ms"] - base["reaction_ms"]["mean"]) / base["reaction_ms"]["mean"] * 100, 1),
             "felt10": int(today["alertness_self_1to10"])}
    played = [g for g in db.games_today(crew_id, day) if g["valid"]]
    if played:
        st = focus_status(played[-1], *game_baseline(crew_id, exclude_last=True), played[-1]["self_alertness"], R)
        if "drop_pct" in st:
            focus = {"src": "REAL", "drop_pct": st["drop_pct"], "felt10": st["felt10"]}
    focus["low"] = focus["drop_pct"] >= R["focus_drop_pct"]
    focus["measured10"] = max(0, min(10, round(10 - max(0, focus["drop_pct"]) / 5)))
    focus["gap"] = focus["felt10"] - focus["measured10"]
    focus["blind"] = focus["gap"] >= R["gap_points"]
    rest = triage([], [], vitals, True, base, sleep, stress, focus["low"], KB, R)
    last = next((ev for ev in db.events(crew_id, day) if ev["kind"] in ("triage", "remeasure")), None)
    color, level = rest["color"], rest["level"]
    rank = ["GREEN", "YELLOW", "YELLOW_STRONG", "RED"]            # today's status = the worse of: last assessment, current vitals
    if last and rank.index(last["detail"].get("level", last["color"])) > rank.index(level):
        color, level = last["color"], last["detail"].get("level", last["color"])
    return {"crew_id": crew_id, "day": day, "today": today, "vitals": vitals, "vsrc": vsrc, "base": base, "nights": nights,
            "sleep": sleep, "stress": stress, "focus": focus, "rest": rest, "color": color, "level": level,
            "lonely_high": today["loneliness_1to10"] >= R["lonely_high"], "checkins": ci, "last_triage": last,
            "role": ROLE.get(today["role"], today["role"]), "sex": PROFILE.get(crew_id, "M"),
            "trends": early_warning(upto, base, R)}


def game_baseline(player, exclude_last=False):
    """Personal baseline = first two valid sessions. Before that, a general reference (prototype assumption)."""
    past = db.player_sessions(player)
    if exclude_last:
        past = past[:-1]
    if len(past) >= 2:
        return sum(p["mean_speed"] for p in past[:2]) / 2, sum(p["lapses"] for p in past[:2]) / 2
    return 1000 / R["ref_rt_ms"], 0


def crew_ready(day):
    out = {}
    for c in db.crew_list():
        x = context(c["crew_id"], day)
        out[c["crew_id"]] = dict(readiness(x["sleep"], x["stress"], x["focus"]["drop_pct"], x["color"]),
                                 role=x["role"], team=x["today"]["team_1to5"], lonely=x["today"]["loneliness_1to10"])
    return out


EARTH = {"GREEN": B("Included in the daily report to Earth", "أُدرج في التقرير اليومي للأرض"),
         "YELLOW": B("Early notice sent: the ground team is following and preparing", "أُرسل تنبيه مبكر: الفريق الأرضي يتابع ويستعد"),
         "YELLOW_STRONG": B("Notice sent: the flight surgeon is asked to review within the hour", "أُرسل إشعار: مطلوب من الطبيب الأرضي المراجعة خلال ساعة"),
         "RED": B("SOS summary sent automatically", "أُرسل ملخص SOS تلقائياً")}


@app.context_processor
def inject():
    crew_id, day, where = state()
    row = db.q("SELECT event, role FROM daily_log WHERE crew_id=? AND mission_day=?", (crew_id, day))[0]
    ev = B(row["event"], EVENT.get(row["event"], row["event"])) if row["event"] else ""
    return {"S": {"crew": crew_id, "day": day, "loc": where, "event": ev, "role": ROLE.get(row["role"], row["role"]),
                  "total": MISSION_DAYS, "pct": round(day / MISSION_DAYS * 100)},
            "CREW": db.crew_list(), "ROLE": ROLE, "COMMS": R["comms"], "R": R, "VLABEL": VLABEL, "VUNIT": VUNIT, "VITALS": VITALS,
            "LANG": lang(), "COLOR": {"GREEN": "Green || أخضر", "YELLOW": "Yellow || أصفر", "RED": "Red || أحمر"}, "EARTH": EARTH,
            "VOICE": KB["voice"]}


@app.template_filter("clock")
def clock(ts):
    return time.strftime("%H:%M:%S", time.localtime(ts))


# ------------------------------------------------------------------ pages
@app.route("/set", methods=["POST"])
def set_state():
    session["crew"] = request.form.get("crew", "ASTRO-02")
    session["day"] = max(15, min(MISSION_DAYS, int(request.form.get("day") or 76)))
    session["loc"] = request.form.get("loc", "mars_far")
    return redirect(request.form.get("next") or url_for("home"))


@app.route("/scenario/<name>")
def scenario(name):
    session["crew"], session["day"] = {"green": ("ASTRO-01", 50), "yellow": ("ASTRO-02", 76), "red": ("ASTRO-04", 124)}.get(name, ("ASTRO-02", 76))
    return redirect(url_for("home"))


def the_plan(x):
    return tomorrow_plan(x["sleep"], x["stress"], x["focus"]["low"], x["color"], x["lonely_high"], x["today"]["sleep_problem"])


@app.route("/")
def home():
    crew_id, day, _ = state()
    x = context(crew_id, day)
    notice = next((ev for ev in db.events(crew_id, day) if ev["kind"] == "earth"), None)
    return render_template("home.html", x=x, plan=the_plan(x), n=news2(x["vitals"], R), recent=db.events(crew_id, limit=5),
                           games=len(db.games_today(crew_id, day)), notice=notice, SUP=SUP)


@app.route("/checkin", methods=["GET", "POST"])
def checkin():
    crew_id, day, _ = state()
    if request.method == "POST":
        f, kind = request.form, request.form["kind"]
        if kind == "morning":
            data = {"sleep_hours": float(f["sleep_hours"]), "sleep_quality": int(f["sleep_quality"]),
                    "sleep_problem": f["sleep_problem"], "alertness": int(f["alertness"])}
        else:
            data = {k: int(f[k]) for k in ("mood", "stress", "workload", "lonely", "team", "meals", "caffeine")}
            data.update(water=f["water"], feelings=f.getlist("feelings"), note=f.get("note", "")[:300])
        db.save_checkin(crew_id, day, kind, data)
        db.add_event(crew_id, day, "checkin", "", B("Morning check-in", "تسجيل الصباح") if kind == "morning" else B("Evening check-in", "تسجيل المساء"), data)
        return redirect(url_for("sleep_page") if kind == "morning" and data["sleep_problem"] != "none" else url_for("home"))
    return render_template("checkin.html", x=context(crew_id, day), SUP=SUP)


@app.route("/vitals", methods=["POST"])
def vitals_manual():
    crew_id, day, _ = state()
    if request.form.get("reset"):
        db.save_manual_vitals(crew_id, day, {})
    else:
        data = {k: float(request.form[k]) for k in VITALS if request.form.get(k)}
        db.save_manual_vitals(crew_id, day, data)
        db.add_event(crew_id, day, "vitals", "", B("Manual vital signs entry", "إدخال قياسات يدوي"), data)
    return redirect(request.form.get("next") or url_for("home"))


@app.route("/body")
def body():
    crew_id, day, _ = state()
    return render_template("body.html", x=context(crew_id, day), KB=loc(KB), SUP=SUP)


def run_triage(x, chosen, yes, vitals, alert):
    return triage(chosen, yes, vitals, alert, x["base"], x["sleep"], x["stress"], x["focus"]["low"], KB, R)


def names(chosen, i):
    return ", ".join(KB["symptoms"][s]["name"].split(" || ")[i] for s in chosen)


@app.route("/triage", methods=["POST"])
def do_triage():
    crew_id, day, _ = state()
    x = context(crew_id, day)
    chosen = [s for s in request.form.getlist("sym") if s in KB["symptoms"]]
    yes = [(a.split(":")[0], int(a.split(":")[1])) for a in request.form.getlist("yes") if a.split(":")[0] in chosen]
    vitals = {k: float(request.form.get(k) or x["vitals"][k]) for k in VITALS}
    alert = request.form.get("alert", "1") == "1"
    res = run_triage(x, chosen, yes, vitals, alert)
    title = B("Complaint: " + names(chosen, 0), "شكوى: " + names(chosen, 1)) if chosen else B("Vital signs check", "فحص قياسات")
    eid = db.add_event(crew_id, day, "triage", res["color"], title,
                       {"chosen": chosen, "yes": yes, "vitals": vitals, "alert": alert, "level": res["level"],
                        "reasons": res["reasons"], "factors": res["factors"], "news2": res["news2"]["total"], "round": 0})
    db.add_event(crew_id, day, "earth", res["color"], EARTH[res["level"]], {"level": res["level"], "event": eid})   # Earth is always kept informed
    return redirect(url_for("result", eid=eid))


@app.route("/result/<int:eid>")
def result(eid):
    ev = db.get_event(eid)
    x = context(ev["crew_id"], ev["mission_day"])
    d = ev["detail"]
    res = run_triage(x, d["chosen"], [tuple(y) for y in d["yes"]], d["vitals"], d["alert"])
    res.update(color=ev["color"], level=d["level"], monitor=R["monitor"][d["level"]])
    syms = [dict(KB["symptoms"][s], id=s) for s in d["chosen"]]
    return render_template("result.html", ev=ev, d=d, res=res, syms=syms, x=x, KB=KB, SUP=SUP,
                           speed=int(request.args.get("speed", 1)), auto=request.args.get("auto", "1") == "1")


@app.route("/remeasure/<int:eid>", methods=["POST"])
def remeasure(eid):
    """The re-measure loop: YELLOW is never left open. Better -> green. Not better -> one step up."""
    ev = db.get_event(eid)
    d, x = ev["detail"], context(ev["crew_id"], ev["mission_day"])
    vitals = {k: float(request.form.get(k) or d["vitals"][k]) for k in VITALS}
    better = request.form.get("better") == "1"
    res = run_triage(x, d["chosen"], [tuple(y) for y in d["yes"]], vitals, d["alert"])
    if res["color"] == "RED":
        color, level, note = "RED", "RED", B("The new readings are in the red band.", "القياسات الجديدة في المنطقة الحمراء.")
    elif not better:
        level = "YELLOW_STRONG" if d["level"] == "YELLOW" else "RED"
        color = "RED" if level == "RED" else "YELLOW"
        note = B("Symptoms did not improve: the level was raised one step.", "لم تتحسن الأعراض: تم رفع المستوى درجة.")
    elif res["level"] == "YELLOW_STRONG":
        color, level, note = "YELLOW", "YELLOW_STRONG", B("You feel better but one reading is still in the red band.", "تحسّن الإحساس لكن ما زال قياس في المنطقة الحمراء.")
    else:
        color, level, note = "GREEN", "GREEN", B("Symptoms improved and the readings are acceptable. Follow-up every 4 hours for the rest of the day.",
                                                 "تحسّنت الأعراض والقياسات مقبولة. متابعة كل 4 ساعات لباقي اليوم.")
    new = dict(d, vitals=vitals, level=level, round=d.get("round", 0) + 1, note=note, reasons=res["reasons"], news2=res["news2"]["total"])
    t = ev["title"].replace("Re-measure: ", "").replace("إعادة قياس: ", "").split(" || ")
    nid = db.add_event(ev["crew_id"], ev["mission_day"], "remeasure", color, B("Re-measure: " + t[0], "إعادة قياس: " + t[-1]), new)
    db.add_event(ev["crew_id"], ev["mission_day"], "earth", color, EARTH[level], {"level": level, "event": nid})
    return redirect(url_for("result", eid=nid))


@app.route("/calm")
def calm():
    return render_template("calm.html", back=request.args.get("back", "/"))


@app.route("/calm/done", methods=["POST"])
def calm_done():
    crew_id, day, _ = state()
    db.add_event(crew_id, day, "calm", "", B("3-minute breathing session", "جلسة تنفس 3 دقائق"), {})
    return redirect(request.form.get("back") or "/")


# ---- focus game ----
@app.route("/game")
def game():
    crew_id, day, _ = state()
    x = context(crew_id, day)
    return render_template("game.html", x=x, seconds=int(request.args.get("seconds", 180)), task=request.args.get("task", ""),
                           played=len(db.games_today(crew_id, day)), sessions=db.all_games(), blocked=x["color"] == "RED")


def explain(st, quick, reference):
    """Plain scientific explanation of the result: measured score, felt score, and what the gap means."""
    out = []
    felt, meas, gap = st["felt10"], st["measured10"], st["felt10"] - st["measured10"]
    out.append(B(f"Measured focus {meas}/10. You said you felt {felt}/10.", f"تركيزك المقيس {meas}/10. وقلت إنك تشعر {felt}/10."))
    if gap >= R["gap_points"]:
        out.append(B("Mismatch: you feel better than the test measures. Research on sleep restriction found that performance keeps falling "
                     "while the feeling of sleepiness levels off (Van Dongen 2003). Do not rely on your feeling for precise tasks today.",
                     "تعارض: تشعر أنك أفضل مما يقيسه الاختبار. أبحاث تقييد النوم وجدت أن الأداء يستمر بالهبوط بينما الإحساس بالنعاس يثبت "
                     "(Van Dongen 2003). لا تعتمد على إحساسك في المهام الدقيقة اليوم."))
    elif gap <= -R["gap_points"]:
        out.append(B("Mismatch the other way: you feel worse than the test measures. Your attention is working normally, so the feeling may come from stress or mood. Psychological Support can help.",
                     "تعارض بالاتجاه الآخر: تشعر أنك أسوأ مما يقيسه الاختبار. انتباهك يعمل طبيعياً، فقد يكون الإحساس من التوتر أو المزاج. «الدعم النفسي» قد يساعد."))
    else:
        out.append(B("Your feeling matches the measurement.", "إحساسك يطابق القياس."))
    if st["status"] == "LOW":
        out.append(B(f"Your reaction speed is {st['drop_pct']}% below your normal. What you need: rest 20 minutes and test again, or swap the precise task with a ready crewmate, and protect tonight's sleep.",
                     f"سرعة رد فعلك أقل من طبيعتك بـ {st['drop_pct']}%. ما تحتاجه: استراحة 20 دقيقة ثم إعادة الاختبار، أو تبديل المهمة الدقيقة مع زميل جاهز، وحماية نوم الليلة."))
    else:
        out.append(B("Your reaction speed is within your normal range. You can carry out the task.", "سرعة رد فعلك ضمن طبيعتك. تستطيع تنفيذ المهمة."))
    if quick:
        out.append(B("Quick test: a short estimate, less accurate than the validated 3-minute test.", "اختبار سريع: تقدير قصير، أقل دقة من اختبار الـ 3 دقائق المثبت علمياً."))
    if reference:
        out.append(B(f"Compared with a general reference ({R['ref_rt_ms']} ms) until two sessions set your personal baseline. This reference is a prototype assumption.",
                     f"المقارنة مع مرجع عام ({R['ref_rt_ms']} مللي ثانية) حتى تُحدَّد طبيعتك الشخصية من جلستين. هذا المرجع افتراض للنموذج الأولي."))
    return out


@app.route("/api/game", methods=["POST"])
def api_game():
    crew_id, day, _ = state()
    d = request.get_json()
    player = (d.get("player") or crew_id).strip()[:40]
    secs = int(d.get("seconds", 180))
    rules = dict(R, min_trials=max(4, min(R["min_trials"], round(secs / 9))))
    s = score_session([float(v) for v in d["rts"]], int(d["false_starts"]), rules)
    reference = len(db.player_sessions(player)) < 2
    st = focus_status(s, *game_baseline(player), int(d["self_alertness"]), R)
    db.save_game(player, crew_id, day, d.get("task", ""), int(d["self_alertness"]), s, d["rts"], "REAL")
    color = {"LOW": "YELLOW", "OK": "GREEN"}.get(st["status"], "")
    db.add_event(crew_id, day, "game", color, B("Focus game", "لعبة التركيز"), {"session": s, "status": st, "player": player})
    text = explain(st, secs < 180, reference) if "drop_pct" in st else [B("The session is not valid: too many early taps or too few trials. Please play again.",
                                                                          "الجلسة غير صالحة: ضغطات مبكرة كثيرة أو محاولات قليلة. أعد اللعب.")]
    return jsonify({"session": s, "status": st, "explain": loc(text)})


# ---- tasks + crew readiness ----
@app.route("/tasks", methods=["GET", "POST"])
def tasks():
    crew_id, day, _ = state()
    ready = crew_ready(day)
    if request.method == "POST":
        db.add_event(crew_id, day, "swap", "YELLOW", request.form["text"], {})
        return redirect(url_for("tasks", sent=1))
    order = sorted(ready.items(), key=lambda kv: -kv[1]["score"])
    return render_template("tasks.html", ready=ready, order=order, tasks=SUP["tasks"], swaps=suggest_swaps(SUP["tasks"], ready),
                           me=crew_id, sent=request.args.get("sent"))


@app.route("/sleep", methods=["GET", "POST"])
def sleep_page():
    crew_id, day, _ = state()
    x = context(crew_id, day)
    problem = request.values.get("problem") or x["today"]["sleep_problem"]
    if request.method == "POST":
        nm = SUP["sleep"][problem]["name"].split(" || ")
        db.add_event(crew_id, day, "sleep", "", B("Sleep support: " + nm[0], "دعم النوم: " + nm[-1]), {"problem": problem})
        return redirect(url_for("sleep_page", problem=problem, saved=1))
    return render_template("sleep.html", x=x, SUP=SUP, problem=problem, saved=request.args.get("saved"))


@app.route("/mind", methods=["GET", "POST"])
def mind():
    crew_id, day, _ = state()
    x = context(crew_id, day)
    picked, urgent = [], False
    if request.method == "POST":
        picked = [f for f in request.form.getlist("feel") if f in SUP["feelings"]]
        urgent = bool(request.form.getlist("urgent"))
        if request.form.get("earth"):
            db.add_event(crew_id, day, "earth", "", B("Private session with ground support requested (simulated)", "طلب جلسة خاصة مع الدعم الأرضي (محاكاة)"), {"private": True})
        else:
            f = lambda i: ", ".join(SUP["feelings"][k]["name"].split(" || ")[i] for k in picked) or "-"
            db.add_event(crew_id, day, "mind", "RED" if urgent else "", B("Psychological support: " + f(0), "دعم نفسي: " + f(-1)), {"feelings": picked, "urgent": urgent})
    return render_template("mind.html", x=x, SUP=SUP, picked=picked, urgent=urgent, asked=bool(request.form.get("earth")))


@app.route("/team", methods=["GET", "POST"])
def team():
    crew_id, day, _ = state()
    if request.method == "POST":
        db.add_event(crew_id, day, "team", "", B("Team suggestion sent to the commander (simulated)", "اقتراح للفريق أُرسل للقائد (محاكاة)"), {})
        return redirect(url_for("team", sent=1))
    ready = crew_ready(day)
    counts = {b: sum(1 for r in ready.values() if r["band"] == b) for b in ("GREEN", "YELLOW", "RED")}
    worst = "RED" if counts["RED"] else "YELLOW" if counts["YELLOW"] >= 2 else "GREEN"
    week = []
    for dd in range(max(15, day - 6), day + 1):
        rr = crew_ready(dd) if dd != day else ready
        week.append({"day": dd, "bands": sorted((r["band"] for r in rr.values()), key="GREEN YELLOW RED".split().index)})
    avg = lambda k: round(sum(r[k] for r in ready.values()) / len(ready), 1)
    return render_template("team.html", counts=counts, week=week, worst=worst, SUP=SUP, team_avg=avg("team"),
                           lonely_avg=avg("lonely"), n=len(ready), sent=request.args.get("sent"))


@app.route("/tomorrow", methods=["GET", "POST"])
def tomorrow():
    crew_id, day, _ = state()
    x = context(crew_id, day)
    if request.method == "POST":
        db.add_event(crew_id, day, "plan", "", B(f"Plan for day {day + 1} accepted", f"قبول خطة اليوم {day + 1}"), {})
        return redirect(url_for("tomorrow", ok=1))
    return render_template("tomorrow.html", x=x, plan=the_plan(x), ok=request.args.get("ok"))


# ---- Silent Hour (SIMULATION ONLY: nothing is sent anywhere) ----
def build_packet(x, ev):
    d = ev["detail"] if ev else {}
    v = d.get("vitals", x["vitals"])
    return {"type": "AURA-5 SOS (SIMULATED - not transmitted)", "crew_id": x["crew_id"], "role": x["today"]["role"], "sex": x["sex"],
            "mission_day": x["day"], "color": ev["color"] if ev else "RED",
            "symptoms": [KB["symptoms"][s]["name"].split(" || ")[0] for s in d.get("chosen", [])],
            "symptom_ids": d.get("chosen", []), "danger_answers": [r.split(" || ")[0] for r in d.get("reasons", [])],
            "vitals": v, "news2_total": news2(v, R)["total"],
            "personal_baseline": {k: x["base"][k]["mean"] for k in ("heart_rate_bpm", "systolic_bp", "spo2_pct", "temp_c")},
            "context": {"sleep_last_night_h": x["sleep"]["last"], "sleep_avg_48h": x["sleep"]["avg48"],
                        "sleep_debt_7d_h": x["sleep"]["debt7"], "stress_self_1to10": x["stress"]["self"],
                        "stress_status": x["stress"]["status"], "focus_drop_pct": x["focus"]["drop_pct"]},
            "data_sources": x["vsrc"]}


@app.route("/silent/start", methods=["GET", "POST"])
def silent_start():
    crew_id, day, where = state()
    ev = db.get_event(int(request.values["event"])) if request.values.get("event") else None
    x = context(ev["crew_id"], ev["mission_day"]) if ev else context(crew_id, day)
    sid = db.start_silent(x["crew_id"], x["day"], where, 1, build_packet(x, ev))
    db.silent_log_add(sid, "send", B("SOS summary sent to Earth automatically (simulated)", "أُرسل ملخص SOS إلى الأرض تلقائياً (محاكاة)"))
    db.add_event(x["crew_id"], x["day"], "silent", "RED", B("Silent Hour started", "بدء الساعة الصامتة"), {"silent_id": sid})
    return redirect(url_for("silent", sid=sid))


@app.route("/silent/<int:sid>")
def silent(sid):
    s = db.get_silent(sid)
    comm = R["comms"][s["location"]]
    steps, seen = [], set()
    for sym in s["packet"]["symptom_ids"]:
        for st in KB["symptoms"][sym]["red_steps"]:
            if st not in seen:
                seen.add(st); steps.append({"t": st, "src": KB["symptoms"][sym]["source"]})
    if not steps:
        steps = [{"t": t, "src": "IFRC 2020, General approach"} for t in
                 [B("Secure the person in a safe, comfortable position.", "ثبّت المصاب في وضع آمن ومريح."),
                  B("Watch alertness and breathing continuously.", "راقب الوعي والتنفس باستمرار."),
                  B("Do not leave the person alone.", "لا تترك المصاب وحده."),
                  B("Note every change with its time.", "سجّل كل تغيّر مع الوقت.")]]
    timing = {"one_way": comm["one_way_s"], "review": R["ground_review_min"] * 60, "started": s["started"],
              "speed": s["speed"], "now": time.time(), "remeasure": R["silent_remeasure_minutes"] * 60}
    lg, done = db.silent_log(sid), set()
    for l in lg:                                       # restore which steps were already marked done
        if l["kind"] == "step":
            t = l["text"].split(" || ")[0]
            (done.add if t.startswith("Step done: ") else done.discard)(t.split(": ", 1)[1])
    for st in steps:
        st["done"] = st["t"].split(" || ")[0] in done
    return render_template("silent.html", s=s, comm=comm, steps=steps, log=lg, timing=timing,
                           packet_json=json.dumps(s["packet"], ensure_ascii=False, indent=2))


@app.route("/silent/<int:sid>/speed", methods=["POST"])
def silent_speed(sid):
    sp = float(request.form.get("speed", 1))
    db.run("UPDATE silent SET speed=?, started=?, location=? WHERE id=?",
           (sp, time.time(), request.form.get("loc") or db.get_silent(sid)["location"], sid))
    db.silent_log_add(sid, "note", B(f"Timer reset (demo speed x{int(sp)})", f"إعادة ضبط المؤقت (سرعة العرض ×{int(sp)})"))
    return redirect(url_for("silent", sid=sid))


@app.route("/api/silent/<int:sid>/log", methods=["POST"])
def api_silent_log(sid):
    d = request.get_json()
    db.silent_log_add(sid, d.get("kind", "note"), d["text"][:400])
    return jsonify(ok=True, ts=time.strftime("%H:%M:%S"))


@app.route("/api/silent/<int:sid>/measure", methods=["POST"])
def api_silent_measure(sid):
    """Re-measure during the Silent Hour. Automatic = a new SIMULATED sensor reading (old value + small noise). Manual = typed values."""
    s = db.get_silent(sid)
    d = request.get_json() or {}
    old = s["packet"]["vitals"]
    manual = any(d.get(k) not in (None, "") for k in VITALS)
    v = {k: (float(d[k]) if d.get(k) not in (None, "") else round(old[k] + random.uniform(-1, 1) * (0.2 if k == "temp_c" else 2), 1)) for k in VITALS}
    n = news2(v, R)
    en = (f"pulse {v['heart_rate_bpm']:.0f}, breathing {v['resp_rate']:.0f}, oxygen {v['spo2_pct']:.0f}%, pressure {v['systolic_bp']:.0f}/{v['diastolic_bp']:.0f}, temperature {v['temp_c']}, NEWS2 = {n['total']}")
    ar = (f"نبض {v['heart_rate_bpm']:.0f}، تنفس {v['resp_rate']:.0f}، أكسجين {v['spo2_pct']:.0f}%، ضغط {v['systolic_bp']:.0f}/{v['diastolic_bp']:.0f}، حرارة {v['temp_c']}، NEWS2 = {n['total']}")
    text = B(("Manual entry: " if manual else "Automatic sensor reading (simulated): ") + en, ("إدخال يدوي: " if manual else "قراءة تلقائية من الحسّاس (محاكاة): ") + ar)
    db.silent_log_add(sid, "measure", text)
    return jsonify(text=loc(text), ts=time.strftime("%H:%M:%S"), news2=n["total"])


@app.route("/silent/<int:sid>/summary.txt")
def silent_summary(sid):
    s = db.get_silent(sid)
    p = s["packet"]
    lines = ["AURA-5  -  SOS SUMMARY", "PROTOTYPE / SIMULATION ONLY: this file was NOT transmitted to Earth or to anyone.", "",
             f"Crew: {p['crew_id']} ({p['role']}, {p.get('sex', '-')})   Mission day: {p['mission_day']}   Location: {s['location']}",
             f"Started: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(s['started']))}", "",
             "SYMPTOMS: " + ("; ".join(p["symptoms"]) or "-"), "DANGER SIGNS: " + ("; ".join(p["danger_answers"]) or "-"), "",
             "VITAL SIGNS (source):"]
    lines += [f"  {k}: {p['vitals'][k]}  [{p['data_sources'].get(k, 'SIM')}]" for k in VITALS]
    lines += [f"  NEWS2 total: {p['news2_total']}  (Earth hospital scale, not validated for space)", "",
              "PERSONAL BASELINE: " + json.dumps(p["personal_baseline"]), "CONTEXT: " + json.dumps(p["context"]), "", "LOG:"]
    lines += [f"  {time.strftime('%H:%M:%S', time.localtime(l['ts']))}  [{l['kind']}]  {l['text'].split(' || ')[0]}" for l in db.silent_log(sid)]
    lines += ["", "This summary is a screening aid for the flight surgeon. It is not a diagnosis."]
    return Response("﻿" + "\n".join(lines), mimetype="text/plain; charset=utf-8",
                    headers={"Content-Disposition": f"attachment; filename=aura5_sos_{sid}.txt"})


@app.route("/log")
def log():
    crew_id, day, _ = state()
    who = request.args.get("who", crew_id)
    return render_template("log.html", events=db.events(None if who == "all" else who), who=who)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
