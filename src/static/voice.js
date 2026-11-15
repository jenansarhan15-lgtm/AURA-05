// Voice layer (prototype). Speaking = the browser's speechSynthesis. Listening = the browser's SpeechRecognition (Chrome / Edge).
// Understanding uses simple KEYWORDS from knowledge.json, not a trained model, so every match can be explained.
// The language follows the page language (English or Arabic).
const Voice = (function () {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const AR = document.documentElement.lang === "ar";
  let speakerOn = true;
  try { speakerOn = localStorage.getItem("aura_speaker") !== "off"; } catch (e) {}
  const norm = t => (t || "").toLowerCase().replace(/[ً-ْـ]/g, "").replace(/[أإآ]/g, "ا").replace(/ة/g, "ه").replace(/ى/g, "ي").replace(/[؟?.,!،']/g, " ").replace(/\s+/g, " ").trim();
  const has = (text, words) => { const t = " " + norm(text) + " "; return words.some(w => { const n = norm(w); return t.includes(" " + n + " ") || (n.length > 3 && /[؀-ۿ]/.test(n) && t.includes(n)); }); };
  const voice = () => window.speechSynthesis ? speechSynthesis.getVoices().find(v => v.lang.toLowerCase().startsWith(AR ? "ar" : "en")) : null;
  if (window.speechSynthesis) { speechSynthesis.getVoices(); speechSynthesis.onvoiceschanged = () => document.dispatchEvent(new Event("voices")); }
  function speak(text, done) {
    const v = voice();
    if (!speakerOn || !v) { if (done) setTimeout(done, 350); return; }      // no voice for this language: text only, keep going
    const u = new SpeechSynthesisUtterance(text); u.lang = v.lang; u.voice = v; u.rate = .95;
    let fired = false; const fin = () => { if (!fired) { fired = true; if (done) done(); } };
    u.onend = fin; u.onerror = fin; setTimeout(fin, 2500 + text.length * 110);      // safety: never get stuck
    speechSynthesis.cancel(); speechSynthesis.speak(u);
  }
  function stop() { if (window.speechSynthesis) speechSynthesis.cancel(); }
  function listen(onText, onFail) {                    // one short phrase, then stop
    if (!SR) { onFail && onFail("unsupported"); return null; }
    const r = new SR(); r.lang = AR ? "ar-JO" : "en-US"; r.interimResults = false; r.maxAlternatives = 3;
    let got = false;
    r.onresult = e => { got = true; onText([...e.results[0]].map(a => a.transcript).join(" | ")); };
    r.onerror = e => { if (!got) { got = true; onFail && onFail(e.error); } };
    r.onend = () => { if (!got) onFail && onFail("silence"); };
    try { r.start(); } catch (e) { onFail && onFail("busy"); }
    return r;
  }
  function setSpeaker(on) { speakerOn = on; try { localStorage.setItem("aura_speaker", on ? "on" : "off"); } catch (e) {} if (!on) stop(); }
  return { speak, stop, listen, has, norm, supported: !!SR, hasVoice: () => !!voice(), get speakerOn() { return speakerOn; }, setSpeaker };
})();
