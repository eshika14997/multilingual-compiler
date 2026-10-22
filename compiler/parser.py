from .errors import CompileError
from .dictionary import KeywordDictionary
from . import ast_nodes as A

STARTS = {"INT", "FLOAT", "SET", "PRINT", "IF", "WHILE"}
STOPS = {"ELSE", "END_IF", "END_WHILE"}
COMPARE = {"==", "!=", "<", ">", "<=", ">="}


class ParseError(Exception):
    def __init__(self, msg, tok):
        super().__init__(msg)
        self.msg, self.tok = msg, tok


class Parser:
    """
    Grammar (recursive descent):
      program   -> statement*
      statement -> decl | assign | print | if | while
      decl      -> (INT|FLOAT) IDENT [ '=' expr ] ';'
      assign    -> [SET] IDENT '=' expr ';'
      print     -> PRINT expr (',' expr)* ';'
      if        -> IF expr statement* [ELSE statement*] END_IF
      while     -> WHILE expr statement* END_WHILE
      expr      -> additive [ (== != < > <= >=) additive ]
      additive  -> term (('+'|'-') term)*
      term      -> unary (('*'|'/'|'%') unary)*
      unary     -> '-' unary | primary
      primary   -> NUMBER | STRING | IDENT | '(' expr ')'
    """

    def __init__(self, tokens, lang="en", dictionary=None):
        self.t, self.i, self.lang = tokens, 0, lang
        self.dict = dictionary or KeywordDictionary()
        self.errors = []

    # ---------- helpers ----------
    @property
    def cur(self):
        return self.t[self.i]

    def advance(self):
        tok = self.t[self.i]
        if tok.type != "EOF":
            self.i += 1
        return tok

    def kw(self, canon):
        return f"'{self.dict.word(self.lang, canon)}'"

    def desc(self, tok):
        if tok.type == "EOF":
            return "end of file"
        if tok.type == "KEYWORD":
            return f"keyword '{tok.lexeme}'"
        return f"'{tok.lexeme}'"

    def is_kw(self, *names):
        return self.cur.type == "KEYWORD" and self.cur.value in names

    def is_op(self, *ops):
        return self.cur.type == "OP" and self.cur.value in ops

    def expect(self, ttype, what):
        if self.cur.type != ttype:
            raise ParseError(f"Expected {what} but found {self.desc(self.cur)}", self.cur)
        return self.advance()

    # ---------- error recovery ----------
    def sync(self):
        while self.cur.type != "EOF":
            if self.cur.type == "SEMI":
                self.i += 1
                return
            if self.cur.type == "KEYWORD" and self.cur.value in (STARTS | STOPS):
                return
            self.i += 1

    def safe_statement(self):
        try:
            return self.statement()
        except ParseError as e:
            self.errors.append(CompileError("SYNTAX", e.msg, e.tok.line, e.tok.col))
            self.sync()
            return None

    # ---------- statements ----------
    def parse(self):
        body = []
        while self.cur.type != "EOF":
            s = self.safe_statement()
            if s:
                body.append(s)
        return A.Program(body), self.errors

    def block(self, stops, closer, opener):
        body = []
        while not self.is_kw(*stops):
            if self.cur.type == "EOF":
                self.errors.append(CompileError(
                    "SYNTAX", f"Missing {self.kw(closer)} for block opened at line {opener.line}",
                    self.cur.line, self.cur.col))
                return body, False
            s = self.safe_statement()
            if s:
                body.append(s)
        return body, True

    def statement(self):
        tok = self.cur
        if tok.type == "KEYWORD":
            c = tok.value
            if c in ("INT", "FLOAT"):
                return self.decl()
            if c == "SET":
                return self.assign(True)
            if c == "PRINT":
                return self.print_stmt()
            if c == "IF":
                return self.if_stmt()
            if c == "WHILE":
                return self.while_stmt()
            self.advance()
            raise ParseError(f"Unexpected {self.desc(tok)} here (no matching block is open)", tok)
        if tok.type == "IDENT" and self.t[self.i + 1].type == "OP" and self.t[self.i + 1].value == "=":
            return self.assign(False)
        self.advance()
        raise ParseError(f"Unexpected {self.desc(tok)} at the start of a statement", tok)

    def decl(self):
        tok = self.advance()
        ty = "int" if tok.value == "INT" else "float"
        name = self.expect("IDENT", "a variable name")
        init = None
        if self.is_op("="):
            self.advance()
            init = self.expr()
        self.expect("SEMI", "';'")
        return A.Decl(ty, name.value, init, tok.line, tok.col)

    def assign(self, with_set):
        tok = self.advance() if with_set else self.cur
        name = self.expect("IDENT", "a variable name")
        if not self.is_op("="):
            raise ParseError(f"Expected '=' but found {self.desc(self.cur)}", self.cur)
        self.advance()
        value = self.expr()
        self.expect("SEMI", "';'")
        return A.Assign(name.value, value, tok.line, tok.col)

    def print_stmt(self):
        tok = self.advance()
        args = [self.expr()]
        while self.cur.type == "COMMA":
            self.advance()
            args.append(self.expr())
        self.expect("SEMI", "';'")
        return A.Print(args, tok.line, tok.col)

    def if_stmt(self):
        tok = self.advance()
        cond = self.expr()
        then, ok = self.block({"ELSE", "END_IF"}, "END_IF", tok)
        orelse = []
        if ok and self.is_kw("ELSE"):
            self.advance()
            orelse, ok = self.block({"END_IF"}, "END_IF", tok)
        if ok:
            self.advance()
        return A.If(cond, then, orelse, tok.line, tok.col)

    def while_stmt(self):
        tok = self.advance()
        cond = self.expr()
        body, ok = self.block({"END_WHILE"}, "END_WHILE", tok)
        if ok:
            self.advance()
        return A.While(cond, body, tok.line, tok.col)

    # ---------- expressions ----------
    def expr(self):
        left = self.additive()
        while self.is_op(*COMPARE):
            op = self.advance()
            left = A.Binary(op.value, left, self.additive(), op.line, op.col)
        return left

    def additive(self):
        left = self.term()
        while self.is_op("+", "-"):
            op = self.advance()
            left = A.Binary(op.value, left, self.term(), op.line, op.col)
        return left

    def term(self):
        left = self.unary()
        while self.is_op("*", "/", "%"):
            op = self.advance()
            left = A.Binary(op.value, left, self.unary(), op.line, op.col)
        return left

    def unary(self):
        if self.is_op("-"):
            op = self.advance()
            return A.Unary("-", self.unary(), op.line, op.col)
        return self.primary()

    def primary(self):
        t = self.cur
        if t.type == "NUMBER":
            self.advance()
            return A.Num(t.value, t.line, t.col)
        if t.type == "STRING":
            self.advance()
            return A.Str(t.value, t.line, t.col)
        if t.type == "IDENT":
            self.advance()
            return A.Var(t.value, t.line, t.col)
        if t.type == "LPAREN":
            self.advance()
            e = self.expr()
            self.expect("RPAREN", "')'")
            return e
        raise ParseError(f"Expected an expression but found {self.desc(t)}", t)
