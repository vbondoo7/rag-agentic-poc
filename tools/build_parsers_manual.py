import os
import subprocess
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")

BASE_DIR = Path(__file__).resolve().parent.parent
GRAMMARS = {
    "tree-sitter-java": ["src/parser.c"],
    "tree-sitter-python": ["src/parser.c", "src/scanner.c"],
    "tree-sitter-go": ["src/parser.c"],
    "tree-sitter-javascript": ["src/parser.c", "src/scanner.c"],
   # "tree-sitter-typescript/typescript": ["src/parser.c", "src/scanner.c"],
    "tree-sitter-json": ["src/parser.c"],
    "tree-sitter-yaml": ["src/parser.c", "src/scanner.c"],
}

OUT_LIB = BASE_DIR / "parsers" / "my-languages.so"
TMP_OBJS = []

logging.info(f"🔧 Compiling grammars manually for Apple Silicon...")
os.makedirs(OUT_LIB.parent, exist_ok=True)

INCLUDE_PATH = BASE_DIR / ".venv" / "include"
if not INCLUDE_PATH.exists():
    INCLUDE_PATH = "/opt/homebrew/include"  # fallback

for name, files in GRAMMARS.items():
    grammar_dir = BASE_DIR / "parsers" / "grammars" / name
    for file in files:
        src = grammar_dir / file
        if not src.exists():
            logging.warning(f"⚠️ Missing: {src}, skipping.")
            continue
        obj = src.with_suffix(".o")
        TMP_OBJS.append(str(obj))
        logging.info(f"🧩 Compiling {src} ...")
        subprocess.run([
            "clang",
            "-O2",
            "-fPIC",
            "-arch", "arm64",
            "-I", str(grammar_dir),
            "-I", str(INCLUDE_PATH),
            "-I", "parsers/include",   # 👈 Add this line
            "-I", "parsers/include/tree_sitter",
            "-c", str(src),
            "-o", str(obj)
        ], check=True)

logging.info("🔗 Linking all grammars into a shared library...")
cmd = [
    "clang",
    "-dynamiclib",
    "-arch", "arm64",
    "-undefined", "dynamic_lookup",
    "-o", str(OUT_LIB),
] + TMP_OBJS
subprocess.run(cmd, check=True)
logging.info(f"✅ Done! Library created at: {OUT_LIB}")
