(() => {
  "use strict";
  const $ = (s) => document.querySelector(s);
  const LOCALES = { en: "en-IN", hi: "hi-IN", gu: "gu-IN" };
  const LANG_NAMES = { en: "English", hi: "हिन्दी", gu: "ગુજરાતી" };
  const SPEAK = {
    en: { output: "Output is", error: "There is an error", line: "on line", noOutput: "The program printed nothing" },
    hi: { output: "आउटपुट है", error: "त्रुटि है", line: "लाइन", noOutput: "प्रोग्राम ने कुछ प्रिंट नहीं किया" },
    gu: { output: "આઉટપુટ છે", error: "ભૂલ છે", line: "લાઇન", noOutput: "પ્રોગ્રામે કંઈ પ્રિન્ટ કર્યું નથી" }
  };
  const STAGES = ["lexer", "parser", "semantic", "ir", "codegen", "run"];
  const STAGE_LABELS = ["Lexer", "Parser", "Semantic", "IR", "C code", "Run"];
  const TABS = [["output", "Output"], ["tokens", "Tokens"], ["ast", "AST"], ["ir", "IR"], ["c", "C code"], ["compare", "Compare"]];

  const CUSTOM = "__custom__";
  const state = { lang: "en", keywords: null, examples: [], phraseMap: null, listening: false, last: null, loaded: "", prevExample: "" };
  const code = $("#code");

  // ---------- helpers ----------
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  let toastTimer;
  function toast(msg) {
    const t = $("#toast");
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove("show"), 3200);
  }

  async function api(path, body) {
    const res = await fetch(path, {
      method: body ? "POST" : "GET",
      headers: body ? { "Content-Type": "application/json" } : {},
      body: body ? JSON.stringify(body) : undefined
    });
    if (!res.ok) {
      let msg = "Server error";
      try { msg = (await res.json()).error || msg; } catch (e) { /* ignore */ }
      throw new Error(msg);
    }
    return res.json();
  }

  function insertAtCursor(text) {
    const start = code.selectionStart, end = code.selectionEnd;
    const before = code.value.slice(0, start);
    const needSpace = before && !/[\s(]$/.test(before) && !/^[\s;,)]/.test(text);
    const ins = (needSpace ? " " : "") + text;
    code.value = before + ins + code.value.slice(end);
    code.selectionStart = code.selectionEnd = start + ins.length;
    code.focus();
    markEdited();
  }

  // When the user changes an example, show that it is now their own program.
  function markEdited() {
    const sel = $("#example");
    if (sel.value !== CUSTOM && code.value !== state.loaded) {
      sel.value = CUSTOM;
      state.prevExample = CUSTOM;
    }
  }

  function goToLine(line) {
    const lines = code.value.split("\n");
    if (!line || line > lines.length) return;
    let start = 0;
    for (let i = 0; i < line - 1; i++) start += lines[i].length + 1;
    code.focus();
    code.setSelectionRange(start, start + lines[line - 1].length);
  }

  // ---------- tabs & pipeline ----------
  function buildTabs() {
    const box = $("#tabs");
    box.innerHTML = TABS.map(([id, label], i) =>
      `<button role="tab" data-tab="${id}" class="${i === 0 ? "active" : ""}">${label}</button>`).join("");
    box.addEventListener("click", (e) => {
      const b = e.target.closest("button[data-tab]");
      if (b) showTab(b.dataset.tab);
    });
  }
  function showTab(id) {
    document.querySelectorAll("#tabs button").forEach((b) => b.classList.toggle("active", b.dataset.tab === id));
    TABS.forEach(([t]) => { $("#panel-" + t).hidden = t !== id; });
  }
  function renderPipeline(r) {
    const idx = r ? STAGES.indexOf(r.stage) : -1;
    $("#pipeline").innerHTML = STAGE_LABELS.map((label, i) => {
      let cls = "pill";
      if (r && i < idx) cls += " done";
      if (r && i === idx) cls += r.ok ? " done" : " fail";
      const mark = cls.includes("done") ? "✓ " : cls.includes("fail") ? "✗ " : "";
      return `<span class="${cls}">${mark}${label}</span>`;
    }).join("");
  }

  // ---------- rendering a compile result ----------
  function render(r) {
    state.last = r;
    renderPipeline(r);

    const ul = $("#errors");
    if (r.errors.length) {
      ul.hidden = false;
      ul.innerHTML = r.errors.map((e) =>
        `<li data-line="${e.line || 0}"><b>${esc(e.kind)}</b>${e.line ? ` — line ${e.line}, col ${e.col}` : ""}: ${esc(e.message)}</li>`).join("");
    } else {
      ul.hidden = true;
      ul.innerHTML = "";
    }

    const out = $("#outputBox");
    if (r.ok) out.textContent = r.output === "" ? "(program printed nothing)" : r.output;
    else if (r.output) out.textContent = r.output;
    else out.textContent = "No output — fix the error(s) listed above.";

    $("#normBox").textContent = r.normalized || "";
    $("#tokTable").innerHTML = "<tr><th>Line</th><th>Col</th><th>Written as</th><th>Token</th><th>Lang</th></tr>" +
      r.tokens.map((t) => `<tr><td>${t.line}</td><td>${t.col}</td><td>${esc(t.lexeme)}</td><td>${esc(t.token)}</td><td>${esc(t.lang)}</td></tr>`).join("");
    $("#astBox").textContent = r.ast || "(not reached)";
    $("#irBox").textContent = r.ir.length ? r.ir.map((l, i) => String(i + 1).padStart(2, " ") + "  " + l).join("\n") : "(not reached)";
    $("#cBox").textContent = r.c_code || "(not reached)";
    showTab("output");
  }

  async function runProgram() {
    const btn = $("#run");
    btn.disabled = true;
    try {
      const r = await api("/api/compile", { source: code.value, lang: state.lang, policy: $("#policy").value });
      render(r);
      if ($("#autoSpeak").checked) speakResult(r);
    } catch (e) { toast(e.message); } finally { btn.disabled = false; }
  }

  async function runCompare() {
    const btn = $("#compare");
    btn.disabled = true;
    try {
      const r = await api("/api/compare", { source: code.value, lang: state.lang, policy: "strict" });
      const box = $("#compareBox");
      if (!r.ok) {
        box.innerHTML = `<p>Cannot compare: ${esc(r.error)}</p>`;
      } else {
        const badge = (ok, label) => `<span class="badge ${ok ? "good" : "bad"}">${ok ? "✓" : "✗"} ${label}</span>`;
        box.innerHTML =
          `<div class="badges">${badge(r.same_tokens, "Same tokens")}${badge(r.same_ir, "Same IR")}${badge(r.same_output, "Same output")}</div>` +
          `<div class="cmp">` + ["en", "hi", "gu"].map((l) => {
            const x = r.langs[l];
            return `<div><h3>${LANG_NAMES[l]}</h3><pre>${esc(x.source)}</pre>` +
              `<p class="label">Output</p><pre>${esc(x.errors.length ? x.errors.join("\n") : x.output)}</pre></div>`;
          }).join("") + `</div>` +
          `<p class="label" style="margin-top:12px">Shared intermediate code:</p><pre>${esc(r.langs.en.ir.join("\n") || "(none)")}</pre>`;
      }
      showTab("compare");
    } catch (e) { toast(e.message); } finally { btn.disabled = false; }
  }

  // ---------- language handling ----------
  function refreshLangUi() {
    state.phraseMap = MLCSpeech.buildPhraseMap(state.keywords, state.lang);
    const words = state.keywords[state.lang];
    $("#chips").innerHTML = Object.values(words).map((w) => `<span class="chip" title="click to insert" style="cursor:pointer">${esc(w)}</span>`).join("");
    $("#lang").value = state.lang;
    document.documentElement.lang = state.lang;
    updateVoiceStatus();
    if (state.listening) { stopListening(); startListening(); }
  }

  async function onLangChange() {
    const next = $("#lang").value;
    if (next === state.lang) return;
    state.lang = next;
    if ($("#example").value !== CUSTOM) {
      loadExample();                         // ready-made program: load it in the new language
    } else if (code.value.trim()) {
      try {                                  // own program: convert its keywords
        const r = await api("/api/translate", { source: code.value, lang: next, policy: "mixed" });
        if (r.ok) { code.value = r.source; toast("Keywords converted to " + LANG_NAMES[next]); }
        else toast("Could not convert keywords — fix lexical errors first");
      } catch (e) { toast(e.message); }
    }
    refreshLangUi();
  }

  function buildExampleSelect() {
    const groups = {};
    state.examples.forEach((x) => (groups[x.category] = groups[x.category] || []).push(x));
    let html = `<option value="${CUSTOM}">✏️ Write my own program</option>`;
    Object.entries(groups).forEach(([cat, items]) => {
      html += `<optgroup label="${esc(cat)}">` +
        items.map((x) => `<option value="${esc(x.id)}">${esc(x.title)}</option>`).join("") + "</optgroup>";
    });
    $("#example").innerHTML = html;
  }

  function starter(lang) {
    const k = state.keywords[lang];
    return `// Write your program here\n${k.INT} a = 10;\n${k.PRINT} "Value : ", a;\n`;
  }

  function loadExample() {
    const id = $("#example").value;
    if (id === CUSTOM) {
      code.value = state.loaded = starter(state.lang);
      code.focus();
    } else {
      const ex = state.examples.find((x) => x.id === id);
      if (ex) code.value = state.loaded = ex[state.lang];
    }
    state.prevExample = id;
  }

  function onExampleChange() {
    const unsaved = code.value.trim() && code.value !== state.loaded;
    if (unsaved && !confirm("Replace the code in the editor?")) {
      $("#example").value = state.prevExample;
      return;
    }
    loadExample();
  }

  // ---------- text to speech ----------
  const hasTTS = "speechSynthesis" in window;
  function pickVoice(lang) {
    if (!hasTTS) return null;
    const loc = LOCALES[lang].toLowerCase();
    const vs = speechSynthesis.getVoices();
    return vs.find((v) => v.lang.replace("_", "-").toLowerCase() === loc) ||
           vs.find((v) => v.lang.toLowerCase().startsWith(lang)) || null;
  }
  function updateVoiceStatus() {
    const el = $("#voiceStatus");
    if (!hasTTS) { el.textContent = "🔊 Text-to-speech is not supported in this browser."; return; }
    const v = pickVoice(state.lang);
    el.textContent = v ? `🔊 Voice for ${LANG_NAMES[state.lang]}: ${v.name} (${v.lang})`
      : `🔊 No ${LANG_NAMES[state.lang]} voice installed on this device — English voice will be used for plain text/numbers.`;
  }
  function speak(text, lang) {
    if (!hasTTS) { toast("Text-to-speech is not supported in this browser"); return; }
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = LOCALES[lang];
    u.voice = pickVoice(lang) || null;
    u.rate = 0.95;
    speechSynthesis.speak(u);
  }
  function speakResult(r) {
    if (!r) { toast("Run a program first"); return; }
    // use the selected language only if a voice for it exists, otherwise fall back to English
    const lang = pickVoice(state.lang) ? state.lang : "en";
    const L = SPEAK[lang];
    let text;
    if (r.ok) {
      const body = r.output.trim().replace(/\n+/g, ". ");
      text = body ? `${L.output}: ${body}` : L.noOutput;
    } else {
      const e = r.errors[0];
      text = `${L.error}. ${e.line ? `${L.line} ${e.line}. ` : ""}${e.message}`;
    }
    if (lang === "en" && /[^\x00-\x7F]/.test(text)) toast("No voice for " + LANG_NAMES[state.lang] + " — non-English text may not be read");
    speak(text, lang);
  }

  // ---------- speech to text ----------
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  let rec = null;

  function setMicUi(on) {
    $("#mic").classList.toggle("listening", on);
    $("#mic").textContent = on ? "⏹ Stop" : "🎤 Speak";
    $("#micStatus").textContent = on ? `🎙 Listening in ${LANG_NAMES[state.lang]} (${LOCALES[state.lang]}) … say “semicolon”, “new line”, “run”` : "";
    if (!on) $("#interim").textContent = "";
  }

  function startListening() {
    if (!SR) { toast("Speech recognition is not supported here — use Chrome, Edge or Safari"); return; }
    rec = new SR();
    rec.lang = LOCALES[state.lang];
    rec.continuous = true;
    rec.interimResults = true;
    rec.onresult = (e) => {
      let interim = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const res = e.results[i];
        const text = res[0].transcript;
        if (!res.isFinal) { interim += text; continue; }
        const cmd = MLCSpeech.detectCommand(text);
        if (cmd === "run") { toast("Voice command: run"); runProgram(); }
        else if (cmd === "clear") { code.value = ""; markEdited(); toast("Voice command: clear"); }
        else insertAtCursor(MLCSpeech.processSpeech(text, state.phraseMap));
      }
      $("#interim").textContent = interim;
    };
    rec.onerror = (e) => {
      if (e.error === "not-allowed" || e.error === "service-not-allowed") {
        toast("Microphone permission denied — allow it in the browser address bar");
        state.listening = false; setMicUi(false);
      } else if (e.error === "language-not-supported") {
        toast("This browser cannot recognise " + LANG_NAMES[state.lang]);
        state.listening = false; setMicUi(false);
      } else if (e.error === "network") {
        toast("Speech recognition needs an internet connection");
      }
    };
    rec.onend = () => { // browsers stop after silence; restart while the user still wants to dictate
      if (state.listening) { try { rec.start(); } catch (err) { state.listening = false; setMicUi(false); } }
    };
    state.listening = true;
    setMicUi(true);
    try { rec.start(); } catch (err) { /* already started */ }
  }

  function stopListening() {
    state.listening = false;
    if (rec) { rec.onend = null; try { rec.stop(); } catch (err) { /* ignore */ } }
    setMicUi(false);
  }

  // ---------- init ----------
  async function init() {
    buildTabs();
    renderPipeline(null);
    try {
      [state.keywords, state.examples] = await Promise.all([api("/api/keywords"), api("/api/examples")]);
    } catch (e) { toast("Could not reach the server: " + e.message); return; }

    buildExampleSelect();
    $("#example").value = state.examples[0].id;
    loadExample();
    refreshLangUi();

    $("#lang").addEventListener("change", onLangChange);
    $("#example").addEventListener("change", onExampleChange);
    code.addEventListener("input", markEdited);
    $("#run").addEventListener("click", runProgram);
    $("#compare").addEventListener("click", runCompare);
    $("#clear").addEventListener("click", () => { code.value = ""; code.focus(); markEdited(); });
    $("#mic").addEventListener("click", () => (state.listening ? stopListening() : startListening()));
    $("#speakOut").addEventListener("click", () => speakResult(state.last));
    $("#stopSpeak").addEventListener("click", () => hasTTS && speechSynthesis.cancel());
    $("#chips").addEventListener("click", (e) => { if (e.target.classList.contains("chip")) insertAtCursor(e.target.textContent); });
    $("#errors").addEventListener("click", (e) => { const li = e.target.closest("li"); if (li) goToLine(+li.dataset.line); });
    code.addEventListener("keydown", (e) => { if ((e.metaKey || e.ctrlKey) && e.key === "Enter") runProgram(); });
    if (hasTTS) speechSynthesis.addEventListener("voiceschanged", updateVoiceStatus);
    if (!SR) $("#micStatus").textContent = "🎤 Voice input is not supported in this browser (use Chrome, Edge or Safari).";
  }
  init();
})();
