#!/usr/bin/env python3
import os
import sys
import logging
from tree_sitter_languages import get_parser

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

SUPPORTED_LANGUAGES = {
    "py": "python",
    "java": "java",
    "go": "go",
    "js": "javascript",
    "ts": "typescript",
}


def detect_language(filepath):
    ext = filepath.split(".")[-1]
    return SUPPORTED_LANGUAGES.get(ext, None)


def parse_file(filepath):
    language_name = detect_language(filepath)
    if not language_name:
        raise ValueError(f"Unsupported file extension for {filepath}")

    logging.info(f"🔍 Detected language: {language_name}")

    try:
        # ✅ get_parser gives a ready-to-use parser instance
        parser = get_parser(language_name)
    except Exception as e:
        logging.error(f"❌ Failed to initialize parser for {language_name}: {e}")
        raise

    with open(filepath, "r", encoding="utf-8") as f:
        source_code = f.read().encode("utf8")

    try:
        tree = parser.parse(source_code)
    except Exception as e:
        logging.error(f"❌ Parsing error: {e}")
        raise

    root_node = tree.root_node
    logging.info(f"✅ Parsed successfully. Root node: {root_node.type}")

    extract_summary(language_name, source_code, root_node)


def extract_summary(language, source_code, root_node):
    """Minimal AST summary: lists top-level defs."""
    logging.info("📜 Extracting structure summary...")
    cursor = root_node.walk()
    visited = set()

    def walk(node, depth=0):
        if node.id in visited:
            return
        visited.add(node.id)

        indent = "  " * depth
        if node.type in ("function_definition", "class_definition", "method_definition"):
            snippet = (
                source_code[node.start_byte:node.end_byte]
                .decode("utf-8")
                .splitlines()[0]
            )
            logging.info(f"{indent}- {node.type}: {snippet.strip()}")

        for child in node.children:
            walk(child, depth + 1)

    walk(root_node)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python tools/code_analyzer.py <path_to_source_file>")
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        sys.exit(1)

    try:
        parse_file(filepath)
    except Exception as e:
        logging.error(f"💥 Failed to initialize or parse: {e}")
        sys.exit(1)
