# 🌐 AI Community Credit Network - MVP Complete

## 🎉 **Project Overview**

A fintech platform providing **credit scoring to credit-invisible users** (informal economy workers, street vendors, gig workers) by leveraging **community trust graphs** instead of traditional credit history.

Built with **FastAPI**, **PostgreSQL**, **Neo4j**, **React**, and **Celery** - ready for Phase 2 GNN and Phase 3 blockchain integration.

---

## ✅ **What's Implemented**

### 🔐 **Authentication & User Management**
- ✅ Phone + Aadhaar registration with OTP verification
- ✅ JWT-based authentication with refresh tokens
- ✅ DPDP Act 2023 compliant (Aadhaar hashing, consent tracking)
- ✅ User profiles with demographics

### 🧮 **Rule-Based Trust Scoring Engine**
- ✅ **5-component weighted scoring system**:
  - 40% - Repayment History (on-time payment rate)
  - 20% - Community Tenure (months active)
  - 15% - Vouch Count (community endorsements)
  - 15% - Voucher Reliability (avg score of vouchers)
  - 10% - Loan Volume (total successfully repaid)
- ✅ Cold start handling (new users start at 300)
- ✅ Plain-language explanations
- ✅ Content hashing for blockchain anchoring (Phase 3 ready)

### 🏘️ **Community Management**
- ✅ Create communities (SHG, Merchant, Neighborhood types)
- ✅ Join with optional vouching
- ✅ Vouch for members (creates trust relationships)
- ✅ Cluster health dashboard with metrics:
  - Average trust score
  - On-time repayment rate (90 days)
  - Active borrowers count
  - Financial summary
  - At-risk member alerts
  - Status: Stable/Growing/Fragile

### 💰 **Loan Management**
- ✅ Loan application flow
- ✅ Community-based lending
- ✅ Repayment tracking with grace period
- ✅ Auto trust score recalculation after repayment
- ✅ Loan status tracking (pending → approved → disbursed → repaid)

### 📊 **Graph Database (Neo4j)**
- ✅ User nodes with trust scores
- ✅ VOUCHES_FOR relationships with weights
- ✅ MEMBER_OF relationships for communities
- ✅ Trust graph visualization API (D3.js ready)

### ⚙️ **Background Jobs (Celery)**
- ✅ Async trust score computation
- ✅ Nightly cluster health checks
- ✅ Repayment reminders (3 days before due)
- ✅ Scheduled tasks with Celery Beat

### 👨‍💼 **Admin & Compliance**
- ✅ Fairness report (anonymized demographics)
- ✅ Score breakdown by gender/state/urban-rural
- ✅ Full audit logging
- ✅ DPDP Act compliance features

### 🎨 **Frontend (React + Tailwind)**
- ✅ User dashboard with score gauge
- ✅ Score breakdown visualization
- ✅ Authentication flow (register + OTP)
- ✅ Responsive design
- ✅ API integration with axios
- ✅ State management with Zustand

### 🔗 **Blockchain-Ready Architecture**
- ✅ Content hash generation (SHA-256)
- ✅ Blockchain audit service stub
- ✅ Event logging structure
- ✅ Web3 wallet address field
- ✅ Ready for Phase 3 Polygon + IPFS integration

---

## 📁 **Project Structure**

```
credit/
├── backend/
│   ├── app/
│   │   ├── core/          # Config, database, security, Neo4j
│   │   ├── models/        # SQLAlchemy models (User, Loan, etc.)
│   │   ├── routers/       # FastAPI endpoints
│   │   ├── schemas/       # Pydantic validation schemas
│   │   ├── services/      # Business logic (scoring, health)
│   │   └── tasks/         # Celery async jobs
│   ├── tests/             # Unit & integration tests
│   ├── scripts/           # seed_data.py
│   ├── alembic/           # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API client
│   │   └── stores/        # Zustand state management
│   ├── package.json
│   └── vite.config.js
│
├── docker-compose.yml     # All services
├── README.md              # Main documentation
├── SETUP.md               # Detailed setup guide
└── .gitignore
```

---

## 🛠️ **Tech Stack**

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Backend** | FastAPI | 0.109.0 | REST API framework |
| **Database** | PostgreSQL | 16 | Relational data |
| **Graph DB** | Neo4j | 5.16 | Trust relationships |
| **Cache** | Redis | 7.2 | Caching & Celery backend |
| **Queue** | RabbitMQ | 3.13 | Message broker |
| **Tasks** | Celery | 5.3.6 | Background jobs |
| **Frontend** | React | 18.2 | UI framework |
| **Styling** | Tailwind CSS | 3.4 | CSS framework |
| **Viz** | D3.js | 7.8 | Graph visualization |
| **MLOps** | MLflow | 2.10 | Phase 2 ready |
| **DevOps** | Docker | - | Containerization |

---

## 🚀 **Quick Start**

### **1. Start Services**
```powershell
docker-compose up -d
```

### **2. Setup Backend**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python scripts/seed_data.py
uvicorn app.main:app --reload
```

### **3. Setup Frontend**
```powershell
cd frontend
npm install
npm run dev
```

### **4. Access**
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Neo4j: http://localhost:7474

---

## 📊 **API Endpoints**

### **Auth**
- `POST /auth/register` - Register with phone + Aadhaar
- `POST /auth/verify-otp` - Verify OTP, get JWT
- `POST /auth/refresh` - Refresh access token

### **Users**
- `GET /users/me` - Current user profile
- `GET /users/{id}/score` - Trust score breakdown
- `GET /users/{id}/graph` - Trust graph for visualization

### **Communities**
- `POST /communities` - Create community
- `GET /communities` - List user's communities
- `POST /communities/{id}/join` - Join community
- `POST /communities/{id}/vouch` - Vouch for member
- `GET /communities/{id}/dashboard` - Health metrics

### **Loans**
- `POST /loans/apply` - Submit application
- `GET /loans/{id}/status` - Loan status & repayments
- `POST /loans/{id}/repay` - Log repayment
- `GET /loans/my-loans` - User's loan history

### **Scoring**
- `POST /scoring/compute/{user_id}` - Trigger recalculation
- `GET /scoring/explain/{user_id}` - Score explanation

### **Admin**
- `GET /admin/fairness-report` - Demographic fairness analysis

---

## 🧪 **Testing**

### **Run Unit Tests**
```powershell
cd backend
pytest tests/ -v
```

### **Test Coverage**
```powershell
pytest --cov=app tests/ --cov-report=html
```

### **Sample Data**
```powershell
python scripts/seed_data.py
```

Creates:
- 3 communities (SHG, Merchant, Neighborhood)
- 30 users with realistic profiles
- Trust relationships (vouches)
- Loan histories with repayments
- Computed trust scores

---

## 📈 **Score Calculation Example**

**User: Priya Kumar**
- Repayment: 90% on-time (18/20 payments) → **900 points**
- Tenure: 12 months active → **500 points**
- Vouches: 5 members vouch → **500 points**
- Voucher Quality: Avg score 750 → **750 points**
- Loan Volume: ₹40,000 repaid → **400 points**

**Weighted Score:**
```
(900 × 0.40) + (500 × 0.20) + (500 × 0.15) + (750 × 0.15) + (400 × 0.10)
= 360 + 100 + 75 + 112.5 + 40
= 687.5 / 1000
```

**Result:** Score of **688** = **"Good"** tier

---

## 🎯 **Future Phases**

### **Phase 2: ML/GNN Integration**
- Graph Neural Networks for trust propagation
- MLflow experiment tracking
- Advanced fraud detection
- Predictive default modeling

### **Phase 3: Blockchain**
- Polygon smart contracts
- IPFS for score verification
- Immutable audit trail
- Decentralized credit history

---

## 🔒 **Security & Compliance**

✅ **DPDP Act 2023**
- Aadhaar stored as SHA-256 hash
- Explicit user consent tracking
- Anonymized demographic reporting
- Right to data deletion ready

✅ **Security Features**
- JWT authentication
- Password hashing (bcrypt)
- API rate limiting ready
- CORS configuration
- Input validation (Pydantic)

---

## 📊 **Monitoring & Observability**

- **Health Check**: `GET /health`
- **API Docs**: Swagger UI at `/docs`
- **Neo4j Browser**: Graph visualization
- **RabbitMQ Management**: Queue monitoring
- **MLflow UI**: Model tracking (Phase 2)
- **Audit Logs**: Full event tracking

---

## 🤝 **Contributing**

This is an MVP. Future contributions welcome for:
- Advanced graph algorithms
- Mobile app (React Native)
- NBFC partner integrations
- Regional language support
- Enhanced fraud detection

---

## 📄 **License**

Proprietary - All rights reserved

---

## 🎓 **Learning Resources**

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Neo4j Graph Academy](https://neo4j.com/graphacademy)
- [Celery Best Practices](https://docs.celeryq.dev)
- [React Documentation](https://react.dev)
- [Tailwind CSS](https://tailwindcss.com)

---

## 📞 **Support**

For issues or questions:
1. Check [SETUP.md](SETUP.md) for troubleshooting
2. Review API docs at http://localhost:8000/docs
3. Check Docker logs: `docker-compose logs -f`

---

**Built with ❤️ for financial inclusion**

🌍 Empowering the credit-invisible through community trust
