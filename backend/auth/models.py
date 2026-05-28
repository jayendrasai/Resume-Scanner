from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id               = Column(Integer, primary_key=True, index=True)
    email            = Column(String, unique=True, index=True, nullable=False)
    password_hash    = Column(String, nullable=False)
    tier             = Column(String, default="free", nullable=False)  # "free" | "premium"
    premium_expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())
    # Razorpay 30-Day Pass Columns
    razorpay_customer_id = Column(String, nullable=True)
    razorpay_order_id    = Column(String, unique=True, nullable=True, index=True)