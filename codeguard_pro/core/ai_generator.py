import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class AIGenerator:

    def __init__(self):
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise ValueError("GROQ_API_KEY not set")

        self.client = Groq(api_key=key)

    def generate_review(self, code):

        prompt = f"""
Review this Python code.
Suggest improvements in:
- PEP8
- Performance
- Security
- Refactoring
- Best practices

Code:
{code}
"""

        response = self.client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[{"role": "user", "content": prompt}]
)

        return response.choices[0].message.content