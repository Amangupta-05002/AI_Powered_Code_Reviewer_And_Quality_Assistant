import json
import os
from datetime import datetime

LOG_DIR = "storage"
LOG_FILE = os.path.join(LOG_DIR, "review_logs.json")


def save_review(file_name, function_name, docstring, style, status):

    entry = {
        "file_name": file_name,
        "function_name": function_name,
        "generated_docstring": docstring,
        "selected_style": style,
        "timestamp": datetime.utcnow().isoformat(),
        "status": status
    }

    # Create storage folder automatically
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    # Create log file automatically
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

    # Load existing logs
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    data.append(entry)

    # Save updated logs
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)