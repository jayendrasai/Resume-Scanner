from fastapi import Request, HTTPException, status
from history_manager import get_user_scan_count

async def verify_guest_id(request: Request):
    guest_id = request.headers.get("X-Guest-ID")
    
    if not guest_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Guest Identifier"
        )
    
    # Optional: Rate Limiting (e.g., max 10 scans per guest)
    scan_count = get_user_scan_count(guest_id)
    if scan_count >= 3:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Scan limit reached for this guest ID"
        )
        
    return guest_id