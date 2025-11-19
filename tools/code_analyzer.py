# tools/code_analyzer.py
"""
Analyze code files in repo and write per-file metadata JSON into data/metadata/.
This uses tree-sitter if available, otherwise falls back to regex heuristics.
"""

import os
import re
import json
from pathlib import Path
from logger import log

# Try optional tree-sitter path
try:
    from tree_sitter_languages import get_parser, get_language
    HAS_TREESITTER = True
except Exception:
    HAS_TREESITTER = False
    log = log

SUPPORTED_EXTS = {".py", ".java", ".go", ".js", ".ts", ".json", ".yaml", ".yml", ".md"}

def _short_from_comments(text):
    # first docstring/comment-ish line
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("#") or s.startswith("//") or s.startswith("/*") or s.startswith("---"):
            return s.lstrip("#/ *-").strip()
        if len(s) > 30:
            return s[:200].strip()
    return ""

def _heuristic_imports(text):
    imports = set()
    for m in re.finditer(r'^\s*(?:from\s+([\w\.]+)\s+import|import\s+([\w\.]+))', text, re.M):
        module = m.group(1) or m.group(2)
        if module:
            imports.add(module)
    for m in re.finditer(r'\bpackage\s+([\w\.]+)', text):
        imports.add(m.group(1))
    return list(imports)

def analyze_file(path: str, metadata_dir: str):
    ext = Path(path).suffix.lower()
    if ext not in SUPPORTED_EXTS:
        return None
    try:
        with open(path, "r", encoding="utf8", errors="ignore") as fh:
            txt = fh.read()
    except Exception as e:
        log.error(f"Could not read {path}: {e}")
        return None

    meta = {"file": path, "language": ext.lstrip("."), "short_description": _short_from_comments(txt)}

    # imports heuristics
    meta["imports"] = _heuristic_imports(txt)

    # simple heuristics for external calls
    calls = []
    if re.search(r'\brequests\.', txt): calls.append("http:requests")
    if re.search(r'\bhttp\.', txt): calls.append("http")
    if re.search(r'grpc\.', txt) or "grpc" in txt: calls.append("grpc")
    if re.search(r'\bredis\b', txt, re.I): calls.append("redis")
    if re.search(r'\bjdbc:|DriverManager.getConnection|sqlalchemy', txt, re.I): calls.append("database")
    meta["external_calls"] = calls

    # Functions/classes extraction: try tree-sitter if available
    functions = []
    classes = []
    try:
        if HAS_TREESITTER:
            parser = get_parser(meta["language"])
            lang = get_language(meta["language"])
            parser.set_language(lang)
            tree = parser.parse(bytes(txt, "utf8"))
            root = tree.root_node

            # walk for common node types
            def walk(node):
                for ch in node.children:
                    try:
                        if ch.type in ("function_definition", "function_declaration", "method_definition", "def", "function"):
                            # attempt name extraction (safe)
                            name = txt[ch.start_byte:ch.end_byte].split("(")[0].strip().split()[-1]
                            functions.append(name)
                        if ch.type in ("class_definition", "class_declaration", "class"):
                            name = txt[ch.start_byte:ch.end_byte].split(":")[0].strip().split()[-1]
                            classes.append(name)
                    except Exception:
                        pass
                    walk(ch)
            walk(root)
    except Exception as e:
        log.warning(f"tree-sitter analysis skipped/failed for {path}: {e}")

    # fallback heuristics if empty
    if not functions:
        functions = re.findall(r'^\s*def\s+([A-Za-z0-9_]+)\s*\(', txt, re.M)
        functions += re.findall(r'function\s+([A-Za-z0-9_]+)\s*\(', txt)
    if not classes:
        classes = re.findall(r'^\s*class\s+([A-Za-z0-9_]+)\s*[:\(]', txt, re.M)

    meta["functions"] = list(dict.fromkeys(functions))[:80]
    meta["classes"] = list(dict.fromkeys(classes))[:80]

    # Save metadata JSON
    os.makedirs(metadata_dir, exist_ok=True)
    safe_name = path.replace(os.sep, "__")
    out = os.path.join(metadata_dir, safe_name + ".json")
    try:
        with open(out, "w", encoding="utf8") as fh:
            json.dump(meta, fh, indent=2)
    except Exception as e:
        log.error(f"Failed to write metadata for {path}: {e}")
        return None

    log.info(f"analyzed {path} -> {out}")
    return meta

def analyze_folder(root_folder: str, metadata_dir: str):
    metas = []
    for root, _, files in os.walk(root_folder):
        for f in files:
            p = os.path.join(root, f)
            if Path(p).suffix.lower() in SUPPORTED_EXTS:
                m = analyze_file(p, metadata_dir)
                if m:
                    metas.append(m)
    return metas

if __name__ == "__main__":
    import sys
    repo = sys.argv[1] if len(sys.argv) > 1 else "./sample_codebase"
    md = sys.argv[2] if len(sys.argv) > 2 else "data/metadata"
    analyze_folder(repo, md)
    print("analysis complete")
