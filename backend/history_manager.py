import json
import os
from datetime import datetime

HISTORY_FILE = "history.json"

def get_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def log_activity(guest_id: str, filename: str):
    history = get_history()
    new_entry = {
        "guest_id": guest_id,
        "filename": filename,
        "timestamp": datetime.now().isoformat()
    }
    history.append(new_entry)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

def get_user_scan_count(guest_id: str) -> int:
    history = get_history()
    return sum(1 for entry in history if entry['guest_id'] == guest_id)