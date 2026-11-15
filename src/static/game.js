// Focus game: a build of the short Psychomotor Vigilance Test (PVT-B).
// IMPORTANT: all timing happens here, in the browser, with performance.now().
// If the server measured the time, we would be measuring the internet, not the person.
const FALSE_START_MS = 100;            // faster than this is not a real reaction
const TIMEOUT_MS = 30000;              // no answer for 30 s counts as a very slow response

const el = (id) => document.getElementById(id);
let rts = [], falseStarts = 0, shownAt = null, endsAt = 0, waitTimer = null, frame = null, running = false;

function start() {
  if (!el("player").value.trim()) { el("player").focus(); return; }
  el("setup").hidden = true; el("play").hidden = false;
  rts = []; falseStarts = 0; running = true;
  endsAt = performance.now() + GAME_SECONDS * 1000;
  scheduleStimulus(1000 + Math.random() * 3000);
  tickClock();
}

function scheduleStimulus(delay) {            // random wait of 1 to 4 s so the signal cannot be predicted
  shownAt = null; el("stim").textContent = ""; el("hint").textContent = GT.wait;
  waitTimer = setTimeout(showStimulus, delay);
}

function showStimulus() {
  if (!running) return;
  shownAt = performance.now(); el("hint").textContent = GT.tap;
  const run = () => {
    if (shownAt === null) return;
    const ms = performance.now() - shownAt;
    el("stim").textContent = Math.round(ms);
    if (ms >= TIMEOUT_MS) { record(ms); return; }
    frame = requestAnimationFrame(run);
  };
  run();
}

function record(rt) {
  cancelAnimationFrame(frame); shownAt = null;
  if (rt < FALSE_START_MS) falseStarts++; else rts.push(Math.round(rt));
  el("stim").textContent = Math.round(rt); el("hint").textContent = GT.ms;
  next(1000);                                   // show the time for 1 s, then wait 0 to 3 s more
}

function next(feedbackMs) {
  if (performance.now() >= endsAt) { finish(); return; }
  waitTimer = setTimeout(() => scheduleStimulus(Math.random() * 3000), feedbackMs);
}

function tap(e) {
  if (e) e.preventDefault();
  if (!running) return;
  if (shownAt === null) {                       // tapped before the counter: a false start
    if (el("hint").textContent === GT.ms) return;   // ignore taps during the feedback second
    falseStarts++; clearTimeout(waitTimer);
    el("stim").textContent = GT.early; el("hint").textContent = GT.wait;
    next(1000); return;
  }
  record(performance.now() - shownAt);
}

function tickClock() {
  if (!running) return;
  const left = Math.max(0, Math.ceil((endsAt - performance.now()) / 1000));
  el("clock").textContent = GT.left + " " + Math.floor(left / 60) + ":" + String(left % 60).padStart(2, "0");
  if (left <= 0 && shownAt === null) { finish(); return; }
  setTimeout(tickClock, 250);
}

async function finish() {
  if (!running) return; running = false; clearTimeout(waitTimer); cancelAnimationFrame(frame);
  el("play").hidden = true; el("done").hidden = false;
  const body = { player: el("player").value.trim(), self_alertness: Number(el("alert").value) || 5,
                 rts: rts, false_starts: falseStarts, seconds: GAME_SECONDS, task: GAME_TASK };
  const res = await fetch("/api/game", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const d = await res.json(); const s = d.session, st = d.status;
  const tile = (label, value) => `<div class="tile"><span class="small muted">${label}</span><div class="v num">${value}</div></div>`;
  el("tiles").innerHTML = tile(GT.trials, s.n_trials) + tile(GT.mean, (s.mean_rt ?? "-") + " ms") +
    tile(GT.lapses, s.lapses ?? "-") + tile(GT.fs, s.false_starts);
  el("explain").innerHTML = d.explain.map((t, i) => `<li class="${i === 0 ? "" : "muted"}" style="${i === 0 ? "font-size:18px;font-weight:600" : ""}">${t}</li>`).join("");
  if (st.measured10 !== undefined) {
    el("scores").hidden = el("gapbar").hidden = false; el("gm").textContent = st.measured10; el("gf").textContent = st.felt10;
    el("gi1").style.insetInlineStart = st.felt10 * 10 + "%"; el("gi2").style.insetInlineStart = st.measured10 * 10 + "%";
  }
  if (window.Voice) Voice.speak(d.explain.slice(0, 3).join(" "));
}

el("startBtn").addEventListener("click", start);
el("stim").addEventListener("pointerdown", tap);
document.addEventListener("keydown", (e) => { if (e.code === "Space" && running) tap(e); });
