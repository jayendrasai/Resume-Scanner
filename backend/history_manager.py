import json
import os
from datetime import datetime, timedelta

HISTORY_FILE = "history.json"
WINDOW_HOURS = 3

def get_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

# def log_activity(guest_id: str, filename: str):
#     history = get_history()
#     new_entry = {
#         "guest_id": guest_id,
#         "filename": filename,
#         "timestamp": datetime.now().isoformat()
#     }
#     history.append(new_entry)
#     with open(HISTORY_FILE, "w") as f:
#         json.dump(history, f, indent=4)


def log_activity(guest_id: str, ip: str, filename: str):
    history = get_history()

    # keep only last 24 hours
    day_ago = datetime.now() - timedelta(days=1)
    history = [
        e for e in history
        if datetime.fromisoformat(e["timestamp"]) > day_ago
    ]

    new_entry = {
        "guest_id": guest_id,
        "ip": ip,
        "filename": filename,
        "timestamp": datetime.now().isoformat()
    }

    history.append(new_entry)

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

# def get_user_scan_count(guest_id: str) -> int:
#     history = get_history()
#     return sum(1 for entry in history if entry['guest_id'] == guest_id)


def get_user_scan_count(guest_id: str, ip: str) -> int:
    history = get_history()
    now = datetime.now()
    cutoff_time = now - timedelta(hours=WINDOW_HOURS)

    valid_entries = []
    for entry in history:
        timestamp_str = entry.get("timestamp")
        if not timestamp_str:
            continue
            
        entry_time = datetime.fromisoformat(timestamp_str)
        if entry_time > cutoff_time:
            if entry.get("guest_id") == guest_id or entry.get("ip") == ip:
                valid_entries.append(entry)

    return len(valid_entries)