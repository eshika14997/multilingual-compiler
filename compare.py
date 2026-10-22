"""Demo of the main project result: EN = HI = GU  ->  same tokens, same IR, same output."""
import sys
from compiler.pipeline import compile_source

PROGRAMS = sys.argv[1:] or ["sum", "if", "while"]
LANGS = ["en", "hi", "gu"]

for name in PROGRAMS:
    results = {}
    for lang in LANGS:
        with open(f"examples/{name}_{lang}.mlang", encoding="utf-8") as f:
            results[lang] = compile_source(f.read(), lang)
    base = results["en"]
    print(f"\n### {name}")
    for lang in LANGS:
        r = results[lang]
        print(f"  {lang}: errors={len(r.errors)}  same tokens={r.normalized == base.normalized}"
              f"  same IR={r.ir == base.ir}  same output={r.output == base.output}")
    print("  IR:\n    " + "\n    ".join(base.ir))
    print("  Output:", base.output.strip().replace("\n", " | "))
