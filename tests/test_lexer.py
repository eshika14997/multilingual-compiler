import os, sys, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from compiler.lexer import Lexer
from compiler.dictionary import KeywordDictionary

EX = os.path.join(ROOT, "examples")


def norm(fname, lang, policy="strict"):
    with open(os.path.join(EX, fname), encoding="utf-8") as f:
        lx = Lexer(f.read(), lang, policy)
    _, errs = lx.tokenize()
    return lx.normalized(), errs


class T(unittest.TestCase):
    def test_dictionary_valid(self):
        self.assertEqual(KeywordDictionary().errors, [])

    def test_same_tokens_all_languages(self):
        en, e1 = norm("sum_en.mlang", "en")
        hi, e2 = norm("sum_hi.mlang", "hi")
        gu, e3 = norm("sum_gu.mlang", "gu")
        self.assertEqual((e1, e2, e3), ([], [], []))
        self.assertEqual(en, hi)
        self.assertEqual(en, gu)

    def test_strict_rejects_mixed(self):
        _, errs = norm("sum_hi.mlang", "en", "strict")
        self.assertTrue(any(e.kind == "MIXED_LANGUAGE" for e in errs))

    def test_mixed_policy_allows(self):
        _, errs = norm("sum_hi.mlang", "en", "mixed")
        self.assertEqual(errs, [])

    def test_lexical_error(self):
        _, errs = Lexer("int x = 5 @ 3;", "en").tokenize()
        self.assertTrue(any(e.kind == "LEXICAL" for e in errs))

    def test_unterminated_string(self):
        _, errs = Lexer('print "abc;', "en").tokenize()
        self.assertTrue(any("Unterminated" in e.message for e in errs))


if __name__ == "__main__":
    unittest.main()
