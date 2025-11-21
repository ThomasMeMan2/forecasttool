# Forecast Studio - Deployment & Test Handleiding (Nederlands)

## 📋 Inhoudsopgave

1. [Vereisten](#1-vereisten)
2. [Lokale Deployment met Docker](#2-lokale-deployment-met-docker)
3. [Database Setup](#3-database-setup)
4. [Demo Data Laden](#4-demo-data-laden)
5. [Applicatie Testen](#5-applicatie-testen)
6. [Troubleshooting](#6-troubleshooting)
7. [Productie Deployment](#7-productie-deployment)

---

## 1. Vereisten

### Minimale Systeem Vereisten
- **OS**: Linux, macOS, of Windows (met WSL2)
- **RAM**: 4GB minimum, 8GB aanbevolen
- **Disk**: 2GB vrije ruimte
- **CPU**: 2 cores minimum

### Benodigde Software
- ✅ **Docker** (versie 20.10+)
- ✅ **Docker Compose** (versie 2.0+)
- ✅ **Git** (voor code checkout)
- ⚠️ **Python 3.11+** (optioneel, voor lokaal testen zonder Docker)

### Docker Installatie Controleren

```bash
# Check Docker versie
docker --version
# Verwachte output: Docker version 20.10.x of hoger

# Check Docker Compose
docker compose version
# Verwachte output: Docker Compose version v2.x.x

# Test Docker
docker run hello-world
# Moet succesvol een test container draaien
```

### Als Docker nog niet geïnstalleerd is:

**macOS**:
```bash
# Download Docker Desktop voor Mac
# https://www.docker.com/products/docker-desktop
```

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install docker.io docker-compose-plugin
sudo usermod -aG docker $USER
# Log uit en weer in
```

**Windows**:
```bash
# Download Docker Desktop voor Windows
# https://www.docker.com/products/docker-desktop
# Zorg dat WSL2 enabled is
```

---

## 2. Lokale Deployment met Docker

### Stap 1: Repository Clonen

```bash
# Navigeer naar gewenste directory
cd ~/projects

# Clone de repository
git clone <repository-url> forecasttool
cd forecasttool

# Checkout de branch met alle features
git checkout claude/forecast-studio-app-016waL2pLPR6ZPREoeqzrBXF
```

### Stap 2: Environment Configuratie

```bash
# Kopieer example environment file
cp backend/.env.example backend/.env

# Genereer een veilige SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Kopieer de output
```

**Bewerk `backend/.env` met een text editor:**

```bash
nano backend/.env
# of
vim backend/.env
# of gebruik een GUI editor
```

**Minimale configuratie:**

```env
# Database (blijft hetzelfde voor Docker)
DATABASE_URL=postgresql://forecast_user:forecast_pass@db:5432/forecast_db

# Security (VERANDER DEZE!)
SECRET_KEY=<plak-hier-de-gegenereerde-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS (voeg je frontend URL toe als je die hebt)
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# App
DEBUG=True
APP_NAME=Forecast Studio

# LLM (optioneel - laat leeg voor template fallback)
LLM_PROVIDER=template
ENABLE_LLM_INSIGHTS=False

# Als je OpenAI wilt gebruiken:
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-...
# ENABLE_LLM_INSIGHTS=True
```

**Sla het bestand op** (`Ctrl+X`, dan `Y`, dan `Enter` in nano)

### Stap 3: Docker Services Starten

```bash
# Build en start alle services
docker compose up --build

# Of in de achtergrond:
docker compose up --build -d
```

**Wat gebeurt er nu?**
- PostgreSQL database wordt gestart (poort 5432)
- Backend API wordt gebouwd en gestart (poort 8000)
- Frontend (optioneel) wordt gestart (poort 3000)
- Database migraties worden automatisch uitgevoerd

**Output controleren:**
```bash
# Logs bekijken (als je -d gebruikt hebt)
docker compose logs -f

# Status controleren
docker compose ps

# Verwachte output:
# NAME                COMMAND             STATUS              PORTS
# forecasttool-db-1   "docker-entrypoint" Up 2 minutes        0.0.0.0:5432->5432/tcp
# forecasttool-api-1  "uvicorn app.main"  Up 2 minutes        0.0.0.0:8000->8000/tcp
```

### Stap 4: API Beschikbaarheid Controleren

```bash
# Health check
curl http://localhost:8000/api/health

# Verwachte output:
# {"status":"healthy","service":"Forecast Studio"}
```

**Open in browser:**
- API Documentatie: http://localhost:8000/api/docs
- API ReDoc: http://localhost:8000/api/redoc

✅ **SUCCESS!** Als je de API docs ziet, werkt de deployment!

---

## 3. Database Setup

De database wordt automatisch aangemaakt door Docker Compose. Maar we moeten wel:

### Optie A: Alembic Migraties (Aanbevolen voor Productie)

```bash
# Ga de backend container in
docker compose exec api bash

# Voer migraties uit
alembic upgrade head

# Verlaat container
exit
```

### Optie B: Direct Database Creatie (Simpel voor Development)

Database tabellen worden automatisch aangemaakt bij eerste start dankzij:
```python
# In backend/app/main.py
Base.metadata.create_all(bind=engine)
```

### Database Controleren

```bash
# Connect naar PostgreSQL
docker compose exec db psql -U forecast_user -d forecast_db

# In psql:
\dt  # Lijst alle tabellen
# Je zou moeten zien:
# - users
# - projects
# - project_datasets
# - timeseries
# - forecasts
# - global_events
# - id_specific_events
# - user_exclusions
# - forecast_adjustments
# - project_insights
# - project_shares
# - project_versions
# - scheduled_forecasts
# - forecast_comparisons

\q  # Exit psql
```

---

## 4. Demo Data Laden

### Stap 1: Eerste Gebruiker Aanmaken

```bash
# Registreer admin gebruiker
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@forecaststudio.com",
    "password": "Admin123!Secure",
    "full_name": "Admin Gebruiker",
    "organization": "Forecast Studio"
  }'

# Verwachte output:
# {
#   "id": 1,
#   "email": "admin@forecaststudio.com",
#   "full_name": "Admin Gebruiker",
#   ...
# }
```

### Stap 2: Inloggen en Token Verkrijgen

```bash
# Login
curl -X POST "http://localhost:8000/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@forecaststudio.com&password=Admin123!Secure"

# Output bevat access_token:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer"
# }
```

**Sla de token op in een variabele:**

```bash
# macOS/Linux:
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Windows (PowerShell):
$TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Verifieer:
echo $TOKEN
```

### Stap 3: Project Aanmaken

```bash
curl -X POST "http://localhost:8000/api/projects" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Demo Retail Project",
    "description": "Voorbeeld project met retail forecast data"
  }'

# Output geeft project_id:
# {
#   "id": 1,
#   "name": "Demo Retail Project",
#   ...
# }
```

**Sla project ID op:**
```bash
export PROJECT_ID=1  # Of het ID uit de output
```

### Stap 4: Demo Data Uploaden

```bash
# Upload timeseries data
curl -X POST "http://localhost:8000/api/datasets/$PROJECT_ID/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@demo_data/demo_timeseries_data.csv"

# Verwachte output:
# {
#   "id": 1,
#   "project_id": 1,
#   "filename": "demo_timeseries_data.csv",
#   "row_count": 4380,
#   ...
# }
```

### Stap 5: Controleer Time Series

```bash
# Lijst alle time series
curl -X GET "http://localhost:8000/api/datasets/$PROJECT_ID/timeseries" \
  -H "Authorization: Bearer $TOKEN" | jq

# Je zou 6 time series moeten zien:
# - PRODUCT_A
# - PRODUCT_B
# - PRODUCT_C
# - STORE_001
# - STORE_002
# - REGION_NORTH
```

### Stap 6: Events Toevoegen

```bash
# Voeg global event toe
curl -X POST "http://localhost:8000/api/events/$PROJECT_ID/global-events" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "Black Friday 2024",
    "event_date": "2024-11-29",
    "event_type": "holiday",
    "description": "Jaarlijkse Black Friday sale"
  }'
```

---

## 5. Applicatie Testen

### Test 1: Basis Forecast Genereren

```bash
# Genereer forecast voor PRODUCT_A
curl -X POST "http://localhost:8000/api/forecasts/$PROJECT_ID/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "timeseries_ids": ["PRODUCT_A"],
    "horizon": 12,
    "confidence_level": 90
  }' | jq

# Output toont forecast met:
# - forecast_data (12 periodes)
# - confidence intervals
# - accuracy metrics (MAPE, RMSE, MAE)
```

### Test 2: Ensemble Forecast (Phase 2)

```bash
# Genereer enhanced ensemble forecast
curl -X POST "http://localhost:8000/api/forecasts/$PROJECT_ID/generate-enhanced?use_events=true" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "timeseries_ids": ["PRODUCT_B"],
    "horizon": 12,
    "confidence_level": 90
  }' | jq

# Output bevat:
# - ensemble_models: ["AutoARIMA", "AutoETS", "Prophet"]
# - ensemble_weights: {...}
# - forecast_value_added: X%
```

### Test 3: Diagnostics (Phase 3)

```bash
# Genereer diagnostics voor PRODUCT_A
curl -X GET "http://localhost:8000/api/diagnostics/$PROJECT_ID/timeseries/PRODUCT_A/diagnostics?frequency=D" \
  -H "Authorization: Bearer $TOKEN" | jq

# Output bevat:
# - acf_results (autocorrelatie)
# - pacf_results (partial autocorrelatie)
# - stationarity test resultaten
# - seasonal decomposition
# - summary statistics
```

### Test 4: LLM Insights (Phase 3)

```bash
# Genereer AI insight
curl -X POST "http://localhost:8000/api/insights/$PROJECT_ID/timeseries/PRODUCT_A/insights/history" \
  -H "Authorization: Bearer $TOKEN" | jq

# Output:
# {
#   "insight": {
#     "type": "history_summary",
#     "text": "Deze tijdreeks vertoont een duidelijke stijgende trend...",
#     "confidence": 0.5,
#     "model": "template"
#   }
# }
```

### Test 5: Project Sharing (Phase 4)

```bash
# Maak tweede gebruiker aan
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "colleague@forecaststudio.com",
    "password": "Colleague123!",
    "full_name": "Collega Gebruiker"
  }'

# Deel project met collega
curl -X POST "http://localhost:8000/api/sharing/$PROJECT_ID/shares" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "colleague@forecaststudio.com",
    "can_view": true,
    "can_edit": true,
    "can_delete": false,
    "can_share": false
  }' | jq
```

### Test 6: Forecast Comparison (Phase 4)

```bash
# Eerst twee forecasts genereren
FORECAST_ID_1=$(curl -s -X POST "http://localhost:8000/api/forecasts/$PROJECT_ID/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"timeseries_ids": ["PRODUCT_A"], "horizon": 12, "confidence_level": 90}' \
  | jq -r '.[0].id')

FORECAST_ID_2=$(curl -s -X POST "http://localhost:8000/api/forecasts/$PROJECT_ID/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"timeseries_ids": ["PRODUCT_B"], "horizon": 12, "confidence_level": 90}' \
  | jq -r '.[0].id')

# Vergelijk forecasts
curl -X POST "http://localhost:8000/api/comparison/$PROJECT_ID/comparisons" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"comparison_name\": \"Product A vs Product B\",
    \"forecast_ids\": [$FORECAST_ID_1, $FORECAST_ID_2]
  }" | jq
```

### Test 7: Geautomatiseerde Test Suite Draaien

```bash
# Installeer Python dependencies
pip install requests

# Run test suite
cd /pad/naar/forecasttool
python3 tests/test_comprehensive.py

# Output toont:
# ============================================================
# FORECAST STUDIO - COMPREHENSIVE TEST SUITE
# ============================================================
# ✓ TEST_AUTH_001
# ✓ TEST_AUTH_002
# ...
# TEST SUMMARY
# Total Tests: 20
# ✓ Passed: 18 (90.0%)
# ✗ Failed: 0 (0.0%)
# ⊘ Skipped: 2 (10.0%)
```

---

## 6. Troubleshooting

### Probleem: "Cannot connect to API"

**Oplossing:**
```bash
# Check of containers draaien
docker compose ps

# Als containers gestopt zijn:
docker compose up -d

# Logs bekijken
docker compose logs api

# Poort check
curl http://localhost:8000/api/health
```

### Probleem: "Database connection error"

**Oplossing:**
```bash
# Check database container
docker compose logs db

# Herstart database
docker compose restart db

# Wacht 10 seconden en test opnieuw
sleep 10
curl http://localhost:8000/api/health
```

### Probleem: "AttributeError: 'Settings' object has no attribute 'secret_key'"

**Oplossing:**
```bash
# SECRET_KEY ontbreekt in .env
echo "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')" >> backend/.env

# Herstart API
docker compose restart api
```

### Probleem: "401 Unauthorized"

**Oplossing:**
```bash
# Token is verlopen of ongeldig
# Login opnieuw om nieuwe token te krijgen
curl -X POST "http://localhost:8000/api/auth/token" \
  -d "username=admin@forecaststudio.com&password=Admin123!Secure"

# Gebruik de nieuwe access_token
```

### Probleem: Langzame Forecasting

**Oplossing:**
```bash
# Prophet model is traag - gebruik alleen AutoARIMA/AutoETS
curl -X POST "http://localhost:8000/api/forecasts/$PROJECT_ID/generate-enhanced?models=AutoARIMA&models=AutoETS" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"timeseries_ids": ["PRODUCT_A"], "horizon": 12, "confidence_level": 90}'
```

### Probleem: "No module named 'jose'"

**Oplossing:**
```bash
# Rebuild Docker image
docker compose down
docker compose up --build
```

### Logs Bekijken voor Debugging

```bash
# Alle logs
docker compose logs

# Alleen API logs
docker compose logs api

# Follow mode (realtime)
docker compose logs -f api

# Laatste 100 regels
docker compose logs --tail=100 api
```

---

## 7. Productie Deployment

### Optie A: Docker Compose (Simpel)

**Voor kleine deployments (< 100 gebruikers):**

```bash
# 1. Clone op productie server
git clone <repo-url> /opt/forecasttool
cd /opt/forecasttool

# 2. Configureer .env voor productie
nano backend/.env
# Zet DEBUG=False
# Gebruik sterke SECRET_KEY
# Configureer echte DATABASE_URL

# 3. Start met production compose
docker compose -f docker-compose.prod.yml up -d

# 4. Setup nginx als reverse proxy
```

**Nginx configuratie voorbeeld:**

```nginx
server {
    listen 80;
    server_name forecast.jouwdomein.nl;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Optie B: Kubernetes (Enterprise)

**Voor grote deployments (1000+ gebruikers):**

```bash
# 1. Build en push Docker images
docker build -t forecast-api:1.0 ./backend
docker push jouwregistry.azurecr.io/forecast-api:1.0

# 2. Deploy met Helm
helm install forecast-studio ./helm-chart

# 3. Configure ingress en TLS
```

### Optie C: Cloud Platforms

**Azure Container Apps:**
```bash
az containerapp up \
  --name forecast-studio \
  --resource-group forecast-rg \
  --environment forecast-env \
  --image forecast-api:1.0
```

**Google Cloud Run:**
```bash
gcloud run deploy forecast-studio \
  --image gcr.io/project-id/forecast-api:1.0 \
  --platform managed \
  --region europe-west1
```

**AWS ECS:**
```bash
aws ecs create-service \
  --cluster forecast-cluster \
  --service-name forecast-studio \
  --task-definition forecast-task
```

### Productie Checklist

- [ ] SECRET_KEY gegenereerd en veilig opgeslagen
- [ ] DEBUG=False in .env
- [ ] Database backups geconfigureerd
- [ ] HTTPS/SSL certificaten geïnstalleerd
- [ ] CORS origins beperkt tot productie domain
- [ ] Monitoring en logging opgezet (Sentry, DataDog)
- [ ] Health checks geconfigureerd
- [ ] Rate limiting enabled
- [ ] Firewall regels geconfigureerd
- [ ] Scheduled backups actief
- [ ] Disaster recovery plan gedocumenteerd

---

## 8. Quick Start Samenvatting

**Minimale stappen om snel te beginnen:**

```bash
# 1. Clone
git clone <repo> forecasttool && cd forecasttool

# 2. Configure
cp backend/.env.example backend/.env
# Edit .env en voeg SECRET_KEY toe

# 3. Start
docker compose up -d

# 4. Check
curl http://localhost:8000/api/health

# 5. Create User
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test123!","full_name":"Test"}'

# 6. Login
curl -X POST http://localhost:8000/api/auth/token \
  -d "username=test@test.com&password=Test123!"

# 7. Browse API
# Open http://localhost:8000/api/docs
```

---

## 9. Nuttige Commando's

### Docker Management

```bash
# Stop alle services
docker compose down

# Herstart services
docker compose restart

# Rebuild na code changes
docker compose up --build

# Verwijder volumes (VOORZICHTIG - data verlies!)
docker compose down -v

# Shell in container
docker compose exec api bash
docker compose exec db psql -U forecast_user -d forecast_db
```

### Database Management

```bash
# Database backup
docker compose exec db pg_dump -U forecast_user forecast_db > backup.sql

# Database restore
docker compose exec -T db psql -U forecast_user -d forecast_db < backup.sql

# Reset database (VOORZICHTIG!)
docker compose down -v
docker compose up -d
```

### Monitoring

```bash
# Resource gebruik
docker stats

# Container logs live
docker compose logs -f

# Check API performance
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/health
```

---

## 10. Support & Resources

### Documentatie
- **API Docs**: http://localhost:8000/api/docs (als server draait)
- **Test Plan**: `TEST_PLAN.md`
- **Test Results**: `TEST_RESULTS.md`
- **Phase Docs**: `PHASE1.md`, `PHASE2.md`, `PHASE3.md`, `PHASE4.md`

### Test Data
- **Location**: `demo_data/`
- **Generator**: `demo_data/generate_demo_data.py`
- **CSV Files**:
  - `demo_timeseries_data.csv`
  - `demo_global_events.csv`
  - `demo_id_events.csv`

### Common Endpoints
- **Health**: `GET /api/health`
- **API Docs**: `GET /api/docs`
- **Register**: `POST /api/auth/register`
- **Login**: `POST /api/auth/token`
- **Projects**: `GET /api/projects`
- **Forecasts**: `POST /api/forecasts/{project_id}/generate`

---

## ✅ Klaar voor gebruik!

Je hebt nu:
- ✅ Forecast Studio lokaal draaien
- ✅ Demo data geladen
- ✅ Alle features getest
- ✅ Productie deployment opties bekeken

**Veel succes met Forecast Studio!** 🚀📊
