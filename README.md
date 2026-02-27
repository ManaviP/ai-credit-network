# AI Community Credit Network - MVP

A fintech platform providing credit scoring to credit-invisible users through community trust graphs.

## 🎯 Overview

This platform serves informal economy workers, street vendors, and gig workers by leveraging community trust relationships instead of traditional credit history.

## 🛠 Tech Stack

- **Backend**: FastAPI (Python 3.11), Supabase (PostgreSQL), Redis, Celery + RabbitMQ
- **Graph DB**: Neo4j for trust relationship storage
- **Frontend**: React.js + Tailwind CSS + D3.js
- **Auth**: JWT + OAuth2
- **DevOps**: Docker + Docker Compose, GitHub Actions
- **MLOps**: MLflow (ready for Phase 2 GNN integration)

## 📁 Project Structure

```
/backend
  /app
    /models       # SQLAlchemy ORM models
    /routers      # FastAPI endpoint routers
    /services     # Business logic (scoring, health checks, blockchain stub)
    /tasks        # Celery async background jobs
    /schemas      # Pydantic validation schemas
    /core         # Config, security, dependencies
  /tests          # Unit and integration tests
  /alembic        # Database migrations

/frontend
  /src
    /components   # React components
    /pages        # Page layouts
    /hooks        # Custom React hooks
    /services     # API client
    /utils        # Helper functions

/docker-compose.yml
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 21+
- Docker & Docker Compose

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Start services
docker-compose up -d

# Run migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Run Tests

```bash
cd backend
pytest tests/ -v
```

## 🎯 Features

### Phase 1 (Current MVP)
- ✅ Rule-based trust scoring (0-1000 scale)
- ✅ Community dashboard with health metrics
- ✅ Basic loan application flow
- ✅ Trust graph visualization
- ✅ JWT authentication with OTP
- ✅ NBFC partner API integration ready
- ✅ Fairness & compliance reporting
- ✅ Blockchain-ready architecture

### Phase 2 (Future)
- 🔄 Graph Neural Network (GNN) scoring
- 🔄 Polygon blockchain integration
- 🔄 IPFS for score verification
- 🔄 Advanced ML models with MLflow

## 🧮 Trust Score Components

1. **Repayment History (40%)** - On-time payment rate
2. **Community Tenure (20%)** - Months active in community
3. **Vouch Count (15%)** - Active member vouches
4. **Voucher Reliability (15%)** - Avg score of vouchers
5. **Loan Volume (10%)** - Successfully repaid amount

**Score Range**: 0-1000  
**Cold Start**: New users start at 300

## 🏥 Cluster Health Status

- **Stable**: Avg trust score > 700
- **Growing**: Avg trust score > 500
- **Fragile**: Avg trust score < 500

## 🔒 Security & Compliance

- DPDP Act 2023 compliant
- Aadhaar stored as SHA-256 hash
- Demographic data anonymization
- Full audit logging for all scoring decisions
- Consent tracking

## 📊 API Endpoints

### Auth
- `POST /auth/register` - Register with phone + Aadhaar
- `POST /auth/verify-otp` - Verify OTP and get JWT
- `POST /auth/refresh` - Refresh access token

### Users
- `GET /users/me` - Current user profile
- `GET /users/{id}/score` - Trust score breakdown
- `GET /users/{id}/graph` - Trust graph for visualization

### Communities
- `POST /communities` - Create new community
- `POST /communities/{id}/join` - Join with optional vouch
- `GET /communities/{id}/dashboard` - Health metrics
- `POST /communities/{id}/vouch` - Vouch for member

### Loans
- `POST /loans/apply` - Submit loan application
- `GET /loans/{id}/status` - Check loan status
- `POST /loans/{id}/repay` - Log repayment
- `GET /loans/my-loans` - User's loan history

### Scoring
- `POST /scoring/compute/{user_id}` - Trigger recalculation
- `GET /scoring/explain/{user_id}` - Plain-language explanation

### Admin
- `GET /admin/fairness-report` - Demographic fairness analysis

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app tests/

# Seed sample data
python scripts/seed_data.py
```

## 📝 Environment Variables

Create `.env` file:

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/credit_network
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Redis
REDIS_URL=redis://localhost:6379

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost:5672

# JWT
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# SMS (for OTP)
SMS_API_KEY=your_sms_api_key
SMS_API_URL=your_sms_api_url
```

## 🤝 Contributing

This is an MVP. Future phases will include GNN models, blockchain anchoring, and advanced ML features.

## 📄 License

Proprietary - All rights reserved
