import json


def snapshot_metrics(current):
    try:
        with open("last_snapshot.json", "r") as f:
            previous = json.load(f)
    except:
        previous = None

    with open("last_snapshot.json", "w") as f:
        json.dump(current, f, indent=4)

    return previous