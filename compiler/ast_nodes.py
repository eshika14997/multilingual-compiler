from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class Num:
    value: str
    line: int = 0
    col: int = 0
    ty: str = ""


@dataclass
class Str:
    value: str
    line: int = 0
    col: int = 0
    ty: str = "string"


@dataclass
class Var:
    name: str
    line: int = 0
    col: int = 0
    ty: str = ""


@dataclass
class Unary:
    op: str
    operand: Any
    line: int = 0
    col: int = 0
    ty: str = ""


@dataclass
class Binary:
    op: str
    left: Any
    right: Any
    line: int = 0
    col: int = 0
    ty: str = ""


@dataclass
class Decl:
    ty: str
    name: str
    init: Optional[Any] = None
    line: int = 0
    col: int = 0


@dataclass
class Assign:
    name: str
    value: Any
    line: int = 0
    col: int = 0


@dataclass
class Print:
    args: List[Any]
    line: int = 0
    col: int = 0


@dataclass
class If:
    cond: Any
    then: List[Any]
    orelse: List[Any]
    line: int = 0
    col: int = 0


@dataclass
class While:
    cond: Any
    body: List[Any]
    line: int = 0
    col: int = 0


@dataclass
class Program:
    body: List[Any]


def dump(n, d=0) -> str:
    """Language-independent text view of the AST."""
    p = "  " * d
    if isinstance(n, Program):
        return "\n".join([p + "Program"] + [dump(s, d + 1) for s in n.body])
    if isinstance(n, Decl):
        out = [f"{p}Decl {n.ty} {n.name}"]
        if n.init is not None:
            out.append(dump(n.init, d + 1))
        return "\n".join(out)
    if isinstance(n, Assign):
        return "\n".join([f"{p}Assign {n.name}", dump(n.value, d + 1)])
    if isinstance(n, Print):
        return "\n".join([p + "Print"] + [dump(a, d + 1) for a in n.args])
    if isinstance(n, If):
        out = [p + "If", p + "  Cond", dump(n.cond, d + 2), p + "  Then"]
        out += [dump(s, d + 2) for s in n.then]
        if n.orelse:
            out += [p + "  Else"] + [dump(s, d + 2) for s in n.orelse]
        return "\n".join(out)
    if isinstance(n, While):
        out = [p + "While", p + "  Cond", dump(n.cond, d + 2), p + "  Body"]
        out += [dump(s, d + 2) for s in n.body]
        return "\n".join(out)
    if isinstance(n, Num):
        return f"{p}Num {n.value}"
    if isinstance(n, Str):
        return f'{p}Str "{n.value}"'
    if isinstance(n, Var):
        return f"{p}Var {n.name}"
    if isinstance(n, Unary):
        return "\n".join([f"{p}Unary {n.op}", dump(n.operand, d + 1)])
    if isinstance(n, Binary):
        return "\n".join([f"{p}Binary {n.op}", dump(n.left, d + 1), dump(n.right, d + 1)])
    return p + repr(n)
