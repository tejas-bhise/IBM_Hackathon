"""
services/parser.py — NEW FILE
Code structure parser. Zero LLM calls. Zero tokens.
Uses Python AST + regex for all languages.
Used by: memory, chat_engine, summarizer, pipeline.
"""
import ast
import re
from typing import Any


# ── Python AST parsers ────────────────────────────────────────────────────────

def extract_functions_python(code: str) -> list:
    """
    Extract function names from Python using AST.
    Returns list of strings. Falls back to regex if syntax error.
    """
    try:
        tree = ast.parse(code)
        return [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
    except SyntaxError:
        # Regex fallback for partial/invalid Python
        return re.findall(r'^\s*(?:async\s+)?def\s+(\w+)\s*\(', code, re.MULTILINE)
    except Exception:
        return []

def extract_classes_python(code: str) -> list:
    """Extract class names from Python using AST."""
    try:
        tree = ast.parse(code)
        return [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    except Exception:
        return re.findall(r'^\s*class\s+(\w+)', code, re.MULTILINE)

def extract_function_signatures(code: str) -> list:
    """
    Returns list of {name, args, lineno, is_async} for each function.
    Used by chat engine for richer no-LLM answers.
    """
    try:
        tree = ast.parse(code)
        result = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = []
                for a in node.args.args:
                    arg_entry: dict[str, Any] = {"name": a.arg}
                    if a.annotation and isinstance(a.annotation, ast.Name):
                        arg_entry["type"] = a.annotation.id
                    args.append(arg_entry)
                result.append({
                    "name":      node.name,
                    "args":      args,
                    "lineno":    node.lineno,
                    "is_async":  isinstance(node, ast.AsyncFunctionDef),
                    "docstring": ast.get_docstring(node) or "",
                })
        return result
    except Exception:
        return []

def extract_decorators(code: str) -> list:
    """Extract decorator names from Python code."""
    try:
        tree = ast.parse(code)
        found = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for d in node.decorator_list:
                    if isinstance(d, ast.Name):
                        found.append(d.id)
                    elif isinstance(d, ast.Attribute):
                        found.append(f"{d.value.id}.{d.attr}" if isinstance(d.value, ast.Name) else d.attr)
                    elif isinstance(d, ast.Call):
                        if isinstance(d.func, ast.Attribute):
                            found.append(f"{d.func.value.id}.{d.func.attr}" if isinstance(d.func.value, ast.Name) else d.func.attr)
        return list(dict.fromkeys(found))  # dedup preserving order
    except Exception:
        return []

def extract_imports_python(code: str) -> list:
    """Extract import names from Python using AST."""
    try:
        tree  = ast.parse(code)
        found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    found.append(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    found.append(node.module.split(".")[0])
        return sorted(set(found))
    except Exception:
        return re.findall(r'^(?:import|from)\s+([\w.]+)', code, re.MULTILINE)

def extract_constants(code: str) -> list:
    """Extract module-level constant names (ALL_CAPS variables)."""
    try:
        tree  = ast.parse(code)
        found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        found.append(target.id)
        return found
    except Exception:
        return re.findall(r'^([A-Z][A-Z0-9_]{2,})\s*=', code, re.MULTILINE)


# ── Multi-language regex parsers ───────────────────────────────────────────────

def extract_functions_js(code: str) -> list:
    """Extract function names from JS/TS using regex."""
    found = set()
    # function declarations
    for m in re.finditer(r'\bfunction\s+(\w+)\s*\(', code):
        found.add(m.group(1))
    # arrow functions / const declarations
    for m in re.finditer(r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(', code):
        found.add(m.group(1))
    # class methods
    for m in re.finditer(r'^\s{2,}(?:async\s+)?(\w+)\s*\(', code, re.MULTILINE):
        name = m.group(1)
        if name not in ("if", "while", "for", "switch", "catch", "function"):
            found.add(name)
    return sorted(found)

def extract_classes_js(code: str) -> list:
    """Extract class names from JS/TS."""
    return re.findall(r'\bclass\s+(\w+)', code)

def extract_routes_express(code: str) -> list:
    """Extract Express.js routes (app.get, router.post, etc.)."""
    found = []
    for m in re.finditer(r"""(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*['"]([^'"]+)['"]""", code):
        found.append({"method": m.group(1).upper(), "path": m.group(2)})
    return found

def extract_routes_fastapi(code: str) -> list:
    """Extract FastAPI / Flask routes from Python."""
    found = []
    for m in re.finditer(r"""@(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*['"]([^'"]+)['"]""", code):
        found.append({"method": m.group(1).upper(), "path": m.group(2)})
    return found

def extract_java_methods(code: str) -> list:
    """Extract method names from Java."""
    return re.findall(
        r'(?:public|private|protected|static|final|\s)+\s+\w+\s+(\w+)\s*\(',
        code
    )

def extract_go_functions(code: str) -> list:
    """Extract function names from Go."""
    return re.findall(r'^func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(', code, re.MULTILINE)


# ── Unified parser dispatcher ──────────────────────────────────────────────────

def parse_file(path: str, content: str) -> dict:
    """
    Parse any file and return extracted structure.
    Dispatcher chooses AST (Python) or regex (everything else).
    Returns a unified dict usable by memory, chat, summarizer, pipeline.
    """
    ext = ("." + path.rsplit(".", 1)[-1].lower()) if "." in path else ""

    if ext == ".py":
        functions = extract_functions_python(content)
        classes   = extract_classes_python(content)
        imports   = extract_imports_python(content)
        routes    = extract_routes_fastapi(content)
        sigs      = extract_function_signatures(content)
        constants = extract_constants(content)
        decorators = extract_decorators(content)
        return {
            "path":        path,
            "language":    "python",
            "functions":   functions,
            "classes":     classes,
            "imports":     imports,
            "routes":      routes,
            "signatures":  sigs,
            "constants":   constants,
            "decorators":  decorators,
        }

    elif ext in (".js", ".jsx"):
        functions = extract_functions_js(content)
        classes   = extract_classes_js(content)
        routes    = extract_routes_express(content)
        return {
            "path":       path,
            "language":   "javascript",
            "functions":  functions,
            "classes":    classes,
            "imports":    re.findall(r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)""", content),
            "routes":     routes,
            "signatures": [],
            "constants":  [],
        }

    elif ext in (".ts", ".tsx"):
        functions = extract_functions_js(content)
        classes   = extract_classes_js(content)
        imports   = re.findall(r"""from\s+['"]([^'"]+)['"]""", content)
        return {
            "path":       path,
            "language":   "typescript",
            "functions":  functions,
            "classes":    classes,
            "imports":    imports,
            "routes":     [],
            "signatures": [],
            "constants":  [],
        }

    elif ext == ".java":
        return {
            "path":       path,
            "language":   "java",
            "functions":  extract_java_methods(content),
            "classes":    re.findall(r'\bclass\s+(\w+)', content),
            "imports":    re.findall(r'^import\s+([\w.]+);', content, re.MULTILINE),
            "routes":     [],
            "signatures": [],
            "constants":  [],
        }

    elif ext == ".go":
        return {
            "path":       path,
            "language":   "go",
            "functions":  extract_go_functions(content),
            "classes":    re.findall(r'\btype\s+(\w+)\s+struct', content),
            "imports":    re.findall(r'"([\w./]+)"', content),
            "routes":     [],
            "signatures": [],
            "constants":  [],
        }

    else:
        # Generic regex fallback
        return {
            "path":       path,
            "language":   "unknown",
            "functions":  re.findall(r'\bfunction\s+(\w+)\s*\(', content),
            "classes":    re.findall(r'\bclass\s+(\w+)', content),
            "imports":    [],
            "routes":     [],
            "signatures": [],
            "constants":  [],
        }


# ── Bulk parser for pipeline ───────────────────────────────────────────────────

def parse_all_files(files: list) -> dict:
    """
    Parse all project files at ingestion time.
    Returns precomputed structure dict stored in DB — used by chat at query time.

    Returns:
        {
          "functions":  {filename: [fn_name, ...]},
          "classes":    {filename: [cls_name, ...]},
          "routes":     [{method, path, file}, ...],
          "endpoints":  [{method, path, file}, ...],   ← alias
          "all_functions": [fn_name, ...],              ← flat list
          "all_classes":   [cls_name, ...],
          "signatures": {fn_name: {args, lineno, ...}},
        }
    """
    functions_map: dict  = {}
    classes_map: dict    = {}
    all_routes: list     = []
    all_functions: list  = []
    all_classes: list    = []
    signatures: dict     = {}

    for f in files:
        path    = f.get("path", "")
        content = f.get("content", "")
        if not content:
            continue

        parsed = parse_file(path, content)

        fns  = parsed.get("functions", [])
        clss = parsed.get("classes",   [])
        rts  = parsed.get("routes",    [])
        sigs = parsed.get("signatures", [])

        if fns:
            functions_map[path] = fns
            all_functions.extend(fns)

        if clss:
            classes_map[path] = clss
            all_classes.extend(clss)

        for r in rts:
            all_routes.append({**r, "file": path} if isinstance(r, dict) else {"path": r, "file": path})

        for sig in sigs:
            signatures[sig["name"]] = {
                "args":      sig.get("args", []),
                "lineno":    sig.get("lineno", 0),
                "is_async":  sig.get("is_async", False),
                "docstring": sig.get("docstring", ""),
                "file":      path,
            }

    return {
        "functions":     functions_map,
        "classes":       classes_map,
        "routes":        all_routes,
        "endpoints":     all_routes,      # alias
        "all_functions": list(dict.fromkeys(all_functions)),  # dedup
        "all_classes":   list(dict.fromkeys(all_classes)),
        "signatures":    signatures,
        "total_functions": len(all_functions),
        "total_classes":   len(all_classes),
        "total_routes":    len(all_routes),
    }