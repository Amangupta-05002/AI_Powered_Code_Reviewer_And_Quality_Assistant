import ast


def collect_function_data(files_dict):
    """
    Extract functions and docstring status from project files.
    """

    functions = []

    for file_name, code in files_dict.items():

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):

                if isinstance(node, ast.FunctionDef):

                    doc = ast.get_docstring(node)

                    functions.append(
                        {
                            "file": file_name,
                            "function": node.name,
                            "status": "OK" if doc else "Missing",
                            "docstring": doc,
                        }
                    )

        except Exception:
            continue

    return functions


def build_dashboard_summary(functions):

    total = len(functions)

    documented = len([f for f in functions if f["status"] == "OK"])

    missing = total - documented

    return {
        "total_functions": total,
        "documented": documented,
        "missing": missing,
    }