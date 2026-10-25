import os, sys, shutil, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from app import app
from compiler.translate import translate

HAS_CC = any(shutil.which(c) for c in ("gcc", "cc", "clang"))


class AppTests(unittest.TestCase):
    def setUp(self):
        self.c = app.test_client()

    def post(self, path, **kw):
        return self.c.post(path, json=kw)

    def test_index_and_static(self):
        self.assertEqual(self.c.get("/").status_code, 200)
        for f in ("app.js", "speech.js", "style.css"):
            self.assertEqual(self.c.get("/static/" + f).status_code, 200)

    def test_keywords_and_examples(self):
        self.assertEqual(set(self.c.get("/api/keywords").json), {"en", "hi", "gu"})
        ex = self.c.get("/api/examples").json
        self.assertEqual(len(ex), 20)
        self.assertEqual(len({x["id"] for x in ex}), 20)
        self.assertTrue(all(k in ex[0] for k in ("en", "hi", "gu")))

    @unittest.skipUnless(HAS_CC, "no C compiler")
    def test_compile_ok(self):
        r = self.post("/api/compile", source="int a = 2;\nprint a * 21;", lang="en").json
        self.assertTrue(r["ok"])
        self.assertEqual(r["output"], "42\n")

    def test_compile_error_json(self):
        r = self.post("/api/compile", source="print x;", lang="en").json
        self.assertFalse(r["ok"])
        self.assertEqual(r["errors"][0]["kind"], "SEMANTIC")
        self.assertEqual(r["stage"], "semantic")

    def test_validation(self):
        self.assertEqual(self.post("/api/compile", source="x", lang="fr").status_code, 400)
        self.assertEqual(self.post("/api/compile", source="x" * 6000, lang="en").status_code, 400)
        self.assertEqual(self.c.post("/api/compile", data="not json").status_code, 400)

    def test_translate_keeps_strings_and_names(self):
        r = self.post("/api/translate", source='int if_x = 1;\nprint "print if", if_x;', lang="hi").json
        self.assertTrue(r["ok"])
        self.assertEqual(r["source"], 'पूर्णांक if_x = 1;\nप्रिंट "print if", if_x;')

    def test_translate_roundtrip(self):
        src = open(os.path.join(ROOT, "examples", "while_hi.mlang"), encoding="utf-8").read()
        gu, _ = translate(src, "gu")
        back, _ = translate(gu, "hi")
        self.assertEqual(back, src)

    @unittest.skipUnless(HAS_CC, "no C compiler")
    def test_compare(self):
        src = open(os.path.join(ROOT, "examples", "sum_en.mlang"), encoding="utf-8").read()
        r = self.post("/api/compare", source=src, lang="en").json
        self.assertTrue(r["ok"] and r["same_tokens"] and r["same_ir"] and r["same_output"])
        self.assertEqual(r["langs"]["gu"]["output"], "Sum of two number : 30\n")


if __name__ == "__main__":
    unittest.main()
