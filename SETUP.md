# 🚀 Setup Guide - AI Community Credit Network MVP

## Prerequisites

Ensure you have the following installed:
- **Python 3.11.7** ✅ (Already installed)
- **Node.js 21.6.1** ✅ (Already installed)
- **Docker Desktop** (for running services)
- **Git** (for version control)

## 📦 Backend Setup

### Step 1: Create Virtual Environment

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 2: Install Dependencies

```powershell
pip install -r requirements.txt
```

### Step 3: Environment Configuration

Copy the example environment file and configure:

```powershell
copy .env.example .env
```

Edit `.env` with your settings (use defaults for local development).

### Step 4: Start Infrastructure Services

From the root directory:

```powershell
cd ..
docker-compose up -d postgres neo4j redis rabbitmq mlflow
```

Wait ~30 seconds for services to start. Verify with:

```powershell
docker-compose ps
```

All services should show "Up" status.

### Step 5: Initialize Database

```powershell
cd backend

# Create migration
alembic revision --autogenerate -m "Initial migration"

# Run migration
alembic upgrade head
```

### Step 6: Seed Sample Data

```powershell
python scripts/seed_data.py
```

This creates:
- 3 sample communities
- 30 users with realistic data
- Trust relationships
- Loan histories
- Computed trust scores

### Step 7: Start Backend API

```powershell
uvicorn app.main:app --reload
```

API will be available at: **http://localhost:8000**
API Documentation: **http://localhost:8000/docs**

### Step 8: Start Celery Worker (New Terminal)

```powershell
cd backend
.\venv\Scripts\Activate.ps1
celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
```

### Step 9: Start Celery Beat (New Terminal)

```powershell
cd backend
.\venv\Scripts\Activate.ps1
celery -A app.tasks.celery_app beat --loglevel=info
```

## 🎨 Frontend Setup

### Step 1: Install Dependencies

```powershell
cd frontend
npm install
```

### Step 2: Create Environment File

Create `.env` file:

```
VITE_API_URL=http://localhost:8000
```

### Step 3: Start Development Server

```powershell
npm run dev
```

Frontend will be available at: **http://localhost:3000**

## 🧪 Running Tests

### Backend Tests

```powershell
cd backend
pytest tests/ -v
```

### Run with Coverage

```powershell
pytest --cov=app tests/ --cov-report=html
```

## 🌐 Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Register new account |
| **Backend API** | http://localhost:8000 | - |
| **API Docs** | http://localhost:8000/docs | - |
| **Neo4j Browser** | http://localhost:7474 | neo4j / password123 |
| **RabbitMQ Management** | http://localhost:15672 | guest / guest |
| **MLflow UI** | http://localhost:5000 | - |

## 📝 Quick Start Flow

1. **Register a new user**: Visit http://localhost:3000/register
   - Enter your details
   - OTP will be logged in backend terminal (check console)
   - Enter OTP to complete registration

2. **View Dashboard**: See your initial trust score (300 - cold start)

3. **Explore Communities**: Join or create communities

4. **Apply for Loans**: Submit loan applications

5. **Make Repayments**: Log repayments to improve trust score

## 🧩 Testing the API

### Using API Docs (Swagger UI)

1. Visit http://localhost:8000/docs
2. Click "Authorize" button
3. Register via `/auth/register`
4. Verify OTP via `/auth/verify-otp`
5. Copy the `access_token`
6. Click "Authorize" and paste token
7. Now you can test all endpoints!

### Sample API Workflow

```bash
# 1. Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "phone": "9876543210",
    "aadhaar": "123456789012",
    "location": "Mumbai",
    "consent_given": true
  }'

# Check backend logs for OTP

# 2. Verify OTP
curl -X POST http://localhost:8000/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "9876543210",
    "otp": "YOUR_OTP_FROM_LOGS"
  }'

# Save the access_token from response

# 3. Get Profile
curl -X GET http://localhost:8000/users/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🐛 Troubleshooting

### Docker Services Not Starting

```powershell
# Stop all containers
docker-compose down

# Remove volumes and restart
docker-compose down -v
docker-compose up -d
```

### Database Connection Issues

Check if PostgreSQL is running:
```powershell
docker-compose ps postgres
```

If not running:
```powershell
docker-compose up -d postgres
```

### Neo4j Connection Issues

Check Neo4j logs:
```powershell
docker-compose logs neo4j
```

Restart Neo4j:
```powershell
docker-compose restart neo4j
```

### Celery Worker Not Processing Tasks

Ensure RabbitMQ and Redis are running:
```powershell
docker-compose ps rabbitmq redis
```

Restart worker:
```powershell
# Stop with Ctrl+C, then restart
celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
```

### Port Already in Use

If port 8000 or 3000 is in use:

Backend:
```powershell
uvicorn app.main:app --reload --port 8001
```

Frontend (edit `vite.config.js`):
```javascript
server: { port: 3001 }
```

## 📊 Monitoring

### Check Service Health

```powershell
# API Health
curl http://localhost:8000/health

# Neo4j
curl http://localhost:7474/db/neo4j/tx/commit

# RabbitMQ
curl -u guest:guest http://localhost:15672/api/overview
```

### View Logs

```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f postgres
docker-compose logs -f neo4j
```

## 🎯 Next Steps

Once setup is complete:

1. ✅ Explore the API documentation
2. ✅ Test trust score calculation
3. ✅ Create communities and add members
4. ✅ Submit loan applications
5. ✅ Vouch for community members
6. ✅ View cluster health dashboards

## 🔧 Development Tips

### Hot Reload

Both backend (FastAPI) and frontend (Vite) support hot reload:
- Backend: Changes to Python files auto-reload
- Frontend: Changes to React files auto-reload

### Database Migrations

After model changes:

```powershell
cd backend
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

### Reset Database

```powershell
docker-compose down postgres -v
docker-compose up -d postgres
alembic upgrade head
python scripts/seed_data.py
```

## 📚 Additional Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Neo4j Cypher**: https://neo4j.com/docs/cypher-manual
- **Celery Guide**: https://docs.celeryq.dev
- **React Router**: https://reactrouter.com
- **Tailwind CSS**: https://tailwindcss.com

## 🆘 Need Help?

Check the logs:
1. Backend: Terminal where `uvicorn` is running
2. Celery: Terminal where celery worker is running
3. Docker services: `docker-compose logs -f`

Happy coding! 🚀
