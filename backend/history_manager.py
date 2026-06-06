import os
from datetime import datetime, timezone, timedelta
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

# import models from database.models
from auth.models import GuestScan

SCAN_LIMIT = 3
WINDOW_HOURS = 2


async def log_activity(
    db: AsyncSession,
    guest_id: str,
    ip: str,
    filename: str
) -> None:
    """
    Inserts a scan record and prunes records older than 24 hours.
    Replaces fcntl flat-file write — PostgreSQL handles concurrency natively.
    """
    await db.execute(
        text("""
            INSERT INTO guest_scans (guest_id, ip, filename, scanned_at)
            VALUES (:guest_id, :ip, :filename, CURRENT_TIMESTAMP)
        """),
        {"guest_id": guest_id, "ip": ip, "filename": filename}
    )
    # Prune records older than 24h — keeps table lean
    await db.execute(
        delete(GuestScan).where(
            GuestScan.scanned_at < datetime.utcnow() - timedelta(hours=24)
        )
    )
    await db.commit()


async def get_user_scan_count(
    db: AsyncSession,
    guest_id: str,
    ip: str
) -> int:
    """
    Counts scans by guest_id OR ip within the sliding window.
    """
    # Calculate the exact cutoff time in Python
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=WINDOW_HOURS)
    
    result = await db.execute(
        text("""
            SELECT COUNT(*) FROM guest_scans 
            WHERE (guest_id = :guest_id OR ip = :ip)
            AND scanned_at > :cutoff_time
        """),
        {"guest_id": guest_id, "ip": ip, "cutoff_time": cutoff_time}
    )
    return result.scalar() or 0


async def get_history(
    db: AsyncSession,
    guest_id: str
) -> list:
    """Returns scan history for a specific guest_id."""
    result = await db.execute(
        text("""
            SELECT filename, scanned_at, ip
            FROM guest_scans
            WHERE guest_id = :guest_id
            ORDER BY scanned_at DESC
            LIMIT 50
        """),
        {"guest_id": guest_id}
    )
    rows = result.fetchall()
    return [
        {
            "filename": row.filename,
            "timestamp": row.scanned_at.isoformat(),
            "ip": row.ip
        }
        for row in rows
    ]