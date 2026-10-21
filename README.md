# Multilingual Programming Language Compiler (English / Hindi / Gujarati)

Pipeline: Source -> Lexer (keyword mapping) -> Parser -> Semantic -> IR -> C code -> Run

## Day 1 (done): setup, keyword dictionary, lexer, tests
    python main.py examples/sum_hi.mlang --lang hi
    python -m unittest discover -s tests -v
