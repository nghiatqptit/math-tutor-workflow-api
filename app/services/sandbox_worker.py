from __future__ import annotations

import ast
import builtins
import json
import os
import sys
from typing import Any

ALLOWED_IMPORTS = {"sympy", "math", "numpy"}
BLOCKED_NAMES = {
    "os",
    "sys",
    "subprocess",
    "open",
    "eval",
    "exec",
    "compile",
    "input",
    "__import__",
}


def _safe_builtins() -> dict[str, Any]:
    names = ["abs", "all", "any", "float", "int", "len", "max", "min", "pow", "range", "round", "sum"]
    return {name: getattr(builtins, name) for name in names}


def _validate_code(code: str) -> None:
    tree = ast.parse(code)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in ALLOWED_IMPORTS:
                    raise ValueError(f"Disallowed import: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            root = module.split(".")[0]
            if root not in ALLOWED_IMPORTS:
                raise ValueError(f"Disallowed import from: {module}")
        elif isinstance(node, ast.Name) and node.id in BLOCKED_NAMES:
            raise ValueError(f"Blocked symbol: {node.id}")


def _apply_memory_limit(memory_mb: int) -> None:
    try:
        import resource

        memory_bytes = int(memory_mb) * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
    except Exception:
        return


def run(code: str, memory_mb: int) -> dict[str, Any]:
    if len(code) > 6000:
        return {"execution_success": False, "evaluated_result": None, "error": "Code exceeds size limit"}

    _apply_memory_limit(memory_mb)

    try:
        _validate_code(code)
    except Exception as error:
        return {"execution_success": False, "evaluated_result": None, "error": str(error)}

    safe_globals: dict[str, Any] = {"__builtins__": _safe_builtins()}
    safe_locals: dict[str, Any] = {}

    try:
        compiled = compile(code, "<sandbox>", "exec")
        exec(compiled, safe_globals, safe_locals)
        value = safe_locals.get("result", safe_globals.get("result"))
        if value is None:
            return {
                "execution_success": True,
                "evaluated_result": "result variable not set",
                "error": None,
            }
        return {
            "execution_success": True,
            "evaluated_result": str(value),
            "error": None,
        }
    except Exception as error:
        return {"execution_success": False, "evaluated_result": None, "error": str(error)}


def main() -> None:
    raw = sys.stdin.read().strip()
    if not raw:
        print(json.dumps({"execution_success": False, "evaluated_result": None, "error": "Empty input"}))
        return

    payload = json.loads(raw)
    code = payload.get("code", "")
    memory_mb = int(payload.get("memory_mb", 128))

    os.environ.clear()
    result = run(code=code, memory_mb=memory_mb)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
