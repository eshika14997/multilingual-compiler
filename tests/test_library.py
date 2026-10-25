import os, sys, shutil, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from compiler.library import load_library
from compiler.pipeline import compile_source

HAS_CC = any(shutil.which(c) for c in ("gcc", "cc", "clang"))

EXPECTED = {
    "sum_two_numbers": "Sum of two number : 30\n",
    "calculator": "Addition       : 22\nSubtraction    : 12\nMultiplication : 85\nDivision       : 3\n"
                  "Remainder      : 2\nExact division : 3.4\n",
    "bigger_of_two": "Bigger number : 15\n",
    "even_odd": "7 is Odd\n",
    "pos_neg_zero": "-5 is Negative\n",
    "largest_of_three": "Largest number : 45\n",
    "grade": "Grade : A\n",
    "leap_year": "2024 is a Leap Year\n",
    "simple_interest": "Simple Interest : 750\nTotal Amount    : 5750\n",
    "celsius_fahrenheit": "37 C = 98.6 F\n",
    "sum_1_to_n": "Sum of 1 to 10 = 55\n",
    "multiplication_table": "".join(f"7 x {i} = {7*i}\n" for i in range(1, 11)),
    "factorial": "5! = 120\n",
    "fibonacci": "0\n1\n1\n2\n3\n5\n8\n13\n21\n34\n",
    "reverse_number": "Reverse of 12345 is 54321\n",
    "palindrome": "12321 is a Palindrome\n",
    "sum_of_digits": "Sum of digits of 12345 = 15\n",
    "armstrong": "153 is an Armstrong number\n",
    "prime": "29 is a Prime number\n",
    "gcd": "GCD of 48 and 18 is 6\n",
}


class Library(unittest.TestCase):
    def test_twenty_programs(self):
        lib = load_library()
        self.assertEqual({x["id"] for x in lib}, set(EXPECTED))

    def test_all_compile_to_same_ir(self):
        for it in load_library():
            rs = {l: compile_source(it[l], l, run=False) for l in ("en", "hi", "gu")}
            for l, r in rs.items():
                self.assertEqual(r.errors, [], f"{it['id']} ({l})")
            self.assertEqual(rs["en"].ir, rs["hi"].ir, it["id"])
            self.assertEqual(rs["en"].ir, rs["gu"].ir, it["id"])

    @unittest.skipUnless(HAS_CC, "no C compiler")
    def test_expected_output_in_every_language(self):
        for it in load_library():
            for l in ("en", "hi", "gu"):
                r = compile_source(it[l], l)
                self.assertEqual((r.errors, r.output), ([], EXPECTED[it["id"]]), f"{it['id']} ({l})")


if __name__ == "__main__":
    unittest.main()
