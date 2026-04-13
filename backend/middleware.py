from fastapi import Request, HTTPException, status
from history_manager import get_user_scan_count

async def verify_guest_id(request: Request):
    guest_id = request.headers.get("X-Guest-ID")
    #ip = request.client.host
    ip = get_real_ip(request)
    
    if not guest_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Guest Identifier"
        )
    print("from middleware Guest ID: ", guest_id)
    print("IP: ", ip)
    # Optional: Rate Limiting (e.g., max 10 scans per guest)
    scan_count = get_user_scan_count(guest_id, ip)
    if scan_count >= 3:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Scan limit reached for this guest ID"
        )
        
    return guest_id



# backend/middleware.py
def get_real_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        print("from middleware X-Forwarded-For: ", forwarded_for)
        return forwarded_for.split(",")[0].strip()
    print("from middleware client.host: ", request.client.host)
    return request.client.host  # fallback for direct connections / dev