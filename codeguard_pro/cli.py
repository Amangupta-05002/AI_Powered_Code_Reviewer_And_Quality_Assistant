# codeguard_pro/cli.py

import sys
import subprocess
from pathlib import Path

from codeguard_pro.core.config import load_config
from codeguard_pro.core.metrics import build_metrics_summary
from codeguard_pro.database.db import init_db, save_review
from codeguard_pro.core.docstring_validator import DocstringValidator
from codeguard_pro.core.docstring_coverage import DocstringCoverage

def get_staged_files():
    result = subprocess.run(
        ["git", "diff", "--name-only", "--cached"],
        capture_output=True,
        text=True
    )
    return [f for f in result.stdout.splitlines() if f.endswith(".py")]

def run_precommit():
    config = load_config()
    validator = DocstringValidator()
    coverage_engine = DocstringCoverage()

    staged_files = get_staged_files()

    if not staged_files:
        return 0

    init_db()

    for file in staged_files:
        code = Path(file).read_text()

        validation = validator.validate(code)
        coverage = coverage_engine.calculate(code)

        issues = len(validation.get("warnings", []))

        if issues > 0:
            print(f"❌ Validation failed for {file}")
            sys.exit(1)

        if coverage["coverage_percent"] < config["coverage_threshold"]:
            print(f"❌ Coverage below threshold in {file}")
            sys.exit(1)

        record = build_metrics_summary(
            file,
            coverage["coverage_percent"],
            issues
        )

        save_review(record)

    print("✅ Pre-commit checks passed")
    return 0

if __name__ == "__main__":
    run_precommit()