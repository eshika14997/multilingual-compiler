import os
import shutil
import subprocess
import sys
from dataclasses import dataclass


@dataclass
class RunResult:
    ok: bool
    output: str = ""
    error: str = ""


def run_c(c_code: str, workdir: str = "build", timeout: int = 5) -> RunResult:
    cc = shutil.which("gcc") or shutil.which("cc") or shutil.which("clang")
    if not cc:
        return RunResult(False, error="No C compiler found. Install gcc/clang "
                                      "(Mac: xcode-select --install).")
    os.makedirs(workdir, exist_ok=True)
    src = os.path.join(workdir, "out.c")
    exe = os.path.join(workdir, "out.exe" if sys.platform.startswith("win") else "out")
    with open(src, "w", encoding="utf-8") as f:
        f.write(c_code)
    comp = subprocess.run([cc, src, "-o", exe], capture_output=True, text=True)
    if comp.returncode != 0:
        return RunResult(False, error="C compilation failed:\n" + comp.stderr)
    try:
        p = subprocess.run([exe], capture_output=True, timeout=timeout, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return RunResult(False, error=f"Program stopped: exceeded {timeout}s (infinite loop?)")
    out = p.stdout.decode("utf-8", errors="replace")
    if p.returncode != 0:
        return RunResult(False, output=out, error=f"Program crashed (exit code {p.returncode})")
    return RunResult(True, output=out)
