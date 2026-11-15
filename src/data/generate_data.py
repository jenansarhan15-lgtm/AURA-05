"""
Aegis-Mind  -  Simulated mission dataset generator
SIMULATED DATA. Not real astronaut measurements.

Every number below is a simple, explainable rule. The parameters are chosen to be
consistent with published averages (see SOURCES), they are not a medical model.

SOURCES used to choose parameters:
- Sleep in space averages about 6 h vs 8.5 h scheduled (Barger et al., Lancet Neurology 2014).
- Sleep of 6 h or less is linked to slower reaction speed and higher stress in 24 ISS
  astronauts (Reaction Self-Test study, PMC8919197).
- Under chronic sleep restriction performance keeps falling while self-rated sleepiness
  levels off (Van Dongen et al., Sleep 2003).
"""
import csv, random

random.seed(2026)
DAYS = 180
CREW = [  # personal baselines: each person is compared with their own normal
    {"id": "ASTRO-01", "role": "Commander",       "rt_base": 235, "hr_base": 62, "sleep_need": 7.0, "blink_base": 16},
    {"id": "ASTRO-02", "role": "Pilot",           "rt_base": 250, "hr_base": 66, "sleep_need": 7.3, "blink_base": 18},
    {"id": "ASTRO-03", "role": "Medical Officer", "rt_base": 242, "hr_base": 59, "sleep_need": 6.8, "blink_base": 15},
    {"id": "ASTRO-04", "role": "Engineer",        "rt_base": 260, "hr_base": 70, "sleep_need": 7.4, "blink_base": 19},
]
# Mission events that raise workload (day ranges, inclusive)
EVENTS = [(28, 33, "Cargo arrival week"), (74, 78, "Spacewalk preparation"),
          (79, 79, "Spacewalk day"), (121, 127, "System repair"), (160, 166, "Departure preparation")]

def clamp(x, lo, hi): return max(lo, min(hi, x))

rows = []
for c in CREW:
    debt = 0.0
    for day in range(1, DAYS + 1):
        event = next((n for a, b, n in EVENTS if a <= day <= b), "")
        # 1) workload 1-10: normal days about 5, event days about 8
        workload = clamp(round(random.gauss(8.2 if event else 5.0, 1.0)), 1, 10)
        # 2) sleep hours: mean about 6.1 h, less on heavy days
        sleep = clamp(random.gauss(6.3 - 0.25 * (workload - 5), 0.7), 3.0, 9.0)
        if c["id"] == "ASTRO-01" and 43 <= day <= 50:      # scripted well-rested week (GREEN demo)
            workload, sleep = 4, clamp(random.gauss(7.5, 0.15), 7.2, 8.0)
        if c["id"] == "ASTRO-02" and 74 <= day <= 76:      # scripted short nights before the spacewalk (YELLOW demo)
            sleep = clamp(random.gauss(4.8, 0.2), 4.4, 5.2)
        # 3) sleep debt builds when sleep < personal need, and fades slowly
        debt = clamp(0.6 * debt + (c["sleep_need"] - sleep), 0, 10)
        # 4) MEASURED: reaction time slows and lapses rise with sleep debt
        rt = c["rt_base"] * (1 + 0.022 * debt) + random.gauss(0, 8)
        lapses = max(0, round(random.gauss(0.5 + 0.75 * debt, 1.0)))
        # 5) SELF-REPORT: felt alertness drops at first, then levels off (the blind spot)
        alert_self = clamp(round(8.6 - 0.35 * min(debt, 2.5) + random.gauss(0, 0.6)), 1, 10)
        stress_self = clamp(round(2.5 + 0.55 * (workload - 5) + 0.25 * min(debt, 6) + random.gauss(0, 0.8)), 1, 10)
        if c["id"] == "ASTRO-02" and 74 <= day <= 76:
            stress_self = 8
        mood_self = clamp(round(8 - 0.4 * stress_self + random.gauss(0, 0.8)), 1, 10)
        if c["id"] == "ASTRO-02" and day in (75, 76):       # scripted blind spot: feels fine, measures slow
            rt, alert_self, lapses = c["rt_base"] * (1.15 if day == 75 else 1.24), 9, 6
        # 6) basic vitals: resting heart rate rises a little with stress
        hr = round(c["hr_base"] + 1.2 * (stress_self - 3) + random.gauss(0, 2))
        sys_bp = round(119 + 1.0 * (stress_self - 3) + random.gauss(0, 4))
        temp = round(random.gauss(36.7, 0.15), 1)
        spo2 = clamp(round(random.gauss(97.5, 0.8)), 94, 100)
        # 6a) extra daily-log fields (illustrative rules, SIMULATED)
        dia_bp = round(76 + 0.6 * (stress_self - 3) + random.gauss(0, 3))          # shown only, never decides the colour
        resp = clamp(round(random.gauss(15, 1.2)), 12, 19)                         # breaths per minute
        lonely = clamp(round(2 + day / 60 + random.gauss(0, 1.0)), 1, 10)          # rises slowly with mission time
        team = clamp(round(4.3 - 0.15 * (stress_self - 3) + random.gauss(0, 0.5)), 1, 5)
        meals = 3 if random.random() > 0.12 * (workload - 3) else 2
        caffeine = clamp(round(1 + 0.4 * debt + random.gauss(0, 0.6)), 0, 6)
        water_ok = 0 if random.random() < 0.08 + 0.02 * (workload - 5) else 1
        sleep_problem = "none"
        if sleep < 5.6:
            sleep_problem = random.choice(["onset", "awakenings", "uncomfortable", "worry", "schedule"])
        # 6b) CAMERA fatigue signals (30-second face scan). Illustrative values:
        #     PERCLOS = share of time the eyes are at least 80% closed (FHWA 1998 drowsiness measure).
        blink = round(c["blink_base"] * (1 + 0.05 * debt) + random.gauss(0, 1.5))
        perclos = round(clamp(3.5 + 1.6 * debt + random.gauss(0, 1.2), 0.5, 40), 1)
        yawns = max(0, round(random.gauss(0.2 + 0.45 * debt, 0.6)))
        camera_score = clamp(round(100 - 4.5 * (perclos - 3.5) - 4 * yawns), 0, 100)
        # 6c) scripted symptom scenarios for the demo (two cases with opposite outcomes)
        symptom, triage = "", ""
        if c["id"] == "ASTRO-02" and day == 76:    # looks scary, vitals stay within personal range
            symptom, triage = "palpitations + dizziness", "YELLOW path: calm, breathe, re-measure in 10 min"
        if c["id"] == "ASTRO-04" and day == 124:   # vitals clearly outside personal range
            symptom, triage = "chest pain + dizziness", "RED path: Silent Hour (steps + message to Earth)"
            hr, sys_bp, spo2, resp, dia_bp = 118, 92, 91, 24, 58
        # 7) scores 0-100, both relative to the person's own baseline
        slow_pct = (rt - c["rt_base"]) / c["rt_base"] * 100
        measured = clamp(round(100 - 3.2 * slow_pct - 2.0 * lapses), 0, 100)
        felt = alert_self * 10
        gap = felt - measured           # positive = feels better than measured
        # 8) status rule (simple thresholds the team can explain)
        if measured < 55 or gap >= 25: status = "RED"
        elif measured < 75 or gap >= 15: status = "YELLOW"
        else: status = "GREEN"
        if "RED path" in triage: status = "RED"       # symptoms + vitals always win
        if "YELLOW path" in triage and status == "GREEN": status = "YELLOW"
        rows.append([day, c["id"], c["role"], event, workload, round(sleep, 1), round(debt, 1),
                     alert_self, stress_self, mood_self, round(rt), lapses, hr, sys_bp, spo2, temp,
                     blink, perclos, yawns, camera_score, measured, felt, gap, status,
                     symptom, triage, dia_bp, resp, lonely, team, meals, caffeine, water_ok, sleep_problem, "SIMULATED"])

header = ["mission_day", "crew_id", "role", "event", "workload_1to10", "sleep_hours", "sleep_debt_h",
          "alertness_self_1to10", "stress_self_1to10", "mood_self_1to10", "reaction_ms", "lapses",
          "heart_rate_bpm", "systolic_bp", "spo2_pct", "temp_c", "blink_per_min", "perclos_pct", "yawns", "camera_fatigue_score",
          "measured_score", "felt_score", "gap", "status", "symptom", "triage_path", "diastolic_bp", "resp_rate", "loneliness_1to10", "team_1to5", "meals", "caffeine_cups", "water_ok", "sleep_problem", "data_type"]
with open("mission_simulated.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(header); w.writerows(rows)

# quick summary so we can check the numbers make sense
n = len(rows); col = {h: i for i, h in enumerate(header)}
avg = lambda h: sum(r[col[h]] for r in rows) / n
print("rows:", n)
print("avg sleep h:", round(avg("sleep_hours"), 2))
print("share of nights <= 6h:", round(sum(r[col['sleep_hours']] <= 6 for r in rows) / n * 100), "%")
print("avg reaction ms:", round(avg("reaction_ms")), "| avg gap:", round(avg("gap"), 1))
for s in ("GREEN", "YELLOW", "RED"):
    print(s, round(sum(r[col['status']] == s for r in rows) / n * 100), "%")
lo = [r for r in rows if r[col['sleep_hours']] <= 6]; hi = [r for r in rows if r[col['sleep_hours']] > 6]
m = lambda rs, h: round(sum(r[col[h]] for r in rs) / len(rs), 1)
print("sleep<=6h: reaction", m(lo, 'reaction_ms'), "stress", m(lo, 'stress_self_1to10'), "| sleep>6h: reaction", m(hi, 'reaction_ms'), "stress", m(hi, 'stress_self_1to10'))
first = [r for r in rows if r[col['mission_day']] <= 20]; ev = [r for r in rows if r[col['event']]]
print("camera score sleep<=6h:", m(lo,"camera_fatigue_score"), "| >6h:", m(hi,"camera_fatigue_score"))
print("gap first 20 days:", m(first, 'gap'), "| gap on event days:", m(ev, 'gap'))
