"""
Pydantic schemas for API request/response validation.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


# Auth Schemas
class PhoneNumber(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20, description="Phone number")
    
    @validator('phone')
    def validate_phone(cls, v):
        # Remove spaces and dashes
        v = v.replace(' ', '').replace('-', '')
        if not v.isdigit():
            raise ValueError('Phone must contain only digits')
        return v


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: Optional[str] = None
    phone: Optional[str] = None
    aadhaar: str = Field(..., min_length=12, max_length=12, description="12-digit Aadhaar number")
    location: Optional[str] = None
    gender: Optional[str] = None
    state: Optional[str] = None
    urban_rural: Optional[str] = None
    consent_given: bool = True
    provider: str = Field(default="google")
    access_token: str = Field(..., description="Supabase access token from OAuth login")


class OAuthLoginRequest(BaseModel):
    access_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# User Schemas
class UserTierEnum(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class UserProfile(BaseModel):
    id: int
    name: str
    phone: str
    location: Optional[str]
    tier: UserTierEnum
    joined_at: datetime
    current_trust_score: Optional[float]
    
    class Config:
        from_attributes = True


class UserScoreSummary(BaseModel):
    user_id: int
    name: str
    current_score: float
    score_tier: UserTierEnum
    last_computed: datetime
    is_cold_start: bool


# Trust Score Schemas
class ComponentScore(BaseModel):
    score: float
    weight: float
    weighted_contribution: float
    data: Dict


class TrustScoreBreakdown(BaseModel):
    final_score: float
    is_cold_start: bool
    components: Dict[str, ComponentScore]
    computed_at: str


class TrustScoreResponse(BaseModel):
    id: int
    user_id: int
    score: float
    breakdown: TrustScoreBreakdown
    explanation: str
    computed_at: datetime
    
    class Config:
        from_attributes = True


# Community Schemas
class ClusterTypeEnum(str, Enum):
    SHG = "shg"
    MERCHANT = "merchant"
    NEIGHBORHOOD = "neighborhood"


class CreateCommunityRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    cluster_type: ClusterTypeEnum
    description: Optional[str] = None
    location: Optional[str] = None


class CommunityResponse(BaseModel):
    id: int
    name: str
    cluster_type: ClusterTypeEnum
    created_at: datetime
    anchor_user_id: int
    total_members: Optional[int] = 0
    
    class Config:
        from_attributes = True


class JoinCommunityRequest(BaseModel):
    vouched_by_user_id: Optional[int] = None


class VouchRequest(BaseModel):
    vouchee_user_id: int
    weight: float = Field(default=1.0, ge=0.1, le=5.0)


# Loan Schemas
class LoanStatusEnum(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISBURSED = "disbursed"
    REPAID = "repaid"
    DEFAULTED = "defaulted"


class LoanApplicationRequest(BaseModel):
    community_id: int
    amount_requested: float = Field(..., gt=0, description="Loan amount in INR")
    purpose: str = Field(..., min_length=10, max_length=1000)
    tenure_months: int = Field(..., ge=1, le=60)


class LoanApplicationResponse(BaseModel):
    id: int
    borrower_id: int
    community_id: int
    amount_requested: float
    amount_approved: Optional[float]
    purpose: str
    status: LoanStatusEnum
    applied_at: datetime
    trust_score_at_application: Optional[float]
    
    class Config:
        from_attributes = True


class RepaymentRequest(BaseModel):
    amount: float = Field(..., gt=0)
    payment_method: Optional[str] = "upi"
    transaction_id: Optional[str] = None


class RepaymentResponse(BaseModel):
    id: int
    loan_id: int
    amount: float
    due_date: datetime
    paid_date: Optional[datetime]
    on_time: Optional[bool]
    
    class Config:
        from_attributes = True


# Graph Schemas
class GraphNode(BaseModel):
    id: int
    name: str
    score: float


class GraphEdge(BaseModel):
    source: int
    target: int
    weight: float


class TrustGraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


# Cluster Health Schemas
class FinancialSummary(BaseModel):
    total_disbursed: float
    total_repaid: float
    outstanding: float
    currency: str = "INR"


class AtRiskMember(BaseModel):
    user_id: int
    name: str
    current_score: float
    previous_score: float
    score_drop: float
    days_ago: int


class ClusterHealthResponse(BaseModel):
    community_id: int
    community_name: str
    cluster_type: str
    total_members: int
    average_trust_score: float
    on_time_repayment_rate: float
    on_time_repayment_rate_pct: float
    active_borrowers_count: int
    cluster_status: str
    status_color: str
    financial_summary: FinancialSummary
    at_risk_members: List[AtRiskMember]
    computed_at: str


# Admin Schemas
class FairnessReportResponse(BaseModel):
    total_users: int
    avg_score_by_gender: Dict[str, float]
    avg_score_by_state: Dict[str, float]
    avg_score_by_urban_rural: Dict[str, float]
    computed_at: datetime
