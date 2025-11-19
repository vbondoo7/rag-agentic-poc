import os
from tree_sitter import Language

base_dir = os.path.dirname(__file__) if '__file__' in globals() else os.getcwd()
lib_path = os.path.abspath(os.path.join(base_dir, "../parsers/my-languages.so"))

grammars = [
    os.path.abspath(os.path.join(base_dir, "../parsers/grammars/tree-sitter-java")),
    os.path.abspath(os.path.join(base_dir, "../parsers/grammars/tree-sitter-python")),
    os.path.abspath(os.path.join(base_dir, "../parsers/grammars/tree-sitter-go")),
    os.path.abspath(os.path.join(base_dir, "../parsers/grammars/tree-sitter-javascript")),
    os.path.abspath(os.path.join(base_dir, "../parsers/grammars/tree-sitter-typescript/typescript")),
    os.path.abspath(os.path.join(base_dir, "../parsers/grammars/tree-sitter-json")),
    os.path.abspath(os.path.join(base_dir, "../parsers/grammars/tree-sitter-yaml")),
]

print("🔧 Building parsers into:", lib_path)
os.environ["LDFLAGS"] = "-dynamiclib -undefined dynamic_lookup -fPIC"

try:
    Language.build_library(lib_path, grammars)
    print("✅ Successfully built:", lib_path)
except Exception as e:
    print("❌ Build failed:", e)
