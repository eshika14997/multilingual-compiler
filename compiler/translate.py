"""Translate a program between languages by swapping keywords only (identifiers/strings untouched)."""
from .lexer import Lexer
from .dictionary import KeywordDictionary
from .pipeline import compile_source

LANGS = ["en", "hi", "gu"]


def translate(source: str, to_lang: str, dictionary: KeywordDictionary = None):
    """Returns (translated_source, lexical_errors)."""
    d = dictionary or KeywordDictionary()
    lx = Lexer(source, to_lang, "mixed", d)
    toks, errs = lx.tokenize()
    if errs:
        return source, errs
    src, out, last = lx.src, [], 0
    for t in toks:
        if t.type == "KEYWORD":
            out.append(src[last:t.pos])
            out.append(d.word(to_lang, t.value))
            last = t.pos + len(t.lexeme)
    out.append(src[last:])
    return "".join(out), []


def compare_languages(source: str, run: bool = True):
    """Compile the same program in EN, HI and GU and report whether the results match."""
    d = KeywordDictionary()
    langs = {}
    for lang in LANGS:
        text, errs = translate(source, lang, d)
        if errs:
            return {"ok": False, "error": "; ".join(str(e) for e in errs)}
        r = compile_source(text, lang, "strict", run=run)
        langs[lang] = {"source": text, "normalized": r.normalized, "ir": r.ir,
                       "output": r.output, "stage": r.stage,
                       "errors": [str(e) for e in r.errors]}
    base = langs["en"]
    same = lambda k: all(langs[l][k] == base[k] for l in LANGS)
    return {"ok": True, "langs": langs, "same_tokens": same("normalized"),
            "same_ir": same("ir"), "same_output": same("output")}
