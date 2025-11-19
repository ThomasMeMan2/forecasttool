# Getting Started with Forecast Studio

This guide will walk you through setting up and using Forecast Studio for the first time.

## Installation

### Option 1: Using Docker (Recommended)

The easiest way to get started is using Docker Compose:

```bash
# Clone the repository
git clone <repository-url>
cd forecasttool

# Start all services
docker-compose up --build
```

Wait for all services to start. You should see:
- ✅ Database ready
- ✅ Backend running on http://localhost:8000
- ✅ Frontend running on http://localhost:3000

### Option 2: Manual Setup

If you prefer to run services individually:

**1. Database Setup:**
```bash
# Install PostgreSQL
# Create database
createdb forecast_studio
```

**2. Backend Setup:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure .env
cp .env.example .env
# Edit .env with your database URL

# Run server
uvicorn app.main:app --reload
```

**3. Frontend Setup:**
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

## First Steps

### 1. Access the Application

Open your browser to http://localhost:3000

You should see the Forecast Studio home page with:
- Application title and description
- "New Project" button
- Empty project list

### 2. Create Your First Project

1. Click **"New Project"**
2. Fill in the form:
   - **Name**: "My First Forecast" (required)
   - **Description**: "Testing the forecasting tool" (optional)
3. Click **"Create Project"**

You'll be redirected to the project detail page.

### 3. Prepare Your Data

Forecast Studio requires CSV files with three columns:

```csv
id,timestamp,quantity
product_1,2024-01-01,100
product_1,2024-01-02,105
product_1,2024-01-03,110
product_2,2024-01-01,50
product_2,2024-01-02,55
product_2,2024-01-03,60
```

**Column Requirements:**
- **id**: Identifier for each time series (string or number)
  - Examples: product_id, store_id, customer_id
  - Each unique ID becomes a separate forecast

- **timestamp**: Date in ISO format (YYYY-MM-DD) or datetime
  - Supported frequencies: daily, weekly, monthly, quarterly
  - Must be chronologically ordered per ID

- **quantity**: Numeric value to forecast
  - Can be integers or floats
  - Negative values are allowed but may trigger warnings

**Data Requirements:**
- Minimum 10 data points per time series
- At least 2-3 seasonal cycles recommended for best results
- Missing values will be flagged (can be addressed in future phases)

### 4. Upload Data

1. In your project, click the **"Data Upload"** tab (should be active by default)
2. **Drag and drop** your CSV file onto the upload area, or click to browse
3. Wait for upload and validation
4. Review the results:
   - Dataset info (filename, rows, quality score)
   - Data quality warnings (if any)
   - List of detected time series

**Common Upload Issues:**

- **"Missing required columns"**: Ensure your CSV has exactly: id, timestamp, quantity
- **"Invalid timestamp format"**: Use YYYY-MM-DD format
- **"File too large"**: Maximum 50MB per file
- **Quality warnings**: These won't block forecasting but indicate potential issues

### 5. Generate Forecasts

Once data is uploaded:

1. Scroll to **"Generate Forecast"** section
2. Configure parameters:
   - **Forecast Horizon**: How many periods ahead (default: 12)
     - For daily data: days ahead
     - For weekly data: weeks ahead
     - For monthly data: months ahead
   - **Confidence Level**: 80%, 90%, or 95% (default: 90%)
     - Higher = wider prediction intervals
3. Click **"Generate Forecasts"**
4. Wait for processing (typically 10-30 seconds for 5-10 time series)

**Processing Time:**
- 1-5 time series: ~10 seconds
- 10-20 time series: ~30 seconds
- 50+ time series: 1-2 minutes

### 6. View Results

Switch to the **"Forecasts"** tab:

1. **Select a forecast** from the grid
   - Green checkmark = good quality
   - Yellow warning = requires review

2. **Review metrics:**
   - Confidence Score (0-100): Overall forecast reliability
   - MAPE (Mean Absolute Percentage Error): Lower is better
   - RMSE (Root Mean Squared Error): Absolute error magnitude

3. **Analyze the chart:**
   - Blue line = forecast mean
   - Shaded areas = prediction intervals
     - Darker shade = 80% confidence
     - Lighter shade = 90% confidence

4. **Check the table:**
   - Detailed forecast values
   - Both upper and lower bounds
   - Sortable by date

### 7. Export Forecasts

To use forecasts in other tools:

1. Click **"Export CSV"** on any forecast
2. The file will download with columns:
   - timestamp
   - mean (forecast value)
   - lower_80, upper_80 (80% interval)
   - lower_90, upper_90 (90% interval)
3. Import into Excel, Google Sheets, or your BI tool

## Example Workflow

Let's walk through a complete example:

### Sample: Retail Sales Forecast

**Scenario:** You manage a store and want to forecast sales for 3 products.

**1. Create sample data (sample_data.csv):**
```csv
id,timestamp,quantity
product_A,2023-01-01,150
product_A,2023-01-02,155
product_A,2023-01-03,160
... (add 90 more days)
product_B,2023-01-01,200
product_B,2023-01-02,195
... (add 90 more days)
product_C,2023-01-01,80
product_C,2023-01-02,85
... (add 90 more days)
```

**2. Create project:**
- Name: "Q2 2024 Sales Forecast"
- Description: "3-month ahead forecast for top products"

**3. Upload data:**
- Upload sample_data.csv
- Verify: 3 time series detected, ~90 days each

**4. Generate forecast:**
- Horizon: 90 (for 90-day forecast)
- Confidence: 90%
- Click Generate

**5. Analyze results:**
- Check product_A: Look for trends or seasonality
- Compare forecast vs historical patterns
- Note any warnings (e.g., high volatility)

**6. Export for planning:**
- Export each forecast
- Share with inventory team
- Use for purchasing decisions

## Understanding Forecast Quality

### Confidence Score (0-100)

- **80-100**: High confidence - trust this forecast
- **60-79**: Moderate - use with caution
- **0-59**: Low - requires expert review

**Factors affecting score:**
- Data quantity (more is better)
- Data stability (less volatility)
- Model accuracy (lower error metrics)

### MAPE (Mean Absolute Percentage Error)

Average percentage error of historical predictions:
- **0-10%**: Excellent accuracy
- **10-20%**: Good accuracy
- **20-30%**: Moderate accuracy
- **30%+**: Poor accuracy (review data quality)

### Anomaly Flags

- **extreme_high_forecast**: Forecast much higher than historical
- **extreme_low_forecast**: Forecast much lower than historical
- **sudden_trend_change**: Sharp shift in trend
- **limited_historical_data**: < 30 data points

## Tips for Better Forecasts

### 1. Data Quality
- ✅ Provide at least 2-3 complete seasonal cycles
- ✅ Ensure data is clean (no obvious errors)
- ✅ Use consistent time intervals
- ❌ Avoid gaps in time series
- ❌ Don't mix different products in one time series

### 2. Horizon Selection
- Short-term (1-7 periods): Most accurate
- Medium-term (8-26 periods): Good for planning
- Long-term (27+ periods): Use with caution, wide intervals

### 3. Interpreting Intervals
- 80% interval: Narrower, more likely to contain actual value
- 90% interval: Wider, higher confidence coverage
- If intervals are very wide: Data may be too volatile for reliable forecasting

### 4. When to Trust Forecasts
- ✅ High confidence score (80+)
- ✅ Low MAPE (< 20%)
- ✅ Stable historical pattern
- ✅ No anomaly flags
- ❌ Requires review flag is set
- ❌ Very wide prediction intervals
- ❌ Recent trend changes

## Common Questions

**Q: How much data do I need?**
A: Minimum 10 points, but 30+ recommended. For seasonal data, provide at least 2 complete seasons.

**Q: Can I forecast multiple time series at once?**
A: Yes! Upload a CSV with multiple IDs. The system will forecast all of them.

**Q: What if my forecast looks wrong?**
A: Check data quality, ensure sufficient history, and verify no recent anomalies. Future phases will support manual adjustments.

**Q: How often should I regenerate forecasts?**
A: Whenever new data is available. Weekly or monthly regeneration is common.

**Q: Can I export all forecasts at once?**
A: Currently, export one at a time. Bulk export coming in future phases.

## Next Steps

Now that you've created your first forecast:

1. **Experiment**: Try different horizons and confidence levels
2. **Compare**: Upload new data and see how forecasts change
3. **Integrate**: Export forecasts to your planning tools
4. **Learn**: Check the API docs for programmatic access

## Getting Help

- **Documentation**: See README.md for full documentation
- **API Reference**: http://localhost:8000/api/docs
- **Issues**: Report bugs on GitHub
- **Examples**: Check `/examples` folder for sample datasets

---

Happy forecasting! 🚀
