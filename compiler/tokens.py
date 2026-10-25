from dataclasses import dataclass
from typing import Optional


@dataclass
class Token:
    type: str                  # KEYWORD, IDENT, NUMBER, STRING, OP, SEMI, LPAREN, RPAREN, EOF
    value: str                 # canonical name for keywords (e.g. PRINT), lexeme otherwise
    line: int
    col: int
    lexeme: str = ""           # original text written by the user
    lang: Optional[str] = None # language of keyword (en/hi/gu); None for non-keywords
    pos: int = 0               # character offset in the (NFC-normalized) source

    def short(self):
        if self.type == "KEYWORD":
            return self.value
        if self.type in ("IDENT", "NUMBER", "STRING", "OP"):
            return f"{self.type}({self.value})"
        return self.type
