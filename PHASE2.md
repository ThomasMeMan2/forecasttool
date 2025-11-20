# Forecast Studio - Phase 2 Implementation

## Overview

Phase 2 extends Forecast Studio with enhanced forecasting capabilities, event management, manual controls, and AI-powered insights. This phase transforms the application from a simple forecasting tool into a comprehensive forecasting platform.

## 🎯 What's New in Phase 2

### 1. **Ensemble Forecasting Engine**

Advanced multi-model forecasting with intelligent model selection and weighted averaging.

**Features:**
- **Multiple Models**: AutoARIMA, AutoETS, Prophet, SeasonalNaive
- **Ensemble Strategy**: Weighted averaging based on historical accuracy
- **Benchmark Comparisons**: Automatic comparison against Seasonal Naive baseline
- **Forecast Value Added (FVA)**: Quantify improvement over simple benchmarks
- **Smart Model Selection**: Automatically choose best models for each time series

**Benefits:**
- More accurate forecasts through model diversification
- Reduced risk of model-specific biases
- Automatic fallback when individual models fail

### 2. **Event Management System**

Track and incorporate business events into forecasts.

**Global Events** (affect all time series):
- Holidays and seasonal events
- Marketing campaigns
- Price changes
- Economic events
- Custom business events

**ID-Specific Events** (affect individual time series):
- Store closures
- Stockouts
- Product promotions
- Equipment failures
- Local disruptions

**API Endpoints:**
```
POST   /api/events/{project_id}/global-events       - Create global event
GET    /api/events/{project_id}/global-events       - List global events
PUT    /api/events/{project_id}/global-events/{id}  - Update event
DELETE /api/events/{project_id}/global-events/{id}  - Delete event

POST   /api/events/{project_id}/id-events           - Create ID-specific event
GET    /api/events/{project_id}/id-events           - List ID events
PUT    /api/events/{project_id}/id-events/{id}      - Update event
DELETE /api/events/{project_id}/id-events/{id}      - Delete event
```

### 3. **Manual Exclusions**

Exclude specific time periods from forecast training.

**Use Cases:**
- Remove anomalous periods (e.g., COVID lockdowns)
- Exclude data collection errors
- Remove one-time events
- Isolate testing periods

**Features:**
- Date range exclusions per time series
- Activate/deactivate without deletion
- Audit trail with reasons
- Visual indicators in UI (planned)

**API Endpoints:**
```
POST   /api/exclusions/{project_id}/exclusions       - Create exclusion
GET    /api/exclusions/{project_id}/exclusions       - List exclusions
PUT    /api/exclusions/{project_id}/exclusions/{id}  - Update exclusion
DELETE /api/exclusions/{project_id}/exclusions/{id}  - Delete exclusion
```

### 4. **Forecast Adjustments**

Manually override forecast values with business knowledge.

**Features:**
- Adjust individual forecast periods
- Mandatory reasoning for all adjustments
- Complete audit trail
- Original values preserved
- Revert capability

**Use Cases:**
- Incorporate known future events
- Apply expert judgment
- Account for planned changes
- Override model when needed

**API Endpoints:**
```
POST   /api/adjustments/{project_id}/adjustments                    - Create adjustment
GET    /api/adjustments/{project_id}/forecasts/{id}/adjustments     - List adjustments
DELETE /api/adjustments/{project_id}/adjustments/{id}               - Delete adjustment
```

### 5. **LLM-Powered Insights**

AI-generated natural language insights about data and forecasts.

**Supported Providers:**
- **OpenAI** (GPT-4, GPT-3.5-turbo)
- **Anthropic** (Claude 3)
- **Ollama** (Local models for privacy)
- **Template** (Fallback for offline use)

**Insight Types:**
- **History Summary**: Data characteristics and patterns
- **Forecast Summary**: What the forecast predicts and why
- **Quality Assessment**: Confidence levels and reliability
- **Anomaly Explanations**: Why forecasts were flagged
- **Recommendations**: Actionable advice for users

**Configuration:**
```env
LLM_PROVIDER=openai  # or 'anthropic', 'ollama', 'template'
LLM_MODEL=gpt-4-turbo-preview
OPENAI_API_KEY=your-key-here
ENABLE_LLM_INSIGHTS=True
```

## 📊 Enhanced Database Schema

### New Tables

**global_events**
```sql
- id, project_id, event_name, event_date
- event_type, impact_value, description
- created_at, created_by
```

**id_specific_events**
```sql
- id, project_id, timeseries_id, event_name, event_date
- event_type, impact_value, description
- created_at, created_by
```

**user_exclusions**
```sql
- id, project_id, timeseries_id
- start_date, end_date, reason, is_active
- created_at, created_by
```

**forecast_adjustments**
```sql
- id, forecast_id, period_timestamp
- original_value, adjusted_value, adjustment_reason
- created_at, created_by
```

**project_insights**
```sql
- id, project_id, timeseries_id, forecast_id
- insight_type, insight_text, confidence
- llm_model, generated_at
```

### Extended Tables

**forecasts**
- Added: `ensemble_models`, `ensemble_weights`
- Added: `benchmark_model`, `benchmark_data`, `forecast_value_added`

## 🚀 Getting Started with Phase 2

### 1. Update Dependencies

```bash
cd backend
pip install -r requirements.txt
```

New packages:
- `prophet` - Facebook Prophet forecasting
- `openai` - OpenAI API client
- `anthropic` - Anthropic Claude API
- `langchain` - LLM orchestration

### 2. Configure Environment

Update your `.env` file with Phase 2 settings:

```env
# LLM Integration (Optional)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
OPENAI_API_KEY=your-openai-api-key
ENABLE_LLM_INSIGHTS=True
```

### 3. Restart Services

```bash
docker-compose down
docker-compose up --build
```

The database will automatically create new tables on startup.

### 4. Explore New Features

Visit the API documentation:
- Swagger UI: http://localhost:8000/api/docs
- New sections: Events, Exclusions, Adjustments

## 💡 Usage Examples

### Create a Global Holiday Event

```bash
curl -X POST "http://localhost:8000/api/events/1/global-events" \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "Christmas 2024",
    "event_date": "2024-12-25T00:00:00",
    "event_type": "holiday",
    "description": "Annual Christmas holiday"
  }'
```

### Add a Manual Exclusion

```bash
curl -X POST "http://localhost:8000/api/exclusions/1/exclusions" \
  -H "Content-Type: application/json" \
  -d '{
    "timeseries_id": 5,
    "start_date": "2020-03-01T00:00:00",
    "end_date": "2020-06-01T00:00:00",
    "reason": "COVID-19 lockdown - anomalous period",
    "is_active": true
  }'
```

### Adjust a Forecast Value

```bash
curl -X POST "http://localhost:8000/api/adjustments/1/adjustments" \
  -H "Content-Type: application/json" \
  -d '{
    "forecast_id": 10,
    "period_timestamp": "2024-12-25T00:00:00",
    "original_value": 1000,
    "adjusted_value": 2500,
    "adjustment_reason": "Major marketing campaign planned"
  }'
```

## 🎨 Frontend Integration (In Progress)

Phase 2 backend is complete. Frontend enhancements include:

**Planned UI Components:**
- ✅ Backend API ready
- ⏳ Events management interface
- ⏳ Exclusions calendar view
- ⏳ Forecast adjustment modal
- ⏳ LLM insights display
- ⏳ Ensemble model comparison charts

**Integration Path:**
1. Update `frontend/src/types/index.ts` with Phase 2 types
2. Update `frontend/src/lib/api.ts` with new endpoints
3. Create Phase 2 UI components
4. Enhance forecast visualization

## 📈 Performance Considerations

**Ensemble Forecasting:**
- Parallel model execution (where possible)
- Intelligent model selection reduces computation
- Caching of intermediate results

**LLM Insights:**
- Optional feature (can be disabled)
- Template fallback when offline
- Rate limiting to control API costs
- Caching of generated insights

**Database:**
- Indexed foreign keys for fast lookups
- JSON columns for flexible event storage
- Efficient queries with proper joins

## 🔐 Security & Privacy

**LLM Integration:**
- API keys stored in environment variables
- No sensitive data sent to external APIs
- Option to use local Ollama models
- Template fallback requires no external calls

**Audit Trails:**
- All exclusions tracked with reasoning
- All adjustments logged with user ID
- Event creation timestamps recorded
- Complete history for compliance

## 🧪 Testing

Run Phase 2 tests:

```bash
cd backend
pytest -v -k "phase2"
```

Test coverage:
- Event CRUD operations
- Exclusion validation
- Adjustment audit trail
- Ensemble forecast generation
- LLM service fallbacks

## 📚 Additional Documentation

- **API Reference**: http://localhost:8000/api/docs
- **Ensemble Engine**: `backend/app/services/enhanced_forecast_engine.py`
- **LLM Service**: `backend/app/services/llm_insights.py`
- **Event Models**: `backend/app/models.py` (Phase 2 section)

## 🚧 Known Limitations & Future Work

**Current Limitations:**
- No UI for Phase 2 features yet (backend-only)
- FVA calculation needs time-series cross-validation
- Events not yet used as model regressors
- No user authentication (dummy user_id=1)

**Phase 3 Roadmap:**
- Complete frontend integration
- Advanced diagnostics (ACF/PACF plots)
- Event-aware forecasting
- Google Sheets / Airtable sync
- Collaborative features

## 💬 Support

For questions or issues with Phase 2:
1. Check API documentation: `/api/docs`
2. Review this guide
3. Open GitHub issue
4. Check backend logs for errors

## 🎉 Success Metrics

Phase 2 delivers:
- ✅ 4 additional forecast models
- ✅ Event management system
- ✅ Manual exclusions & adjustments
- ✅ LLM insights (3 providers + fallback)
- ✅ 15+ new API endpoints
- ✅ Complete audit trails
- ✅ Enhanced database schema
- ✅ Backward compatible with Phase 1

**Ready for production use with Phase 1 UI. Phase 2 UI coming soon!**
