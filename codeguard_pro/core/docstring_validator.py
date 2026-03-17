import subprocess
import tempfile
import os


class DocstringValidator:

    def validate(self, code):
        try:
            # Create temporary file with UTF-8 encoding
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".py",
                mode="w",
                encoding="utf-8"   # ✅ FIX
            ) as tmp:

                tmp.write(code)
                tmp_path = tmp.name

            # Run pydocstyle
            result = subprocess.run(
                ["pydocstyle", tmp_path],
                capture_output=True,
                text=True,
                encoding="utf-8"  # ✅ FIX
            )

            os.unlink(tmp_path)

            if result.stdout.strip() == "":
                return {
                    "status": "Compliant",
                    "warnings": []
                }

            return {
                "status": "Issues Found",
                "warnings": result.stdout.splitlines()
            }

        except Exception as e:
            return {
                "status": "Error",
                "warnings": [str(e)]
            }