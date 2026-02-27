from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class LoanStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISBURSED = "disbursed"
    REPAID = "repaid"
    DEFAULTED = "defaulted"


class LoanApplication(Base):
    __tablename__ = "loan_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    borrower_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=False)
    amount_requested = Column(Float, nullable=False)
    purpose = Column(Text, nullable=False)
    status = Column(SQLEnum(LoanStatus), default=LoanStatus.PENDING, nullable=False)
    
    # Loan terms
    interest_rate = Column(Float)  # Annual percentage
    tenure_months = Column(Integer)
    amount_approved = Column(Float)
    
    # Timestamps
    applied_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    approved_at = Column(DateTime)
    disbursed_at = Column(DateTime)
    repaid_at = Column(DateTime)
    
    # NBFC partner info
    nbfc_partner_id = Column(String(100))
    nbfc_loan_id = Column(String(100))
    
    # Risk assessment at application time
    trust_score_at_application = Column(Float)
    
    # Blockchain ready (Phase 3)
    blockchain_tx_hash = Column(String(66))  # Ethereum tx hash
    
    # Relationships
    borrower = relationship("User", back_populates="loans_as_borrower", foreign_keys=[borrower_id])
    community = relationship("Community", back_populates="loans")
    repayments = relationship("Repayment", back_populates="loan")
    
    def __repr__(self):
        return f"<Loan {self.id}: ₹{self.amount_requested} - {self.status}>"


class Repayment(Base):
    __tablename__ = "repayments"
    
    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loan_applications.id"), nullable=False)
    amount = Column(Float, nullable=False)
    due_date = Column(DateTime, nullable=False)
    paid_date = Column(DateTime)
    on_time = Column(Integer)  # SQLite compatible boolean (NULL until paid)
    
    # Payment details
    payment_method = Column(String(50))
    transaction_id = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    loan = relationship("LoanApplication", back_populates="repayments")
    
    def __repr__(self):
        return f"<Repayment {self.id}: Loan {self.loan_id} - ₹{self.amount}>"
