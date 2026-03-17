import ast
import os


class DocstringCoverage:

    def calculate(self, code):
        tree = ast.parse(code)
        total = 0
        documented = 0

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                total += 1
                if ast.get_docstring(node):
                    documented += 1

        percent = round((documented / total) * 100, 2) if total else 100

        return {
            "total_objects": total,
            "documented_objects": documented,
            "coverage_percent": percent
        }

    def calculate_project(self, root=".", exclude=None):
        if exclude is None:
            exclude = ["venv", "__pycache__", ".git"]

        total = 0
        documented = 0

        for dirpath, _, filenames in os.walk(root):
            if any(x in dirpath for x in exclude):
                continue

            for file in filenames:
                if file.endswith(".py"):
                    path = os.path.join(dirpath, file)

                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            code = f.read()

                        result = self.calculate(code)
                        total += result["total_objects"]
                        documented += result["documented_objects"]

                    except Exception:
                        continue

        percent = round((documented / total) * 100, 2) if total else 100

        return {
            "total_objects": total,
            "documented_objects": documented,
            "coverage_percent": percent
        }