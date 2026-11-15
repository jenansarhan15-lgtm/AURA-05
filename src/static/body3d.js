// 3D body model drawn on a canvas with plain JavaScript (no external library).
// The body is a set of ellipsoids that are painted with ONE colour, so they merge into a single human silhouette.
// Rotating = turning every point around the vertical axis. Organs are drawn inside as a see-through (x-ray) layer.
(function () {
  const cv = document.getElementById("body3d"), g = cv.getContext("2d"), TX = window.BODY_TX || {};
  const E = (x, y, z, rx, ry, rz) => ({ c: [x, y, z], r: [rx, ry === undefined ? rx : ry, rz === undefined ? rx : rz] });
  const mir = s => [s, { c: [-s.c[0], s.c[1], s.c[2]], r: s.r, col: s.col }];
  function capsule(a, b, ra, rb, n) {               // a tapered limb = a row of spheres from point a to point b
    const out = [];
    for (let i = 0; i <= n; i++) { const t = i / n; out.push(E(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t, ra + (rb - ra) * t)); }
    return out;
  }
  const side = arr => arr.flatMap(mir);
  // x = the body's left (viewer's right when facing us), y = up, z = toward the viewer when facing us
  const BODY = [
    E(0, .845, .005, .082, .105, .092), E(0, .79, .02, .06, .06, .065), ...capsule([0, .745, 0], [0, .67, 0], .042, .046, 5),
    E(0, .655, -.01, .13, .04, .06), E(0, .52, 0, .175, .15, .098), E(0, .39, .005, .155, .11, .092), E(0, .27, 0, .135, .1, .085), E(0, .13, 0, .165, .11, .1),
    ...side([E(.075, .07, -.045, .085, .08, .07), E(.2, .615, 0, .062),
      ...capsule([.215, .6, 0], [.25, .36, -.005], .055, .043, 14), ...capsule([.25, .36, -.005], [.275, .12, .03], .043, .03, 14), E(.283, .03, .04, .03, .058, .022),
      ...capsule([.1, .06, 0], [.1, -.4, .005], .08, .055, 20), E(.1, -.43, .012, .053),
      ...capsule([.1, -.46, 0], [.098, -.84, -.005], .054, .034, 18), E(.1, -.58, -.03, .048, .09, .05), E(.098, -.915, .05, .042, .032, .1)]),
  ];
  const O = (shape, col) => Object.assign(shape, { col });
  const ORGANS = [
    ...Array.from({ length: 15 }, (_, i) => O(E(0, .7 - i * .044, -.062, .014), "#B9C7DA")),          // spine
    O(E(0, .875, 0, .062, .055, .07), "#E7A3AC"),                                                      // brain
    ...mir(O(E(.078, .525, 0, .058, .105, .058), "#F0B4BD")),                                          // lungs
    O(E(.028, .5, .035, .04, .05, .036), "#CF474D"),                                                   // heart
    O(E(-.06, .375, .02, .07, .04, .05), "#B46A52"), O(E(.055, .36, .03, .045, .04, .038), "#E6A46C"), // liver, stomach
    O(E(0, .22, .03, .095, .075, .05), "#EDB98F"),                                                     // intestines
    ...mir(O(E(.065, .3, -.05, .022, .036, .02), "#A5566B")),                                          // kidneys
  ];
  // clickable points on the surface, each tied to a region id in knowledge.json
  const H = (id, x, y, z) => ({ id, p: [x, y, z] });
  const both = (id, x, y, z) => [H(id, x, y, z), H(id, -x, y, z)];
  const SPOTS = [
    H("head_front", 0, .905, .086), H("head_back", 0, .87, -.088), ...both("eyes", .03, .855, .09), ...both("ear", .084, .84, 0),
    H("mouth", 0, .793, .086), H("throat", 0, .705, .044), H("neck_back", 0, .71, -.046),
    H("chest_left", .075, .53, .096), H("chest_right", -.075, .53, .096),
    H("abd_upper", .02, .375, .096), H("abd_right", -.09, .27, .072), H("abd_lower", 0, .16, .1),
    ...both("flank", .11, .29, -.062), H("upper_back", 0, .53, -.099), H("lower_back", 0, .23, -.087),
    ...both("shoulder", .21, .63, .022), ...both("elbow", .252, .36, -.034), ...both("hand", .283, .04, .046),
    ...both("hip", .15, .1, .042), ...both("thigh", .1, -.18, .076), ...both("knee", .1, -.43, .062),
    ...both("calf", .1, -.6, -.06), ...both("foot", .098, -.9, .1),
  ];
  let angle = 0, auto = true, drag = null, hover = null, W = 0, Hh = 0, shown = [], selected = null, organs = true;
  const names = window.REGION_NAMES || {};

  function size() { const r = cv.getBoundingClientRect(), d = window.devicePixelRatio || 1; W = r.width; Hh = r.height; cv.width = W * d; cv.height = Hh * d; g.setTransform(d, 0, 0, d, 0, 0); }
  function project(p) {                               // rotate around the vertical axis, then flatten to the screen
    const s = Math.sin(angle), c = Math.cos(angle), x = p[0] * c + p[2] * s, z = -p[0] * s + p[2] * c, k = Hh * .46;
    return { x: W / 2 + x * k, y: Hh * .5 - p[1] * k, z, k };
  }
  function ell(sh, grow, shrink) {
    const s = Math.sin(angle), c = Math.cos(angle), q = project(sh.c);
    const w = Math.hypot(sh.r[0] * c, sh.r[2] * s) * q.k * (shrink || 1) + (grow || 0), h = sh.r[1] * q.k * (shrink || 1) + (grow || 0);
    g.beginPath(); g.ellipse(q.x, q.y, Math.max(.5, w), Math.max(.5, h), 0, 0, 7); return q;
  }
  function draw() {
    g.clearRect(0, 0, W, Hh);
    const fl = project([0, -.975, 0]);                // floor rings
    g.lineWidth = 1;
    for (const [rr, a] of [[.36, .5], [.27, .8]]) { g.strokeStyle = `rgba(11,140,153,${a * .5})`; g.beginPath(); g.ellipse(fl.x, fl.y, rr * fl.k, rr * fl.k * .2, 0, 0, 7); g.stroke(); }
    // 1) outline: every shape slightly larger, in the line colour   2) fill: every shape in one colour -> one silhouette
    g.fillStyle = "#5F86BA"; for (const sh of BODY) { ell(sh, 1.4); g.fill(); }
    const grad = g.createLinearGradient(W / 2 - Hh * .16, 0, W / 2 + Hh * .16, 0);
    grad.addColorStop(0, "#EAF2FC"); grad.addColorStop(.55, "#D4E3F6"); grad.addColorStop(1, "#BDD2EE");
    g.fillStyle = grad; for (const sh of BODY) { ell(sh); g.fill(); }
    if (organs) {
      const list = ORGANS.map(o => ({ o, z: project(o.c).z })).sort((a, b) => a.z - b.z);
      for (const { o, z } of list) { g.globalAlpha = z < -.02 ? .5 : .88; g.fillStyle = o.col; ell(o); g.fill(); g.globalAlpha = 1; g.strokeStyle = "rgba(15,30,61,.18)"; g.lineWidth = .8; g.stroke(); }
    }
    shown = [];
    const t = performance.now() / 600;
    for (const sp of SPOTS) {
      const q = project(sp.p); if (q.z < -.015) continue;         // only points on the side facing the viewer
      shown.push({ sp, q });
      const on = sp.id === selected, hv = hover && sp.id === hover.id, r = on ? 9 : hv ? 8.5 : 6;
      g.beginPath(); g.arc(q.x, q.y, r + 4 + Math.sin(t + q.y) * 1.5, 0, 7); g.fillStyle = on ? "rgba(185,122,10,.22)" : "rgba(11,140,153,.16)"; g.fill();
      g.beginPath(); g.arc(q.x, q.y, r, 0, 7); g.fillStyle = on ? "#D99A1C" : "#0B8C99"; g.fill(); g.strokeStyle = "#fff"; g.lineWidth = 2; g.stroke();
    }
    for (const { sp, q } of shown) {                               // labels on top of all points
      const on = sp.id === selected, hv = hover === sp; if (!(hv || (on && !hover))) continue;
      const label = names[sp.id] || sp.id; g.font = "600 14px 'IBM Plex Sans', 'IBM Plex Sans Arabic', sans-serif";
      const tw = g.measureText(label).width + 18, lx = Math.min(W - tw - 6, Math.max(6, q.x - tw / 2)), ly = Math.max(4, q.y - 44);
      g.fillStyle = "#0F1E3D"; g.beginPath(); g.roundRect(lx, ly, tw, 26, 7); g.fill();
      g.fillStyle = "#fff"; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText(label, lx + tw / 2, ly + 13.5);
      if (!hv) break;
    }
    const deg = ((angle * 180 / Math.PI) % 360 + 360) % 360;
    document.getElementById("facing").textContent = deg < 45 || deg > 315 ? TX.front : deg > 135 && deg < 225 ? TX.back : TX.sideview;
    document.getElementById("deg").textContent = Math.round(deg) + "°";
  }
  function loop() { if (auto && !drag) angle += .005; draw(); requestAnimationFrame(loop); }
  function at(e) {
    const r = cv.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top; let best = null, bd = 18;
    for (const s of shown) { const d = Math.hypot(s.q.x - x, s.q.y - y); if (d < bd) { bd = d; best = s.sp; } }
    return best;
  }
  cv.addEventListener("pointerdown", e => { drag = { x: e.clientX, a: angle, moved: false }; cv.setPointerCapture(e.pointerId); });
  cv.addEventListener("pointermove", e => {
    if (drag) { const dx = e.clientX - drag.x; if (Math.abs(dx) > 4) { drag.moved = true; auto = false; paint(); } angle = drag.a + dx * .012; }
    else { hover = at(e); cv.style.cursor = hover ? "pointer" : "grab"; }
  });
  cv.addEventListener("pointerup", e => { if (drag && !drag.moved) { const sp = at(e); if (sp) { auto = false; paint(); window.pickRegion(sp.id); } } drag = null; });
  cv.addEventListener("pointerleave", () => { hover = null; });
  function paint() { document.getElementById("autoBtn").textContent = auto ? TX.stop : TX.auto; document.getElementById("organBtn").textContent = organs ? TX.organs_on : TX.organs_off; }
  document.getElementById("autoBtn").onclick = () => { auto = !auto; paint(); };
  document.getElementById("organBtn").onclick = () => { organs = !organs; paint(); };
  document.querySelectorAll("[data-turn]").forEach(b => b.onclick = () => { auto = false; paint(); angle = Number(b.dataset.turn) * Math.PI / 180; });
  window.body3d = { select(id) { selected = id; } };
  window.addEventListener("resize", size); size(); paint(); loop();
})();
