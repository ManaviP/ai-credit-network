from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class ScoreType(str, enum.Enum):
    RULE_BASED = "rule_based"
    GNN = "gnn"  # Phase 2


class TrustScore(Base):
    __tablename__ = "trust_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    score = Column(Float, nullable=False)  # 0-1000
    score_type = Column(SQLEnum(ScoreType), default=ScoreType.RULE_BASED, nullable=False)
    computed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Detailed breakdown
    breakdown_json = Column(JSON, nullable=False)  # Store component scores
    
    # Explanation
    explanation = Column(String(1000))
    
    # Blockchain ready - content hash for IPFS anchoring (Phase 3)
    content_hash = Column(String(64))  # SHA-256 of breakdown_json
    ipfs_cid = Column(String(100))  # IPFS Content ID
    
    # Relationships
    user = relationship("User", back_populates="trust_scores")
    
    def __repr__(self):
        return f"<TrustScore {self.id}: User {self.user_id} - {self.score}>"
