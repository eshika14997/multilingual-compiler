import json
from dataclasses import dataclass
from . import ast_nodes as A


@dataclass
class Instr:
    op: str
    args: list
    ty: str = ""

    def __str__(self):
        o, a = self.op, self.args
        if o == "DECL":
            return f"DECL {self.ty} {a[0]}"
        if o == "ASSIGN":
            return f"ASSIGN {a[0]} {a[1]}"
        if o == "BINOP":
            return f"{a[0]} = {a[1]} {a[2]} {a[3]}"
        if o == "NEG":
            return f"{a[0]} = NEG {a[1]}"
        if o == "LABEL":
            return f"LABEL {a[0]}"
        if o == "GOTO":
            return f"GOTO {a[0]}"
        if o == "IF_FALSE":
            return f"IF_FALSE {a[0]} GOTO {a[1]}"
        if o == "PRINT":
            return f"PRINT {a[0]}"
        return o  # PRINTLN


class IRGenerator:
    """AST -> language-independent three-address code (temps are %t1, %t2 ...)."""

    def __init__(self):
        self.code, self.tmp, self.lbl = [], 0, 0

    def temp(self):
        self.tmp += 1
        return f"%t{self.tmp}"

    def label(self):
        self.lbl += 1
        return f"L{self.lbl}"

    def emit(self, op, *args, ty=""):
        self.code.append(Instr(op, list(args), ty))

    def generate(self, program):
        for s in program.body:
            self.stmt(s)
        return self.code

    def stmt(self, s):
        if isinstance(s, A.Decl):
            self.emit("DECL", s.name, ty=s.ty)
            if s.init is not None:
                self.emit("ASSIGN", s.name, self.expr(s.init))
        elif isinstance(s, A.Assign):
            self.emit("ASSIGN", s.name, self.expr(s.value))
        elif isinstance(s, A.Print):
            for a in s.args:
                self.emit("PRINT", self.expr(a), ty=a.ty)
            self.emit("PRINTLN")
        elif isinstance(s, A.If):
            c = self.expr(s.cond)
            l_else = self.label()
            self.emit("IF_FALSE", c, l_else)
            for x in s.then:
                self.stmt(x)
            if s.orelse:
                l_end = self.label()
                self.emit("GOTO", l_end)
                self.emit("LABEL", l_else)
                for x in s.orelse:
                    self.stmt(x)
                self.emit("LABEL", l_end)
            else:
                self.emit("LABEL", l_else)
        elif isinstance(s, A.While):
            l_start, l_end = self.label(), self.label()
            self.emit("LABEL", l_start)
            c = self.expr(s.cond)
            self.emit("IF_FALSE", c, l_end)
            for x in s.body:
                self.stmt(x)
            self.emit("GOTO", l_start)
            self.emit("LABEL", l_end)

    def expr(self, e):
        if isinstance(e, A.Num):
            return e.value
        if isinstance(e, A.Str):
            return json.dumps(e.value, ensure_ascii=False)
        if isinstance(e, A.Var):
            return e.name
        if isinstance(e, A.Unary):
            x = self.expr(e.operand)
            t = self.temp()
            self.emit("NEG", t, x, ty=e.ty)
            return t
        l, r = self.expr(e.left), self.expr(e.right)
        t = self.temp()
        self.emit("BINOP", t, l, e.op, r, ty=e.ty)
        return t
