from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class AuditLog(Base):
    """
    Log every scoring decision and important events for compliance.
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    event_type = Column(String(100), nullable=False, index=True)  # e.g., "score_computed", "loan_applied"
    entity_id = Column(Integer)  # ID of related entity (loan_id, community_id, etc.)
    payload_json = Column(JSON)  # Full context of the event
    
    # Blockchain ready (Phase 3)
    chain_tx_hash = Column(String(66))  # Ethereum transaction hash
    
    # Metadata
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog {self.id}: {self.event_type}>"


class BlockchainEvent(Base):
    """
    Track events that will be anchored to blockchain (Phase 3).
    """
    __tablename__ = "blockchain_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False)
    payload_json = Column(JSON, nullable=False)
    
    # Blockchain status
    chain_tx_hash = Column(String(66))
    block_number = Column(Integer)
    ipfs_cid = Column(String(100))
    
    # Status
    anchored = Column(Integer, default=0)  # SQLite compatible boolean
    anchored_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<BlockchainEvent {self.id}: {self.event_type}>"
