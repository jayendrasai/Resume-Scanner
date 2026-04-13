import json
import os
import fcntl
from datetime import datetime, timedelta
from typing import Any

HISTORY_FILE = "data/history.json"
WINDOW_HOURS = 3


def get_history() -> list[dict[str, Any]]:
    """Reads history safely using a shared lock."""
    if not os.path.exists(HISTORY_FILE):
        return []
        
    try:
        with open(HISTORY_FILE, "r") as f:
            # Acquire a shared lock (multiple workers can read at once)
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                data = json.load(f)
                # Runtime check: Safely handle if json.load returns None or a dict
                if isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                pass
            finally:
                # Always release!
                fcntl.flock(f, fcntl.LOCK_UN)
    except Exception:
        pass
        
    return []

def write_history(data: list[dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            json.dump(data, f, indent=4)
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

def log_activity(guest_id: str, ip_address: str, filename: str) -> None:
    history = get_history()
    
    # Prune records older than 24 hours to prevent file bloat
    day_ago = datetime.now() - timedelta(days=1)
    history = [e for e in history if datetime.fromisoformat(e['timestamp']) > day_ago]

    new_entry = {
        "guest_id": guest_id,
        "ip": ip_address,
        "filename": filename,
        "timestamp": datetime.now().isoformat()
    }
    history.append(new_entry)
    
    # Safely write the updated array back to disk
    write_history(history)


# def log_activity(guest_id: str, ip: str, filename: str):
#     history = get_history()

#     # keep only last 24 hours
#     day_ago = datetime.now() - timedelta(days=1)
#     history = [
#         e for e in history
#         if datetime.fromisoformat(e["timestamp"]) > day_ago
#     ]

#     new_entry = {
#         "guest_id": guest_id,
#         "ip": ip,
#         "filename": filename,
#         "timestamp": datetime.now().isoformat()
#     }

#     history.append(new_entry)

#     with open(HISTORY_FILE, "w") as f:
#         json.dump(history, f, indent=4)


def get_user_scan_count(guest_id: str, ip_address: str) -> int:
    history = get_history() # Type checker now knows this is list[dict[str, Any]]
    now = datetime.now()
    cutoff_time = now - timedelta(hours=WINDOW_HOURS)
    
    count = sum(
        1 for entry in history
        if (entry.get('guest_id') == guest_id or entry.get('ip') == ip_address)
        and datetime.fromisoformat(entry['timestamp']) > cutoff_time
    )
    return count



#  def get_user_scan_count(guest_id: str, ip: str) -> int:
#     history = get_history()
#     now = datetime.now()
#     cutoff_time = now - timedelta(hours=WINDOW_HOURS)

#     valid_entries = []
#     for entry in history:
#         timestamp_str = entry.get("timestamp")
#         if not timestamp_str:
#             continue
            
#         entry_time = datetime.fromisoformat(timestamp_str)
#         if entry_time > cutoff_time:
#             if entry.get("guest_id") == guest_id or entry.get("ip") == ip:
#                 valid_entries.append(entry)

#     return len(valid_entries)