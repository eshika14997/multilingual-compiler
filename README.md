# Multilingual Programming Language Compiler (English / Hindi / Gujarati)

Pipeline: Source -> Lexer (keyword mapping) -> Parser (AST) -> Semantic -> IR -> C code -> Run

## Language
    int a = 10;   float f = 2.5;   set a = a + 1;   a = a + 1;
    print "text", a;
    if cond ... else ... end_if
    while cond ... end_while
Keywords for each language live in compiler/keywords.json.

## Usage
    python3 main.py examples/sum_hi.mlang --lang hi
    python3 main.py examples/sum_gu.mlang --lang gu --quiet
    python3 main.py examples/sum_hi.mlang --lang en --policy mixed
    python3 compare.py                      # EN = HI = GU proof
    python3 -m unittest discover -s tests -v

## Progress
- Day 1: dictionary, lexer, language policy, tests
- Day 2: parser, semantic analysis, IR, C code generation, compile + run
- Day 3: Flask web UI, speech-to-text, text-to-speech
