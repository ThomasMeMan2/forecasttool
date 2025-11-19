# Forecast Studio

**Professional forecasting made simple** - An intuitive, drag-and-drop forecasting application designed for non-technical users to generate production-grade forecasts.

## 🎯 Vision

Forecast Studio is the "Canva for forecasting" - a tool that hides complexity while surfacing insights. Built for business users who need reliable forecasts without deep technical knowledge.

## ✨ Features (Phase 1 MVP)

- **Project Management**: Create and manage multiple isolated forecast projects
- **CSV Data Upload**: Simple drag-and-drop interface with automatic validation
- **Automated Forecasting**: Powered by StatsForecast's AutoARIMA model
- **Interactive Visualizations**: Beautiful charts with prediction intervals
- **Quality Metrics**: Confidence scores, MAPE, RMSE, and anomaly detection
- **CSV Export**: Download forecasts for external use

## 🏗️ Architecture

### Tech Stack

**Backend:**
- FastAPI (Python web framework)
- SQLAlchemy (ORM)
- PostgreSQL (Database)
- StatsForecast (Time series forecasting)
- Polars (Fast data processing)

**Frontend:**
- Next.js 14 (React framework)
- TypeScript (Type safety)
- Tailwind CSS (Styling)
- Recharts (Visualizations)

**Infrastructure:**
- Docker & Docker Compose (Containerization)
- pytest (Backend testing)

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM available
- Port 3000 (frontend) and 8000 (backend) available

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd forecasttool
```

2. **Start the application:**
```bash
docker-compose up --build
```

This will start:
- PostgreSQL database on port 5432
- Backend API on http://localhost:8000
- Frontend application on http://localhost:3000

3. **Access the application:**
   - Open your browser to http://localhost:3000
   - API documentation: http://localhost:8000/api/docs

### Sample Data Format

Your CSV file should have three columns:

```csv
id,timestamp,quantity
product_1,2024-01-01,100
product_1,2024-01-02,105
product_2,2024-01-01,200
product_2,2024-01-02,210
```

- **id**: Unique identifier for each time series (e.g., product_id, store_id)
- **timestamp**: Date or datetime in ISO format (YYYY-MM-DD)
- **quantity**: Numeric value to forecast

## 📖 Usage Guide

### 1. Create a Project

1. Click "New Project" on the home page
2. Enter a project name and optional description
3. Click "Create Project"

### 2. Upload Data

1. Navigate to the "Data Upload" tab
2. Drag and drop your CSV file or click to browse
3. Wait for validation and processing
4. Review data quality metrics

### 3. Generate Forecasts

1. Set forecast parameters:
   - **Horizon**: Number of periods to forecast (1-52)
   - **Confidence Level**: Prediction interval (80%, 90%, or 95%)
2. Click "Generate Forecasts"
3. Wait for processing (typically 10-30 seconds)

### 4. View Results

1. Switch to the "Forecasts" tab
2. Select a time series to view
3. Review:
   - Forecast chart with prediction intervals
   - Accuracy metrics (MAPE, RMSE)
   - Quality warnings and anomaly flags
   - Tabular forecast values

### 5. Export

1. Click "Export CSV" on any forecast
2. Save the file for use in spreadsheets or other tools

## 🧪 Development

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your settings

# Run database migrations
# (For MVP, tables are auto-created on startup)

# Run the server
uvicorn app.main:app --reload

# Run tests
pytest
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.local.example .env.local

# Run development server
npm run dev

# Build for production
npm run build

# Run type checking
npm run type-check
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest -v
```

Test coverage includes:
- Project CRUD operations
- Data validation and processing
- API endpoint integration tests

### Running Individual Tests

```bash
# Test projects
pytest tests/test_projects.py -v

# Test data processor
pytest tests/test_data_processor.py -v
```

## 📊 API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

### Key Endpoints

**Projects:**
- `POST /api/projects/` - Create project
- `GET /api/projects/` - List projects
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

**Datasets:**
- `POST /api/datasets/{project_id}/upload` - Upload CSV
- `GET /api/datasets/{project_id}/timeseries` - List time series

**Forecasts:**
- `POST /api/forecasts/{project_id}/generate` - Generate forecasts
- `GET /api/forecasts/{project_id}/forecasts` - List forecasts
- `GET /api/forecasts/{project_id}/forecasts/{id}/export` - Export CSV

## 🗂️ Project Structure

```
forecasttool/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration
│   │   ├── database.py          # Database setup
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── routers/             # API endpoints
│   │   │   ├── projects.py
│   │   │   ├── datasets.py
│   │   │   └── forecasts.py
│   │   └── services/            # Business logic
│   │       ├── data_processor.py
│   │       └── forecast_engine.py
│   ├── tests/                   # Test suite
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js pages
│   │   │   ├── page.tsx         # Home page
│   │   │   └── projects/        # Project pages
│   │   ├── components/          # React components
│   │   │   ├── DataUpload.tsx
│   │   │   └── ForecastView.tsx
│   │   ├── lib/
│   │   │   └── api.ts           # API client
│   │   └── types/
│   │       └── index.ts         # TypeScript types
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml           # Orchestration
└── README.md
```

## 🔧 Configuration

### Backend Configuration

Edit `backend/.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/forecast_studio

# Security
SECRET_KEY=your-secret-key-here

# App Settings
DEBUG=True
CORS_ORIGINS=["http://localhost:3000"]
MAX_UPLOAD_SIZE=52428800  # 50MB
```

### Frontend Configuration

Edit `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## 🚢 Production Deployment

### Security Checklist

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Set `DEBUG=False`
- [ ] Use strong database password
- [ ] Configure proper CORS origins
- [ ] Enable HTTPS/TLS
- [ ] Set up database backups
- [ ] Configure log aggregation
- [ ] Set up monitoring and alerts

### Docker Production Build

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables for Production

```env
# Backend
DATABASE_URL=postgresql://user:strong_password@db:5432/forecast_studio
SECRET_KEY=<generate-strong-random-key>
DEBUG=False
CORS_ORIGINS=["https://your-domain.com"]

# Frontend
NEXT_PUBLIC_API_URL=https://api.your-domain.com
```

## 📈 Roadmap

### Phase 2: Enhanced Forecasting
- [ ] Multiple model ensemble (AutoETS, Prophet, Neural networks)
- [ ] Global and ID-specific events support
- [ ] Manual forecast adjustments
- [ ] Benchmark comparisons (Seasonal Naive, SMA)

### Phase 3: Intelligence & UX
- [ ] LLM-powered insights and explanations
- [ ] Automated quality diagnostics
- [ ] Advanced visualization (ACF/PACF, decomposition)
- [ ] Airtable and Google Sheets integration

### Phase 4: Production Features
- [ ] User authentication and authorization
- [ ] Multi-tenant architecture
- [ ] Collaboration features (comments, versions)
- [ ] API access for programmatic usage
- [ ] Advanced export formats (PDF reports, Excel)

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🐛 Troubleshooting

### Port Already in Use

If ports 3000 or 8000 are in use:

```bash
# Check what's using the port
lsof -i :3000
lsof -i :8000

# Kill the process or change ports in docker-compose.yml
```

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps

# View logs
docker-compose logs db

# Reset database
docker-compose down -v
docker-compose up -d
```

### Frontend Build Errors

```bash
# Clear Next.js cache
cd frontend
rm -rf .next node_modules
npm install
npm run build
```

## 📧 Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review API documentation at `/api/docs`

## 🙏 Acknowledgments

- [StatsForecast](https://github.com/Nixtla/statsforecast) for forecasting models
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [Next.js](https://nextjs.org/) for the React framework
- [Recharts](https://recharts.org/) for beautiful charts

---

Built with ❤️ for making forecasting accessible to everyone.
