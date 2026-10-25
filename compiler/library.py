"""Ready-made example programs. Only the English source is stored in programs/*.mlang;
the Hindi and Gujarati versions are produced by translating the keywords."""
import os
import re

from .dictionary import KeywordDictionary
from .translate import translate

DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "programs")


def load_library():
    d = KeywordDictionary()
    items = []
    for fn in sorted(os.listdir(DIR)):
        if not fn.endswith(".mlang"):
            continue
        with open(os.path.join(DIR, fn), encoding="utf-8") as f:
            text = f.read()
        title, cat, body = fn[:-6], "Other", []
        for line in text.splitlines():
            m = re.match(r"//\s*Title:\s*(.+)", line)
            c = re.match(r"//\s*Category:\s*(.+)", line)
            if m:
                title = m.group(1).strip()
            elif c:
                cat = c.group(1).strip()
            else:
                body.append(line)
        en = "\n".join(body).strip() + "\n"
        item = {"id": re.sub(r"^\d+_", "", fn[:-6]), "title": title, "category": cat, "en": en}
        for lang in ("hi", "gu"):
            item[lang] = translate(en, lang, d)[0]
        items.append(item)
    return items
