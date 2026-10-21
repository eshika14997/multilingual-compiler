from dataclasses import dataclass


@dataclass
class CompileError:
    kind: str      # LEXICAL | MIXED_LANGUAGE | DICTIONARY | SYNTAX | SEMANTIC
    message: str
    line: int = 0
    col: int = 0

    def __str__(self):
        loc = f" (line {self.line}, col {self.col})" if self.line else ""
        return f"[{self.kind}]{loc} {self.message}"
