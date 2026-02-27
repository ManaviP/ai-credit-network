from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class ClusterType(str, enum.Enum):
    SHG = "shg"  # Self-Help Group
    MERCHANT = "merchant"
    NEIGHBORHOOD = "neighborhood"


class MemberRole(str, enum.Enum):
    MEMBER = "member"
    ANCHOR = "anchor"


class Community(Base):
    __tablename__ = "communities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    cluster_type = Column(SQLEnum(ClusterType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    anchor_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Metadata
    description = Column(String(1000))
    location = Column(String(255))
    
    # Timestamps
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    anchor_user = relationship("User", foreign_keys=[anchor_user_id])
    memberships = relationship("CommunityMembership", back_populates="community")
    loans = relationship("LoanApplication", back_populates="community")
    
    def __repr__(self):
        return f"<Community {self.id}: {self.name}>"


class CommunityMembership(Base):
    __tablename__ = "community_memberships"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=False)
    role = Column(SQLEnum(MemberRole), default=MemberRole.MEMBER, nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    vouched_by_user_id = Column(Integer, ForeignKey("users.id"))
    
    # Status
    is_active = Column(Integer, default=1)  # SQLite compatible boolean
    left_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="community_memberships", foreign_keys=[user_id])
    community = relationship("Community", back_populates="memberships")
    vouched_by = relationship("User", foreign_keys=[vouched_by_user_id])
    
    def __repr__(self):
        return f"<Membership: User {self.user_id} in Community {self.community_id}>"
