import os
from groq import Groq


class DocstringGenerator:

    def __init__(self, style="google"):
        self.style = style
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def build_prompt(self, code):

        if self.style == "google":
            style_desc = "Google style docstring"

        elif self.style == "numpy":
            style_desc = "NumPy style docstring"

        else:
            style_desc = "reStructuredText (reST) style docstring"

        return f"""
Generate a {style_desc} for the following Python function.

Include:
- Description
- Args / Parameters
- Returns
- Raises (if applicable)

Function code:

{code}

Return ONLY the docstring.
"""

    def generate(self, code):

        prompt = self.build_prompt(code)

        response = self.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        return response.choices[0].message.content