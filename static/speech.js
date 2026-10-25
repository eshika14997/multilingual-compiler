/* Pure helpers for voice input (no browser APIs, so they can be unit-tested in Node). */
(function (root) {
  "use strict";
  const nfc = (s) => s.normalize("NFC");
  const MAXN = 5; // longest spoken phrase, in words

  // Spoken symbol names -> symbols. English names work in every language.
  const SYMBOLS = {
    en: {
      "semicolon": ";", "semi colon": ";", "double equals": "==", "equals equals": "==",
      "equal to": "=", "equals": "=", "equal": "=", "not equal to": "!=", "not equals": "!=",
      "greater than or equal to": ">=", "less than or equal to": "<=",
      "greater than": ">", "less than": "<", "plus": "+", "minus": "-", "times": "*",
      "multiplied by": "*", "multiply": "*", "divided by": "/", "divide": "/",
      "modulo": "%", "modulus": "%", "percent": "%", "comma": ",",
      "open bracket": "(", "close bracket": ")", "open parenthesis": "(", "close parenthesis": ")",
      "open paren": "(", "close paren": ")", "quote": '"', "end quote": '"', "close quote": '"',
      "new line": "\n", "newline": "\n", "next line": "\n"
    },
    hi: {
      "सेमीकोलन": ";", "सेमी कोलन": ";", "अर्धविराम": ";", "बराबर बराबर": "==", "बराबर नहीं": "!=",
      "बराबर": "=", "बड़ा या बराबर": ">=", "छोटा या बराबर": "<=", "से बड़ा": ">", "से छोटा": "<",
      "बड़ा": ">", "छोटा": "<", "प्लस": "+", "जमा": "+", "जोड़": "+", "माइनस": "-", "घटा": "-",
      "गुणा": "*", "भाग": "/", "प्रतिशत": "%", "कॉमा": ",", "अल्पविराम": ",",
      "ब्रैकेट खोलें": "(", "ब्रैकेट बंद": ")", "कोष्ठक खोलें": "(", "कोष्ठक बंद": ")",
      "कोट": '"', "नई लाइन": "\n", "नयी लाइन": "\n", "अगली लाइन": "\n"
    },
    gu: {
      "સેમીકોલન": ";", "અર્ધવિરામ": ";", "બરાબર બરાબર": "==", "બરાબર નથી": "!=", "બરાબર": "=",
      "મોટું": ">", "નાનું": "<", "પ્લસ": "+", "માઇનસ": "-", "ગુણાકાર": "*", "ભાગાકાર": "/",
      "ભાગ": "/", "ટકા": "%", "કોમા": ",", "અલ્પવિરામ": ",", "ઉદ્ધરણ": '"',
      "નવી લાઇન": "\n", "નવી લીટી": "\n"
    }
  };

  const COMMANDS = {
    run: ["run", "run program", "run the program", "execute", "चलाओ", "प्रोग्राम चलाओ", "चलाइए",
          "रन", "रन करो", "ચલાવો", "પ્રોગ્રામ ચલાવો", "રન કરો"],
    clear: ["clear", "clear all", "clear code", "साफ करो", "साफ़ करो", "मिटाओ", "क्लियर",
            "સાફ કરો", "ભૂંસી નાખો", "ક્લિયર"]
  };

  /** Build phrase -> replacement map for the selected language.
   *  Keywords written in ANY language are snapped to the selected language's keyword. */
  function buildPhraseMap(table, lang) {
    const map = new Map();
    const add = (k, v) => map.set(nfc(k).toLowerCase(), v);
    Object.entries(SYMBOLS.en).forEach(([k, v]) => add(k, v));
    Object.entries(SYMBOLS[lang] || {}).forEach(([k, v]) => add(k, v));
    const target = table[lang];
    Object.keys(table).forEach((L) => {
      Object.entries(table[L]).forEach(([canon, word]) => {
        const to = target[canon];
        add(word, to);
        if (word.includes("_")) add(word.replace(/_/g, " "), to);
      });
    });
    return map;
  }

  /** Turn a spoken transcript into source-code text. */
  function processSpeech(transcript, map) {
    const words = nfc(transcript.trim()).split(/\s+/).filter(Boolean);
    const out = [];
    let inQuote = false;
    let i = 0;
    while (i < words.length) {
      let hit = false;
      for (let n = Math.min(MAXN, words.length - i); n >= 1; n--) {
        const phrase = words.slice(i, i + n).join(" ").toLowerCase();
        if (!map.has(phrase)) continue;
        const val = map.get(phrase);
        if (inQuote && val !== '"') continue;      // inside a string: only a closing quote counts
        if (val === '"') inQuote = !inQuote;
        out.push(val);
        i += n;
        hit = true;
        break;
      }
      if (!hit) { out.push(words[i]); i++; }
    }
    let s = out.join(" ");
    s = s.replace(/ ?\n ?/g, "\n").replace(/ ([;,)])/g, "$1").replace(/\( /g, "(");
    s = s.replace(/"\s*([^"]*?)\s*"/g, '"$1"');
    return s;
  }

  /** Returns "run", "clear" or null. */
  function detectCommand(transcript) {
    const t = nfc(transcript).toLowerCase().replace(/[.,!?।]/g, "").trim();
    for (const [cmd, list] of Object.entries(COMMANDS)) {
      if (list.some((w) => nfc(w).toLowerCase() === t)) return cmd;
    }
    return null;
  }

  const api = { SYMBOLS, COMMANDS, buildPhraseMap, processSpeech, detectCommand };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.MLCSpeech = api;
})(typeof self !== "undefined" ? self : this);
