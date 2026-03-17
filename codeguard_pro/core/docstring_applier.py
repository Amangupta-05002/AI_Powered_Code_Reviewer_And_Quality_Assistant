def apply_docstring(function_code: str, ai_docstring: str) -> str:
    """
    Inserts a cleaned AI-generated docstring into a function.
    """

    # Remove markdown artifacts
    ai_docstring = ai_docstring.replace("```python", "")
    ai_docstring = ai_docstring.replace("```", "")
    ai_docstring = ai_docstring.strip()

    # Ensure triple quotes exist
    if not ai_docstring.startswith('"""'):
        ai_docstring = '"""\n' + ai_docstring

    if not ai_docstring.endswith('"""'):
        ai_docstring = ai_docstring + '\n"""'

    lines = function_code.split("\n")

    if len(lines) < 2:
        return function_code

    indent = " " * 4

    # Insert docstring after function definition
    new_lines = [lines[0], indent + ai_docstring]

    new_lines.extend(lines[1:])

    return "\n".join(new_lines)