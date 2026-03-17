import json
from datetime import datetime


def log_ci_run(data):
    try:
        with open("ci_history.json", "r") as f:
            history = json.load(f)
    except:
        history = []

    history.append({
        "timestamp": str(datetime.now()),
        **data
    })

    with open("ci_history.json", "w") as f:
        json.dump(history, f, indent=4)


def load_ci_history():
    try:
        with open("ci_history.json", "r") as f:
            return json.load(f)
    except:
        return []