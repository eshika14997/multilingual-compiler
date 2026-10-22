from dataclasses import dataclass, field
from typing import List

from .lexer import Lexer
from .parser import Parser
from .semantic import SemanticAnalyzer
from .ir import IRGenerator
from .codegen import generate_c
from .runner import run_c
from .errors import CompileError
from . import ast_nodes as A


@dataclass
class Result:
    language: str
    policy: str
    tokens: list = field(default_factory=list)
    normalized: str = ""
    ast: str = ""
    ir: List[str] = field(default_factory=list)
    c_code: str = ""
    output: str = ""
    errors: List[CompileError] = field(default_factory=list)
    stage: str = "start"      # last stage reached

    @property
    def ok(self):
        return not self.errors

    def to_dict(self):
        """JSON-friendly form (used by the Day 3 web UI)."""
        return {
            "language": self.language, "policy": self.policy, "ok": self.ok,
            "stage": self.stage, "tokens": self.tokens, "normalized": self.normalized,
            "ast": self.ast, "ir": self.ir, "c_code": self.c_code, "output": self.output,
            "errors": [{"kind": e.kind, "message": e.message, "line": e.line, "col": e.col}
                       for e in self.errors],
        }


def compile_source(source: str, lang: str = "en", policy: str = "strict", run: bool = True) -> Result:
    r = Result(lang, policy)

    lx = Lexer(source, lang, policy)
    toks, errs = lx.tokenize()
    r.stage = "lexer"
    r.tokens = [{"line": t.line, "col": t.col, "lexeme": t.lexeme,
                 "token": t.short(), "lang": t.lang or ""} for t in toks if t.type != "EOF"]
    r.normalized = lx.normalized()
    if errs:
        r.errors = errs
        return r

    prog, errs = Parser(toks, lang).parse()
    r.stage = "parser"
    r.ast = A.dump(prog)
    if errs:
        r.errors = errs
        return r

    errs = SemanticAnalyzer().analyze(prog)
    r.stage = "semantic"
    if errs:
        r.errors = errs
        return r

    ir = IRGenerator().generate(prog)
    r.ir = [str(i) for i in ir]
    r.stage = "ir"

    r.c_code = generate_c(ir)
    r.stage = "codegen"

    if run:
        res = run_c(r.c_code)
        r.stage = "run"
        r.output = res.output
        if not res.ok:
            r.errors = [CompileError("RUNTIME", res.error)]
    return r
