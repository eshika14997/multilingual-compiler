import unicodedata
from .tokens import Token
from .errors import CompileError
from .dictionary import KeywordDictionary, nfc

DIGITS = "0123456789"


def is_ident_start(ch: str) -> bool:
    return ch == "_" or unicodedata.category(ch).startswith("L")


def is_ident_part(ch: str) -> bool:
    # Letters, digits, underscore AND combining marks (matras/virama in Hindi & Gujarati)
    return ch == "_" or ch in DIGITS or unicodedata.category(ch).startswith(("L", "M"))


TWO_CHAR_OPS = {"==", "!=", "<=", ">="}
ONE_CHAR_OPS = set("+-*/%<>=")


class Lexer:
    """
    policy 'strict': every keyword must belong to the selected language
    policy 'mixed' : keywords from any supported language are accepted
    """

    def __init__(self, source, language="en", policy="strict", dictionary=None):
        self.src = nfc(source)
        self.language = language
        self.policy = policy
        self.dict = dictionary or KeywordDictionary()
        self.tokens, self.errors = [], list(self.dict.errors)
        if language not in self.dict.languages:
            self.errors.append(CompileError("DICTIONARY", f"Unsupported language '{language}'"))

    def tokenize(self):
        s, i, line, col, n = self.src, 0, 1, 1, len(self.src)

        def add(t, v, ln, cl, lex="", lang=None):
            self.tokens.append(Token(t, v, ln, cl, lex or v, lang, i))

        while i < n:
            ch = s[i]
            if ch == "\n":
                i += 1; line += 1; col = 1; continue
            if ch.isspace():
                i += 1; col += 1; continue
            if s.startswith("//", i):
                while i < n and s[i] != "\n":
                    i += 1
                continue
            sc = col
            if is_ident_start(ch):
                j = i
                while j < n and is_ident_part(s[j]):
                    j += 1
                word = s[i:j]
                hit = self.dict.lookup(word)
                if hit:
                    canon, lang = hit
                    if self.policy == "strict" and lang != self.language:
                        self.errors.append(CompileError(
                            "MIXED_LANGUAGE",
                            f"Keyword '{word}' belongs to '{lang}' but selected language is "
                            f"'{self.language}' (strict policy)", line, sc))
                    add("KEYWORD", canon, line, sc, word, lang)
                else:
                    add("IDENT", word, line, sc)
                col += j - i; i = j; continue
            if ch in DIGITS:
                j = i
                while j < n and s[j] in DIGITS:
                    j += 1
                if j + 1 < n and s[j] == "." and s[j + 1] in DIGITS:
                    j += 1
                    while j < n and s[j] in DIGITS:
                        j += 1
                add("NUMBER", s[i:j], line, sc)
                col += j - i; i = j; continue
            if ch == '"':
                j = i + 1
                while j < n and s[j] not in '"\n':
                    j += 1
                if j >= n or s[j] != '"':
                    self.errors.append(CompileError("LEXICAL", "Unterminated string literal", line, sc))
                    col += j - i; i = j; continue
                add("STRING", s[i + 1:j], line, sc, s[i:j + 1])
                col += j + 1 - i; i = j + 1; continue
            if s[i:i + 2] in TWO_CHAR_OPS:
                add("OP", s[i:i + 2], line, sc); i += 2; col += 2; continue
            if ch in ONE_CHAR_OPS:
                add("OP", ch, line, sc); i += 1; col += 1; continue
            single = {";": "SEMI", "(": "LPAREN", ")": "RPAREN", ",": "COMMA"}
            if ch in single:
                add(single[ch], ch, line, sc); i += 1; col += 1; continue
            self.errors.append(CompileError("LEXICAL", f"Unexpected character '{ch}'", line, sc))
            i += 1; col += 1

        add("EOF", "EOF", line, col)
        return self.tokens, self.errors

    def normalized(self):
        """Language-independent token stream."""
        return " ".join(t.short() for t in self.tokens if t.type != "EOF")
