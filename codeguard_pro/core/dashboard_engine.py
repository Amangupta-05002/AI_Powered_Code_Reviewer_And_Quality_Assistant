import ast
import pandas as pd


def extract_dashboard_data(files):
    """
    Extract functions and documentation status from scanned files.
    """

    functions = []

    for file_name, code in files.items():

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):

                if isinstance(node, ast.FunctionDef):

                    doc = ast.get_docstring(node)

                    functions.append(
                        {
                            "file": file_name,
                            "function": node.name,
                            "status": "Documented" if doc else "Missing"
                        }
                    )

        except Exception:
            continue

    df = pd.DataFrame(functions)

    if df.empty:
        return df, {"total": 0, "documented": 0, "missing": 0}

    summary = {
        "total": len(df),
        "documented": len(df[df["status"] == "Documented"]),
        "missing": len(df[df["status"] == "Missing"]),
    }

    return df, summary