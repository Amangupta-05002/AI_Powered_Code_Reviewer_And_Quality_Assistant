import os
import ast


def scan_project_files(folder_path):

    results = {}

    for root, dirs, files in os.walk(folder_path):

        for file in files:

            if file.endswith(".py"):

                path = os.path.join(root, file)

                with open(path, "r", encoding="utf-8") as f:
                    code = f.read()

                functions = []

                try:
                    tree = ast.parse(code)
                except:
                    continue

                for node in ast.walk(tree):

                    if isinstance(node, ast.FunctionDef):

                        doc = ast.get_docstring(node)

                        start = node.lineno
                        end = node.end_lineno

                        lines = code.splitlines()[start-1:end]

                        functions.append({
                            "name": node.name,
                            "code": "\n".join(lines),
                            "docstring": doc
                        })

                results[path] = functions

    return results