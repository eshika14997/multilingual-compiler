from .errors import CompileError
from . import ast_nodes as A

COMPARE = {"==", "!=", "<", ">", "<=", ">="}


class SemanticAnalyzer:
    """Declaration checks + simple type checking (int / float; strings only inside print)."""

    def __init__(self):
        self.sym = {}
        self.errors = []

    def err(self, msg, node):
        self.errors.append(CompileError("SEMANTIC", msg, node.line, node.col))

    def analyze(self, program):
        self.block(program.body)
        return self.errors

    def block(self, stmts):
        for s in stmts:
            self.stmt(s)

    def check_assign(self, name, target_ty, val_ty, node):
        if target_ty == "int" and val_ty == "float":
            self.err(f"Cannot assign a float value to int variable '{name}'", node)

    def stmt(self, s):
        if isinstance(s, A.Decl):
            val_ty = self.expr(s.init) if s.init is not None else None
            if s.name in self.sym:
                self.err(f"Variable '{s.name}' is already declared", s)
            else:
                self.sym[s.name] = s.ty
            if val_ty:
                self.check_assign(s.name, s.ty, val_ty, s)
        elif isinstance(s, A.Assign):
            val_ty = self.expr(s.value)
            if s.name not in self.sym:
                self.err(f"Variable '{s.name}' is used before declaration", s)
            else:
                self.check_assign(s.name, self.sym[s.name], val_ty, s)
        elif isinstance(s, A.Print):
            for a in s.args:
                self.expr(a, allow_str=True)
        elif isinstance(s, A.If):
            self.expr(s.cond)
            self.block(s.then)
            self.block(s.orelse)
        elif isinstance(s, A.While):
            self.expr(s.cond)
            self.block(s.body)

    def expr(self, e, allow_str=False):
        if isinstance(e, A.Num):
            e.ty = "float" if "." in e.value else "int"
        elif isinstance(e, A.Str):
            if not allow_str:
                self.err("String values can only be used inside print", e)
                e.ty = "int"
            else:
                e.ty = "string"
        elif isinstance(e, A.Var):
            if e.name not in self.sym:
                self.err(f"Variable '{e.name}' is used before declaration", e)
                e.ty = "int"
            else:
                e.ty = self.sym[e.name]
        elif isinstance(e, A.Unary):
            e.ty = self.expr(e.operand)
        elif isinstance(e, A.Binary):
            lt, rt = self.expr(e.left), self.expr(e.right)
            if e.op in COMPARE:
                e.ty = "int"
            else:
                if e.op == "%" and "float" in (lt, rt):
                    self.err("Operator '%' needs int operands", e)
                e.ty = "float" if "float" in (lt, rt) else "int"
            if e.op in ("/", "%") and isinstance(e.right, A.Num) and float(e.right.value) == 0:
                self.err("Division by zero", e)
        return e.ty
