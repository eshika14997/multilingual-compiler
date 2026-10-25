# Multilingual Programming Language Compiler (English / Hindi / Gujarati)

Pipeline: Source -> Lexer (keyword mapping) -> Parser (AST) -> Semantic -> IR -> C code -> Run
Web UI: Flask backend + browser speech-to-text and text-to-speech (Web Speech API).

## Setup
    pip3 install -r requirements.txt
    python3 app.py            # then open http://127.0.0.1:8000  (Chrome / Edge / Safari)

## Command line
    python3 main.py examples/sum_hi.mlang --lang hi
    python3 compare.py                      # EN = HI = GU proof
    python3 -m unittest discover -s tests -v

## Language
    int a = 10;   float f = 2.5;   set a = a + 1;   a = a + 1;
    print "text", a;
    if cond ... else ... end_if
    while cond ... end_while
Keywords for each language live in compiler/keywords.json.

## Progress
- Day 1: dictionary, lexer, language policy, tests
- Day 2: parser, semantic analysis, IR, C code generation, compile + run
- Day 3: Flask web UI, speech-to-text, text-to-speech, translate + compare
