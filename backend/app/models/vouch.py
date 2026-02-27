from sqlalchemy import Column, Integer, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class VouchRelationship(Base):
    __tablename__ = "vouch_relationships"
    
    id = Column(Integer, primary_key=True, index=True)
    voucher_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    vouchee_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    weight = Column(Float, default=1.0, nullable=False)  # Vouch strength
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    
    # Track vouching outcomes
    repayment_count = Column(Integer, default=0)
    default_count = Column(Integer, default=0)
    
    # Timestamps
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deactivated_at = Column(DateTime)
    
    # Relationships
    voucher = relationship("User", back_populates="vouches_given", foreign_keys=[voucher_id])
    vouchee = relationship("User", back_populates="vouches_received", foreign_keys=[vouchee_id])
    
    def __repr__(self):
        return f"<Vouch: {self.voucher_id} -> {self.vouchee_id}>"
