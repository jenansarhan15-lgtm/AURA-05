"""Triage engine: decides GREEN / YELLOW / RED and explains why. Texts are 'English || Arabic'.

Safety rules (fixed):
 A. Symptoms + vital signs decide RED. Nothing can lower a RED.
 B. Sleep, stress and the focus game are CONTRIBUTING factors: they can raise GREEN to YELLOW only.
 C. The system assesses and triages like a nurse. It does not give a medical diagnosis, a drug or a dose.
 D. YELLOW always ends with a re-measure. No improvement means escalate.
"""
from .baseline import z_score
from .news2 import news2

LABELS = {"resp_rate": "Breathing rate || معدل التنفس", "spo2_pct": "Oxygen saturation || تشبع الأكسجين",
          "systolic_bp": "Systolic pressure || الضغط الانقباضي", "heart_rate_bpm": "Pulse || النبض", "temp_c": "Temperature || الحرارة"}
both = lambda en, ar: f"{en} || {ar}"
part = lambda s, i: s.split(" || ")[i]


def triage(chosen, answers_yes, vitals, alert, base, sleep, stress, focus_low, KB, R):
    """chosen = list of symptom ids; answers_yes = list of (symptom_id, question_index) answered YES."""
    S = KB["symptoms"]
    red, strong, mild, factors = [], [], [], []

    # ---- A. safety gate ----
    for sid in chosen:
        if S[sid].get("always_red"):
            red.append(both("Danger symptom: " + part(S[sid]["name"], 0), "عَرَض خطر: " + part(S[sid]["name"], 1)))
    for sid, qi in answers_yes:
        q, level = S[sid]["q"][qi]
        (red if level == "red" else strong).append(both(part(q, 0) + " Yes", part(q, 1) + " نعم"))
    if not alert:
        red.append(both("Confused or not fully alert", "تشوّش أو ليس بكامل وعيه"))
    n = news2(vitals, R)
    if n["total"] >= R["news2_red_total"]:
        red.append(both(f"NEWS2 total = {n['total']} (5 or more)", f"مجموع NEWS2 = {n['total']} (5 أو أكثر)"))
    elif n["max_single"] == 3:
        bad = [LABELS[k] for k, p in n["parts"].items() if p == 3]
        strong.append(both("One vital sign in the red band: " + ", ".join(part(b, 0) for b in bad),
                           "قياس واحد في المنطقة الحمراء: " + "، ".join(part(b, 1) for b in bad)))
    elif n["total"] >= R["news2_yellow_total"]:
        mild.append(both(f"NEWS2 total = {n['total']}", f"مجموع NEWS2 = {n['total']}"))

    # ---- personal baseline: far from HIS or HER OWN normal ----
    for key in ("heart_rate_bpm", "systolic_bp", "spo2_pct", "temp_c"):
        if key in base and vitals.get(key) is not None and abs(z_score(float(vitals[key]), base[key])) >= 3:
            mild.append(both(part(LABELS[key], 0) + " is far from the personal baseline", part(LABELS[key], 1) + " بعيد عن الطبيعة الشخصية"))

    # ---- B. contributing factors (can only raise to YELLOW) ----
    if sleep["status"] == "LOW":
        factors.append(both(f"Short sleep (last two nights average {sleep['avg48']} h, sleep debt {sleep['debt7']} h)",
                            f"نوم قليل (معدل آخر ليلتين {sleep['avg48']} ساعة، دَين النوم {sleep['debt7']} ساعة)"))
    elif sleep["status"] == "WATCH":
        factors.append(both(f"Less sleep than needed (last night {sleep['last']} h)", f"نوم أقل من المطلوب (آخر ليلة {sleep['last']} ساعة)"))
    if stress["status"] == "PERSISTENT":
        factors.append(both("High stress for several days", "توتر عالٍ منذ عدة أيام"))
    elif stress["status"] == "HIGH":
        factors.append(both("High stress", "توتر عالٍ"))
    if focus_low:
        factors.append(both("Focus below personal normal in the last test", "تركيز أقل من الطبيعي في آخر اختبار"))
    for sid in chosen:
        if S[sid].get("min") == "YELLOW":
            mild.append(both(part(S[sid]["name"], 0) + " always needs a re-measure", part(S[sid]["name"], 1) + " يحتاج إعادة قياس دائماً"))

    emergency = n["total"] >= R["news2_emergency_total"]
    if red:
        color, level, reasons = "RED", "RED", red + strong
        msg = both("Act now. Start the steps. The summary is sent to Earth automatically.", "تصرّف الآن. ابدأ الخطوات. الملخص يُرسَل للأرض تلقائياً.")
    elif strong:
        color, level, reasons = "YELLOW", "YELLOW_STRONG", strong + mild
        msg = both("Not an emergency now, but it needs a check every hour. Earth has been notified to prepare.",
                   "ليس طارئاً الآن، لكن يحتاج متابعة كل ساعة. أُبلغت الأرض لتستعد.")
    elif mild or (chosen and factors):
        color, level, reasons = "YELLOW", "YELLOW", mild
        msg = (both("Short sleep and stress may be contributing to these symptoms. Calm down and re-measure in 10 minutes.",
                    "قلة النوم والتوتر قد يكونان عاملاً مساهماً في هذه الأعراض. لنهدأ ونُعِد القياس بعد 10 دقائق.")
               if factors else both("Calm down and re-measure in 10 minutes.", "لنهدأ ونُعِد القياس بعد 10 دقائق."))
    else:
        color, level, reasons = "GREEN", "GREEN", []
        msg = both("No danger signs now. Follow the simple steps and keep watching.", "لا توجد علامات خطر الآن. اتبع الخطوات البسيطة وراقب.")
    return {"color": color, "level": level, "reasons": reasons, "factors": factors, "message": msg,
            "news2": n, "emergency": emergency, "monitor": R["monitor"][level]}
