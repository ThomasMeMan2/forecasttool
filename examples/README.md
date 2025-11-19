# Example Data

This directory contains sample datasets for testing Forecast Studio.

## sample_data.csv

A simple example with 3 products showing daily sales over 30 days.

**Structure:**
- 3 time series (product_A, product_B, product_C)
- 30 days of data each (90 total rows)
- Daily frequency
- Upward trend in all products

**Use Case:**
Perfect for testing the basic forecasting workflow. Upload this file to your first project and generate a 7-14 day forecast.

**Expected Results:**
- All forecasts should have high confidence scores (80+)
- Clear upward trends should be detected
- Narrow prediction intervals due to stable patterns

## How to Use

1. Create a new project in Forecast Studio
2. Go to the Data Upload tab
3. Upload `sample_data.csv`
4. Generate forecasts with:
   - Horizon: 14 periods (2 weeks)
   - Confidence: 90%
5. Review results for all 3 products

## Creating Your Own Test Data

To create custom test data:

```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Generate dates
dates = pd.date_range(start='2023-01-01', periods=90, freq='D')

# Create multiple time series
data = []
for product_id in ['prod_1', 'prod_2', 'prod_3']:
    # Base value + trend + noise
    base = np.random.randint(100, 200)
    trend = np.linspace(0, 50, 90)
    noise = np.random.normal(0, 5, 90)

    for i, date in enumerate(dates):
        quantity = base + trend[i] + noise[i]
        data.append({
            'id': product_id,
            'timestamp': date.strftime('%Y-%m-%d'),
            'quantity': round(quantity, 2)
        })

df = pd.DataFrame(data)
df.to_csv('custom_data.csv', index=False)
```

## Data Patterns for Testing

### Trend
```python
# Upward trend
quantity = 100 + (day_number * 2)

# Downward trend
quantity = 200 - (day_number * 1.5)
```

### Seasonality
```python
# Weekly pattern (7-day cycle)
quantity = 100 + 20 * np.sin(2 * np.pi * day_number / 7)

# Monthly pattern
quantity = 100 + 30 * np.sin(2 * np.pi * day_number / 30)
```

### Volatility
```python
# High volatility
noise = np.random.normal(0, 20, num_days)

# Low volatility
noise = np.random.normal(0, 2, num_days)
```

### Complex Pattern
```python
# Trend + Seasonality + Noise
quantity = (
    100 +                          # Base
    (day_number * 0.5) +          # Trend
    (20 * np.sin(2 * np.pi * day_number / 7)) +  # Weekly seasonality
    np.random.normal(0, 5)        # Noise
)
```
