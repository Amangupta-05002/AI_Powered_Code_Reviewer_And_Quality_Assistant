def get_prompt(style, function_code):

    if style == "google":

        return f"""
Generate a Google style docstring for this function.

Include:
Description
Args
Returns
Raises

Function:
{function_code}
"""

    if style == "numpy":

        return f"""
Generate a NumPy style docstring for this function.

Include:
Parameters
Returns
Raises

Function:
{function_code}
"""

    if style == "rest":

        return f"""
Generate a reStructuredText style docstring.

Include:
:param
:return
:raises

Function:
{function_code}
"""