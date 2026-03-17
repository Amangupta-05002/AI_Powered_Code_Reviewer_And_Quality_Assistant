import subprocess
import time

def run_precommit_check():
    start = time.time()

    result = subprocess.run(
        ["git", "diff", "--name-only", "--cached"],
        capture_output=True,
        text=True
    )

    changed_files = result.stdout.splitlines()
    python_files = [f for f in changed_files if f.endswith(".py")]

    duration = round(time.time() - start, 3)

    return python_files, duration