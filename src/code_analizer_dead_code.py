import ast
import os
from collections import defaultdict
EXCLUDE_DIRS = {
    "venv", "env", ".venv",
    "__pycache__",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    "build", "dist"
}

class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.defined_funcs = set()
        self.called_funcs = set()

        self.defined_classes = set()
        self.instantiated_classes = set()

        self.imported_names = set()
        self.used_names = set()

        self.assigned_vars = set()
        self.used_vars = set()

    def visit_FunctionDef(self, node):
        self.defined_funcs.add(node.name)
        self.generic_visit(node)

    def visit_Call(self, node):
        # function calls
        if isinstance(node.func, ast.Name):
            self.called_funcs.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.called_funcs.add(node.func.attr)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.defined_classes.add(node.name)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        self.used_names.add(node.attr)
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
            self.used_vars.add(node.id)
        elif isinstance(node.ctx, ast.Store):
            self.assigned_vars.add(node.id)
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            self.imported_names.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.imported_names.add(alias.asname or alias.name)
        self.generic_visit(node)


def analyze_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            return None

    analyzer = CodeAnalyzer()
    analyzer.visit(tree)
    return analyzer

def scan_project(root):
    combined = CodeAnalyzer()

    for dirpath, dirnames, filenames in os.walk(root):
        # Remove excluded directories from traversal
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]

        for filename in filenames:
            if filename.endswith(".py"):
                result = analyze_file(os.path.join(dirpath, filename))
                if result:
                    combined.defined_funcs |= result.defined_funcs
                    combined.called_funcs |= result.called_funcs

                    combined.defined_classes |= result.defined_classes
                    combined.instantiated_classes |= result.used_names

                    combined.imported_names |= result.imported_names
                    combined.used_names |= result.used_names

                    combined.assigned_vars |= result.assigned_vars
                    combined.used_vars |= result.used_vars

    return combined


def report_dead_code(analyzer):
    print("\n=== DEAD FUNCTIONS (defined but never called) ===")
    for f in sorted(analyzer.defined_funcs - analyzer.called_funcs):
        print("  ", f)

    print("\n=== DEAD CLASSES (defined but never instantiated) ===")
    for c in sorted(analyzer.defined_classes - analyzer.instantiated_classes):
        print("  ", c)

    print("\n=== UNUSED IMPORTS ===")
    for imp in sorted(analyzer.imported_names - analyzer.used_names):
        print("  ", imp)

    print("\n=== UNUSED VARIABLES ===")
    for var in sorted(analyzer.assigned_vars - analyzer.used_vars):
        print("  ", var)


if __name__ == "__main__":
    root = "."  # or your project path
    analyzer = scan_project(root)
    report_dead_code(analyzer)