import os
import shutil
import signal
import subprocess
import sys
import tempfile
from dataclasses import dataclass

MAX_OUT = 100_000  # characters of program output we keep


@dataclass
class RunResult:
    ok: bool
    output: str = ""
    error: str = ""


def run_c(c_code: str, workdir: str = None, timeout: int = 5) -> RunResult:
    cc = shutil.which("gcc") or shutil.which("cc") or shutil.which("clang")
    if not cc:
        return RunResult(False, error="No C compiler found. Install gcc/clang "
                                      "(Mac: xcode-select --install).")
    own = workdir is None
    workdir = tempfile.mkdtemp(prefix="mlc_") if own else workdir   # separate folder per run
    os.makedirs(workdir, exist_ok=True)
    try:
        src = os.path.join(workdir, "out.c")
        win = sys.platform.startswith("win")
        exe = os.path.join(workdir, "out.exe" if win else "out")
        with open(src, "w", encoding="utf-8") as f:
            f.write(c_code)
        comp = subprocess.run([cc, src, "-o", exe], capture_output=True, text=True)
        if comp.returncode != 0:
            return RunResult(False, error="C compilation failed:\n" + comp.stderr)

        out_path = os.path.join(workdir, "stdout.txt")
        # POSIX: cap the size of the output file so a print-loop cannot fill the disk
        cmd = [exe] if win else ["/bin/sh", "-c", 'ulimit -f 2048; exec "$0"', exe]
        try:
            with open(out_path, "wb") as fo:
                p = subprocess.run(cmd, stdout=fo, stderr=subprocess.DEVNULL,
                                   stdin=subprocess.DEVNULL, timeout=timeout)
        except subprocess.TimeoutExpired:
            out = _read(out_path)
            return RunResult(False, out, f"Program stopped: exceeded {timeout}s (infinite loop?)")
        out = _read(out_path)
        if not win and p.returncode == -getattr(signal, "SIGXFSZ", 25):
            return RunResult(False, out, "Program stopped: too much output")
        if p.returncode != 0:
            return RunResult(False, out, f"Program crashed (exit code {p.returncode})")
        return RunResult(True, output=out)
    finally:
        if own:
            shutil.rmtree(workdir, ignore_errors=True)


def _read(path):
    with open(path, "rb") as f:
        return f.read(MAX_OUT * 4).decode("utf-8", errors="replace")[:MAX_OUT]
