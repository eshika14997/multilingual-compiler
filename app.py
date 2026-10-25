import os
from flask import Flask, jsonify, request, send_from_directory

from compiler.pipeline import compile_source
from compiler.dictionary import KeywordDictionary
from compiler.translate import translate, compare_languages
from compiler.library import load_library

ROOT = os.path.dirname(os.path.abspath(__file__))
LANGS = ("en", "hi", "gu")
MAX_SOURCE = 5000

app = Flask(__name__, static_folder=os.path.join(ROOT, "static"), static_url_path="/static")
DICT = KeywordDictionary()
LIBRARY = load_library()   # 20 ready-made programs (en / hi / gu)


def read_json():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, (jsonify(error="Request body must be JSON"), 400)
    source = data.get("source", "")
    lang = data.get("lang", "en")
    policy = data.get("policy", "strict")
    if not isinstance(source, str) or len(source) > MAX_SOURCE:
        return None, (jsonify(error=f"Source must be text of at most {MAX_SOURCE} characters"), 400)
    if lang not in LANGS or policy not in ("strict", "mixed"):
        return None, (jsonify(error="Invalid language or policy"), 400)
    return (source, lang, policy), None


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/keywords")
def keywords():
    return jsonify(DICT.table)


@app.get("/api/examples")
def examples():
    return jsonify(LIBRARY)


@app.post("/api/compile")
def compile_api():
    args, err = read_json()
    if err:
        return err
    source, lang, policy = args
    return jsonify(compile_source(source, lang, policy).to_dict())


@app.post("/api/translate")
def translate_api():
    args, err = read_json()
    if err:
        return err
    source, lang, _ = args
    text, errs = translate(source, lang, DICT)
    return jsonify(ok=not errs, source=text, errors=[str(e) for e in errs])


@app.post("/api/compare")
def compare_api():
    args, err = read_json()
    if err:
        return err
    return jsonify(compare_languages(args[0]))


if __name__ == "__main__":
    # Port 8000 (macOS uses 5000 for AirPlay). localhost counts as a secure context,
    # which the browser needs for microphone access.
    app.run(host="127.0.0.1", port=8000, debug=False)
