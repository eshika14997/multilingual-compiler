import argparse
import sys
from compiler.lexer import Lexer


def main():
    ap = argparse.ArgumentParser(description="Multilingual compiler - Day 1 (lexer)")
    ap.add_argument("file")
    ap.add_argument("--lang", default="en", choices=["en", "hi", "gu"])
    ap.add_argument("--policy", default="strict", choices=["strict", "mixed"])
    a = ap.parse_args()

    with open(a.file, encoding="utf-8") as f:
        src = f.read()
    lx = Lexer(src, a.lang, a.policy)
    tokens, errors = lx.tokenize()

    print(f"{'LINE':<5}{'COL':<5}{'LEXEME':<22}{'TOKEN':<12}{'LANG'}")
    for t in tokens:
        print(f"{t.line:<5}{t.col:<5}{t.lexeme:<22}{t.type if t.type != 'KEYWORD' else t.value:<12}{t.lang or ''}")
    print("\nNormalized:", lx.normalized())
    if errors:
        print("\nErrors:")
        for e in errors:
            print("  ", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
