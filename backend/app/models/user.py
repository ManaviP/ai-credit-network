from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class UserTier(str, enum.Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True, index=True)
    phone = Column(String(20), unique=True, nullable=True, index=True)
    auth_provider = Column(String(50), default="local")
    provider_id = Column(String(255), unique=True, nullable=True)
    aadhaar_hash = Column(String(64), unique=True, nullable=False)  # SHA-256 hash
    location = Column(String(255))
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    tier = Column(SQLEnum(UserTier), default=UserTier.BRONZE, nullable=False)
    
    # DPDP Act 2023 Compliance
    consent_given = Column(Boolean, default=False, nullable=False)
    consent_timestamp = Column(DateTime)
    
    # Demographics (nullable for privacy)
    gender = Column(String(20))
    state = Column(String(100))
    urban_rural = Column(String(20))
    
    # Blockchain ready (Phase 3)
    web3_wallet_address = Column(String(42))  # Ethereum address format
    
    # OTP verification
    otp_code = Column(String(6))
    otp_expires_at = Column(DateTime)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    community_memberships = relationship("CommunityMembership", back_populates="user", foreign_keys="CommunityMembership.user_id")
    loans_as_borrower = relationship("LoanApplication", back_populates="borrower", foreign_keys="LoanApplication.borrower_id")
    trust_scores = relationship("TrustScore", back_populates="user")
    vouches_given = relationship("VouchRelationship", back_populates="voucher", foreign_keys="VouchRelationship.voucher_id")
    vouches_received = relationship("VouchRelationship", back_populates="vouchee", foreign_keys="VouchRelationship.vouchee_id")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.id}: {self.name}>"
