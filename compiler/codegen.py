C_TYPES = {"int": "int", "float": "double"}


def cname(n: str) -> str:
    """Safe C identifier for a user variable (handles Hindi/Gujarati names)."""
    if n.isascii() and n.isidentifier():
        return "v_" + n
    return "u_" + "_".join(f"{ord(c):x}" for c in n)


def cop(x: str) -> str:
    if x.startswith("%"):
        return "t" + x[2:]
    if x.startswith('"') or x[0].isdigit():
        return x
    return cname(x)


def generate_c(ir) -> str:
    decls, temps = {}, {}
    for i in ir:
        if i.op == "DECL":
            decls[i.args[0]] = i.ty
        elif i.op in ("BINOP", "NEG"):
            temps[i.args[0]] = i.ty

    L = ["#include <stdio.h>", "", "int main(void) {"]
    for name, ty in decls.items():
        L.append(f"    {C_TYPES[ty]} {cname(name)} = 0;")
    for name, ty in temps.items():
        L.append(f"    {C_TYPES[ty]} {cop(name)} = 0;")
    if decls or temps:
        L.append("")

    for i in ir:
        a = i.args
        if i.op == "ASSIGN":
            L.append(f"    {cname(a[0])} = {cop(a[1])};")
        elif i.op == "BINOP":
            L.append(f"    {cop(a[0])} = {cop(a[1])} {a[2]} {cop(a[3])};")
        elif i.op == "NEG":
            L.append(f"    {cop(a[0])} = -{cop(a[1])};")
        elif i.op == "LABEL":
            L.append(f"  {a[0]}: ;")
        elif i.op == "GOTO":
            L.append(f"    goto {a[0]};")
        elif i.op == "IF_FALSE":
            L.append(f"    if (!({cop(a[0])})) goto {a[1]};")
        elif i.op == "PRINT":
            fmt = {"int": "%d", "float": "%g", "string": "%s"}[i.ty]
            L.append(f'    printf("{fmt}", {cop(a[0])});')
        elif i.op == "PRINTLN":
            L.append('    printf("\\n");')
    L += ["    return 0;", "}", ""]
    return "\n".join(L)
