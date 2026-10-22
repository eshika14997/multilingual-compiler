import os, sys, shutil, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from compiler.pipeline import compile_source

HAS_CC = any(shutil.which(c) for c in ("gcc", "cc", "clang"))


def load(name, lang):
    with open(os.path.join(ROOT, "examples", f"{name}_{lang}.mlang"), encoding="utf-8") as f:
        return f.read()


def kinds(r):
    return [e.kind for e in r.errors]


class Equivalence(unittest.TestCase):
    def test_same_ir_all_languages(self):
        for name in ("sum", "if", "while"):
            rs = {l: compile_source(load(name, l), l, run=False) for l in ("en", "hi", "gu")}
            for l, r in rs.items():
                self.assertEqual(r.errors, [], f"{name}_{l}")
            self.assertEqual(rs["en"].ir, rs["hi"].ir)
            self.assertEqual(rs["en"].ir, rs["gu"].ir)
            self.assertEqual(rs["en"].c_code, rs["gu"].c_code)

    @unittest.skipUnless(HAS_CC, "no C compiler")
    def test_same_output(self):
        outs = {l: compile_source(load("sum", l), l).output for l in ("en", "hi", "gu")}
        self.assertEqual(set(outs.values()), {"Sum of two number : 30\n"})

    @unittest.skipUnless(HAS_CC, "no C compiler")
    def test_while_and_if_output(self):
        self.assertEqual(compile_source(load("while", "hi"), "hi").output,
                         "Total : 15  Average : 3\n")
        self.assertEqual(compile_source(load("if", "gu"), "gu").output, "Bigger number : 15\n")


class Errors(unittest.TestCase):
    def test_undeclared(self):
        r = compile_source('int a = 1; print b;', "en", run=False)
        self.assertEqual(kinds(r), ["SEMANTIC"])

    def test_redeclared(self):
        r = compile_source("int a = 1; int a = 2;", "en", run=False)
        self.assertIn("already declared", r.errors[0].message)

    def test_float_to_int(self):
        self.assertEqual(kinds(compile_source("int a = 2.5;", "en", run=False)), ["SEMANTIC"])

    def test_string_outside_print(self):
        self.assertEqual(kinds(compile_source('int a = "hi";', "en", run=False)), ["SEMANTIC"])

    def test_division_by_zero(self):
        r = compile_source("int a = 5 / 0;", "en", run=False)
        self.assertIn("Division by zero", r.errors[0].message)

    def test_missing_semicolon_hindi(self):
        r = compile_source("पूर्णांक a = 5\nप्रिंट a;", "hi", run=False)
        self.assertEqual(kinds(r), ["SYNTAX"])
        self.assertEqual(r.errors[0].line, 2)

    def test_missing_end_if(self):
        r = compile_source("int a = 1;\nif a > 0\n print a;", "en", run=False)
        self.assertTrue(any("Missing" in e.message for e in r.errors))

    def test_stray_else_no_hang(self):
        r = compile_source("else print 1;", "en", run=False)
        self.assertTrue(r.errors)

    def test_mixed_language_strict(self):
        r = compile_source("int a = 5; \u092a\u094d\u0930\u093f\u0902\u091f a;", "en", "strict", run=False)
        self.assertIn("MIXED_LANGUAGE", kinds(r))

    def test_mixed_language_allowed(self):
        r = compile_source("int a = 5; \u092a\u094d\u0930\u093f\u0902\u091f a;", "en", "mixed", run=False)
        self.assertEqual(r.errors, [])

    @unittest.skipUnless(HAS_CC, "no C compiler")
    def test_hindi_variable_names(self):
        r = compile_source("पूर्णांक संख्या = 7;\nप्रिंट संख्या * 2;", "hi")
        self.assertEqual((r.errors, r.output), ([], "14\n"))

    @unittest.skipUnless(HAS_CC, "no C compiler")
    def test_infinite_loop_stopped(self):
        r = compile_source("int i = 1; while 1 < 2 set i = 0; end_while", "en")
        self.assertEqual(kinds(r), ["RUNTIME"])


if __name__ == "__main__":
    unittest.main()
