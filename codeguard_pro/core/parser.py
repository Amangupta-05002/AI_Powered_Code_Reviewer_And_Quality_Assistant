import ast

class CodeParser:
    def __init__(self, code: str):
        self.code = code
        self.tree = ast.parse(code)

    def extract(self):
        result = {
            "functions": [],
            "classes": [],
            "imports": []
        }

        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                result["functions"].append({
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "lineno": node.lineno,
                    "docstring": ast.get_docstring(node)
                })

            if isinstance(node, ast.ClassDef):
                result["classes"].append({
                    "name": node.name,
                    "lineno": node.lineno
                })

            if isinstance(node, ast.Import):
                for alias in node.names:
                    result["imports"].append(alias.name)

        return result