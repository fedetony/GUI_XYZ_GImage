import ast
import os
import hashlib
from collections import defaultdict
EXCLUDE_DIRS = {
    "venv", "env", ".venv",
    "__pycache__",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    "build", "dist"
}

def hash_source(source):
    """Normalize and hash function source code."""
    normalized = "\n".join(line.strip() for line in source.splitlines() if line.strip())
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()

def extract_functions_from_file(filepath):
    """Return list of (name, args, body_hash, source, filepath)."""
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            start = node.lineno - 1
            end = node.end_lineno
            func_source = "\n".join(source.splitlines()[start:end])
            body_hash = hash_source(func_source)

            arg_names = [a.arg for a in node.args.args]
            signature = f"{node.name}({', '.join(arg_names)})"

            functions.append({
                "name": node.name,
                "signature": signature,
                "hash": body_hash,
                "source": func_source,
                "file": filepath,
                "line": node.lineno
            })

    return functions

def scan_project(root):
    all_functions = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Remove excluded directories from traversal
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for filename in filenames:
            if filename.endswith(".py"):
                filepath = os.path.join(dirpath, filename)
                all_functions.extend(extract_functions_from_file(filepath))
    return all_functions

def find_duplicates(functions):
    by_name = defaultdict(list)
    by_hash = defaultdict(list)

    for f in functions:
        by_name[f["name"]].append(f)
        by_hash[f["hash"]].append(f)

    print("\n=== FUNCTIONS WITH SAME NAME (possible overrides) ===")
    for name, funcs in by_name.items():
        if len(funcs) > 1:
            print(f"\nFunction name: {name}")
            for f in funcs:
                print(f"  - {f['file']}:{f['line']}  signature={f['signature']}")

    print("\n=== FUNCTIONS WITH IDENTICAL BODIES (copy/paste duplicates) ===")
    for h, funcs in by_hash.items():
        if len(funcs) > 1:
            print(f"\nDuplicate body hash: {h}")
            for f in funcs:
                print(f"  - {f['file']}:{f['line']}  name={f['name']}")

if __name__ == "__main__":
    root = "."  # or your project path
    functions = scan_project(root)
    find_duplicates(functions)