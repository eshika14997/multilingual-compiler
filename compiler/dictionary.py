import json
import os
import unicodedata
from .errors import CompileError

_PATH = os.path.join(os.path.dirname(__file__), "keywords.json")


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


class KeywordDictionary:
    """Formal multilingual keyword dictionary: word -> (canonical, language)."""

    def __init__(self, path: str = _PATH):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)["languages"]
        self.table = data
        self.languages = list(data.keys())
        self.canonicals = set()
        self.reverse = {}
        self.errors = []
        for lang, table in data.items():
            for canon, word in table.items():
                self.canonicals.add(canon)
                word = nfc(word)
                if word in self.reverse and self.reverse[word][0] != canon:
                    self.errors.append(CompileError(
                        "DICTIONARY",
                        f"Ambiguous keyword '{word}': maps to {self.reverse[word][0]} "
                        f"({self.reverse[word][1]}) and {canon} ({lang})"))
                self.reverse[word] = (canon, lang)
        for lang, table in data.items():
            for c in self.canonicals - set(table):
                self.errors.append(CompileError("DICTIONARY", f"Language '{lang}' is missing keyword {c}"))

    def lookup(self, word: str):
        return self.reverse.get(nfc(word))

    def word(self, lang: str, canonical: str) -> str:
        """Keyword as written in a given language (used for friendly error messages)."""
        return self.table.get(lang, self.table["en"]).get(canonical, canonical)
