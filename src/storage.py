"""Storage: ONE SQLite file (data/aegis.db) on the machine running Flask.
When hosted, browser submissions go to that server. No real Earth medical link exists.
Every value carries its source:
SIM (simulated device feed), MANUAL (typed by the astronaut), REAL (team game sessions), DEVICE (future sensor)."""
import csv, json, os, sqlite3, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
DB = os.path.join(DATA, "aegis.db")
CSV = os.path.join(DATA, "mission_simulated.csv")
TEXT_COLS = {"crew_id", "role", "event", "status", "symptom", "triage_path", "sleep_problem", "data_type"}


def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    """Create tables, and load the simulated mission the first time the app runs."""
    if not os.path.exists(CSV):
        subprocess.run([sys.executable, "generate_data.py"], cwd=DATA, check=True, stdout=subprocess.DEVNULL)
    with open(CSV, newline="") as f:
        rows = list(csv.DictReader(f))
    cols = list(rows[0].keys())
    with conn() as c:
        c.execute("CREATE TABLE IF NOT EXISTS daily_log(" +
                  ",".join(f"{k} {'TEXT' if k in TEXT_COLS else 'REAL'}" for k in cols) + ")")
        c.execute("""CREATE TABLE IF NOT EXISTS game_sessions(id INTEGER PRIMARY KEY, player TEXT, crew_id TEXT,
            mission_day INTEGER, task TEXT, played_at REAL, self_alertness INTEGER, n_trials INTEGER, mean_rt REAL,
            mean_speed REAL, slowest10_speed REAL, lapses INTEGER, false_starts INTEGER, valid INTEGER,
            raw_rts TEXT, data_type TEXT)""")
        c.execute("CREATE TABLE IF NOT EXISTS checkins(crew_id TEXT, mission_day INTEGER, kind TEXT, data TEXT, ts REAL)")
        c.execute("CREATE TABLE IF NOT EXISTS manual_vitals(crew_id TEXT, mission_day INTEGER, data TEXT, ts REAL)")
        c.execute("""CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, ts REAL, crew_id TEXT, mission_day INTEGER,
            kind TEXT, color TEXT, title TEXT, detail TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS silent(id INTEGER PRIMARY KEY, crew_id TEXT, mission_day INTEGER,
            started REAL, location TEXT, speed REAL, packet TEXT)""")
        c.execute("CREATE TABLE IF NOT EXISTS silent_log(silent_id INTEGER, ts REAL, kind TEXT, text TEXT)")
        if c.execute("SELECT COUNT(*) FROM daily_log").fetchone()[0] == 0:
            for r in rows:
                vals = [r[k] if k in TEXT_COLS else float(r[k]) for k in cols]
                c.execute(f"INSERT INTO daily_log VALUES({','.join('?' * len(cols))})", vals)


def q(sql, args=()):
    with conn() as c:
        return [dict(r) for r in c.execute(sql, args)]


def run(sql, args=()):
    with conn() as c:
        return c.execute(sql, args).lastrowid


def crew_list():
    return q("SELECT DISTINCT crew_id, role FROM daily_log ORDER BY crew_id")


def crew_rows(crew_id):
    return q("SELECT * FROM daily_log WHERE crew_id=? ORDER BY mission_day", (crew_id,))


# ---- check-ins and manual vitals (MANUAL source) ----
def save_checkin(crew_id, day, kind, data):
    run("DELETE FROM checkins WHERE crew_id=? AND mission_day=? AND kind=?", (crew_id, day, kind))
    run("INSERT INTO checkins VALUES(?,?,?,?,?)", (crew_id, day, kind, json.dumps(data, ensure_ascii=False), time.time()))


def get_checkins(crew_id, day):
    return {r["kind"]: json.loads(r["data"]) for r in
            q("SELECT * FROM checkins WHERE crew_id=? AND mission_day=?", (crew_id, day))}


def save_manual_vitals(crew_id, day, data):
    run("DELETE FROM manual_vitals WHERE crew_id=? AND mission_day=?", (crew_id, day))
    if data:
        run("INSERT INTO manual_vitals VALUES(?,?,?,?)", (crew_id, day, json.dumps(data), time.time()))


def get_manual_vitals(crew_id, day):
    r = q("SELECT data FROM manual_vitals WHERE crew_id=? AND mission_day=?", (crew_id, day))
    return json.loads(r[0]["data"]) if r else {}


# ---- events: the saved-sessions log ----
def add_event(crew_id, day, kind, color, title, detail=None):
    return run("INSERT INTO events(ts, crew_id, mission_day, kind, color, title, detail) VALUES(?,?,?,?,?,?,?)",
               (time.time(), crew_id, day, kind, color, title, json.dumps(detail or {}, ensure_ascii=False)))


def get_event(eid):
    r = q("SELECT * FROM events WHERE id=?", (eid,))
    if r:
        r[0]["detail"] = json.loads(r[0]["detail"])
    return r[0] if r else None


def events(crew_id=None, day=None, kind=None, limit=200):
    sql, args = "SELECT * FROM events WHERE 1=1", []
    for col, val in (("crew_id", crew_id), ("mission_day", day), ("kind", kind)):
        if val is not None:
            sql += f" AND {col}=?"; args.append(val)
    out = q(sql + " ORDER BY id DESC LIMIT ?", args + [limit])
    for r in out:
        r["detail"] = json.loads(r["detail"])
    return out


# ---- focus game ----
def save_game(player, crew_id, day, task, self_alertness, s, rts, data_type):
    run("""INSERT INTO game_sessions(player, crew_id, mission_day, task, played_at, self_alertness, n_trials, mean_rt,
           mean_speed, slowest10_speed, lapses, false_starts, valid, raw_rts, data_type) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (player, crew_id, day, task, time.time(), self_alertness, s.get("n_trials", 0), s.get("mean_rt"),
         s.get("mean_speed"), s.get("slowest10_speed"), s.get("lapses"), s.get("false_starts"),
         int(s.get("valid", False)), json.dumps(rts), data_type))


def player_sessions(player):
    return q("SELECT * FROM game_sessions WHERE player=? AND valid=1 ORDER BY played_at", (player,))


def games_today(crew_id, day):
    return q("SELECT * FROM game_sessions WHERE crew_id=? AND mission_day=? ORDER BY played_at", (crew_id, day))


def all_games():
    return q("SELECT * FROM game_sessions ORDER BY played_at DESC LIMIT 100")


# ---- Silent Hour ----
def start_silent(crew_id, day, location, speed, packet):
    return run("INSERT INTO silent(crew_id, mission_day, started, location, speed, packet) VALUES(?,?,?,?,?,?)",
               (crew_id, day, time.time(), location, speed, json.dumps(packet, ensure_ascii=False)))


def get_silent(sid):
    r = q("SELECT * FROM silent WHERE id=?", (sid,))
    if r:
        r[0]["packet"] = json.loads(r[0]["packet"])
    return r[0] if r else None


def silent_log_add(sid, kind, text):
    run("INSERT INTO silent_log VALUES(?,?,?,?)", (sid, time.time(), kind, text))


def silent_log(sid):
    return q("SELECT * FROM silent_log WHERE silent_id=? ORDER BY ts", (sid,))
