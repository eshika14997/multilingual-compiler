import argparse
import sys

from compiler.pipeline import compile_source


def section(title):
    print(f"\n===== {title} =====")


def main():
    ap = argparse.ArgumentParser(description="Multilingual Programming Language Compiler")
    ap.add_argument("file")
    ap.add_argument("--lang", default="en", choices=["en", "hi", "gu"])
    ap.add_argument("--policy", default="strict", choices=["strict", "mixed"])
    ap.add_argument("--no-run", action="store_true", help="stop after C code generation")
    ap.add_argument("--quiet", action="store_true", help="only show errors and program output")
    a = ap.parse_args()

    with open(a.file, encoding="utf-8") as f:
        src = f.read()
    r = compile_source(src, a.lang, a.policy, run=not a.no_run)

    if not a.quiet:
        section("1. TOKENS (keyword mapping)")
        print(f"{'LINE':<5}{'COL':<5}{'LEXEME':<24}{'TOKEN':<18}LANG")
        for t in r.tokens:
            print(f"{t['line']:<5}{t['col']:<5}{t['lexeme']:<24}{t['token']:<18}{t['lang']}")
        section("2. NORMALIZED TOKEN STREAM")
        print(r.normalized)
        if r.ast:
            section("3. AST (after syntax analysis)")
            print(r.ast)
        if r.ir:
            section("4. INTERMEDIATE CODE")
            print("\n".join(r.ir))
        if r.c_code:
            section("5. GENERATED C CODE")
            print(r.c_code)

    if r.errors:
        section(f"ERRORS (stopped at stage: {r.stage})")
        for e in r.errors:
            print(" ", e)
        if r.output:
            print(r.output)
        sys.exit(1)

    if not a.no_run:
        section("OUTPUT")
        print(r.output, end="")


if __name__ == "__main__":
    main()
