"""Tomorrow plan: simple rules that turn today's picture into a few concrete changes for tomorrow.
The plan is a SUGGESTION. Task changes always need the commander. Exercise is moved or lightened, never cancelled."""
b = lambda en, ar: f"{en} || {ar}"


def tomorrow_plan(sleep, stress, focus_low, color, lonely_high, sleep_problem):
    why, items = [], []
    add = lambda t, tag, a, src, cmd=False: items.append({"t": t, "tag": tag, "a": a, "src": src, "cmd": cmd})
    if sleep["status"] != "OK":
        why.append(b(f"last two nights averaged {sleep['avg48']} h of sleep", f"معدل نوم آخر ليلتين {sleep['avg48']} ساعة"))
        add(b("Sleep", "النوم"), b("ADDED", "أُضيف"), b("Bedtime 45 minutes earlier, with a wind-down period before sleep", "موعد النوم أبكر 45 دقيقة، مع وقت تهدئة قبل النوم"),
            b("NASA: designated times for rest and self-care are part of the routine", "NASA: أوقات محددة للراحة والعناية بالنفس ضمن الروتين"))
        add(b("Cabin lighting", "إضاءة المقصورة"), b("ADJUSTED", "عُدّلت"), b("Alerting light in the morning, pre-sleep light in the evening", "ضوء تنبيه صباحاً، وضوء ما قبل النوم مساءً"),
            b("NASA: station LED lights simulate the day-night cycle", "NASA: مصابيح LED في المحطة تحاكي دورة الليل والنهار"))
    if sleep["status"] == "LOW":
        add(b("Nap", "قيلولة"), b("SUGGESTED", "اقتراح"), b("A short afternoon nap if the schedule allows", "قيلولة قصيرة بعد الظهر إن سمح الجدول"),
            b("Prototype suggestion, needs flight-surgeon approval", "اقتراح النموذج الأولي، يحتاج موافقة الطبيب الأرضي"))
    if sleep["status"] != "OK" or color != "GREEN":
        add(b("Exercise", "التمرين"), b("MOVED, LIGHTER", "نُقل · أخف"), b("In the morning with a lighter load. Never cancelled", "في الصباح وبحِمل أخف. لا يُلغى أبداً"),
            b("Daily exercise protects bone and muscle (NASA HRP)", "التمرين اليومي يحمي العظام والعضلات (NASA HRP)"))
    if stress["status"] != "OK":
        why.append(b("high stress today", "توتر عالٍ اليوم"))
        add(b("Breaks", "استراحة"), b("ADDED", "أُضيفت"), b("Two short breaks with a 3-minute breathing exercise", "استراحتان قصيرتان مع تمرين تنفس 3 دقائق"),
            b("IFRC: calming techniques. NASA CONNECT: countermeasures", "IFRC: تقنيات التهدئة · NASA CONNECT: Countermeasures"))
    if focus_low or color != "GREEN":
        if focus_low:
            why.append(b("focus below normal", "تركيز أقل من الطبيعي"))
        add(b("Precise tasks", "المهام الدقيقة"), b("NEEDS COMMANDER", "يحتاج القائد"), b("Postpone the precise task or swap it with a ready crewmate", "تأجيل المهمة الدقيقة أو تبديلها مع زميل جاهز"),
            b("Builds on the idea of NASA Playbook (crew adjusts its own schedule)", "مبني على فكرة NASA Playbook (الطاقم يعدّل جدوله)"), True)
    if lonely_high:
        why.append(b("feeling lonely", "شعور بالوحدة"))
        add(b("Connection", "تواصل"), b("ADDED", "أُضيف"), b("A call with family or a shared activity with the crew", "مكالمة مع العائلة أو نشاط مشترك مع الطاقم"),
            b("NASA CONNECT: Networking and Community", "NASA CONNECT: Networking و Community"))
    if sleep_problem == "worry":
        add(b("Before sleep", "قبل النوم"), b("ADDED", "أُضيف"), b("Write what is on your mind in the journal half an hour before bed", "اكتب ما يشغل بالك في اليوميات قبل النوم بنصف ساعة"),
            b("NASA CONNECT: Countermeasures (journaling)", "NASA CONNECT: Countermeasures (journaling)"))
    if not items:
        add(b("Keep going", "استمر"), b("AS IS", "كما هو"), b("A good day. Keep the same sleep and exercise routine", "يومك جيد. حافظ على نفس روتين النوم والتمرين"),
            b("NASA CONNECT: Needs (routine, exercise, healthy food)", "NASA CONNECT: Needs (روتين، تمرين، أكل صحي)"))
    add(b("Morning check", "فحص الصباح"), b("FIXED", "ثابت"), b("Morning check-in and the 3-minute focus game", "تسجيل الصباح ولعبة التركيز 3 دقائق"), "NASA Reaction Self-Test (PVT-B)")
    return {"why": why, "items": items}
