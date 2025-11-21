"""
Demo Data Generator for Forecast Studio
Generates realistic time series data with various patterns for testing
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Set random seed for reproducibility
np.random.seed(42)

def generate_demo_data():
    """Generate comprehensive demo dataset with multiple time series patterns"""

    # Date range: 2 years of daily data
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2023, 12, 31)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')

    data_points = []

    # ===== Product A: Strong trend + weekly seasonality =====
    base_value_a = 100
    trend_a = np.linspace(0, 50, len(dates))  # Upward trend
    weekly_seasonality_a = 20 * np.sin(2 * np.pi * np.arange(len(dates)) / 7)
    noise_a = np.random.normal(0, 5, len(dates))
    values_a = base_value_a + trend_a + weekly_seasonality_a + noise_a

    for i, date in enumerate(dates):
        data_points.append({
            'unique_id': 'PRODUCT_A',
            'ds': date.strftime('%Y-%m-%d'),
            'y': max(0, values_a[i])  # Ensure non-negative
        })

    # ===== Product B: Monthly seasonality + holiday spikes =====
    base_value_b = 200
    monthly_seasonality_b = 40 * np.sin(2 * np.pi * np.arange(len(dates)) / 30.5)

    # Add holiday spikes (Black Friday, Christmas, etc.)
    holiday_effect_b = np.zeros(len(dates))
    for i, date in enumerate(dates):
        # Black Friday (last Friday of November)
        if date.month == 11 and date.day >= 23 and date.day <= 30 and date.weekday() == 4:
            holiday_effect_b[i] = 100
        # Christmas season (Dec 15-25)
        elif date.month == 12 and 15 <= date.day <= 25:
            holiday_effect_b[i] = 80
        # New Year
        elif date.month == 1 and date.day <= 7:
            holiday_effect_b[i] = 60

    noise_b = np.random.normal(0, 10, len(dates))
    values_b = base_value_b + monthly_seasonality_b + holiday_effect_b + noise_b

    for i, date in enumerate(dates):
        data_points.append({
            'unique_id': 'PRODUCT_B',
            'ds': date.strftime('%Y-%m-%d'),
            'y': max(0, values_b[i])
        })

    # ===== Product C: Declining trend + outliers =====
    base_value_c = 150
    declining_trend_c = np.linspace(0, -40, len(dates))
    noise_c = np.random.normal(0, 8, len(dates))

    # Add random outliers
    outlier_indices = np.random.choice(len(dates), size=15, replace=False)
    outliers_c = np.zeros(len(dates))
    outliers_c[outlier_indices] = np.random.uniform(-50, -30, size=15)

    values_c = base_value_c + declining_trend_c + noise_c + outliers_c

    for i, date in enumerate(dates):
        data_points.append({
            'unique_id': 'PRODUCT_C',
            'ds': date.strftime('%Y-%m-%d'),
            'y': max(0, values_c[i])
        })

    # ===== Store 001: Stable with weekly pattern =====
    base_value_s1 = 500
    weekly_pattern_s1 = 100 * np.sin(2 * np.pi * np.arange(len(dates)) / 7)
    # Weekend boost
    weekend_boost_s1 = np.array([30 if pd.Timestamp(d).weekday() >= 5 else 0 for d in dates])
    noise_s1 = np.random.normal(0, 15, len(dates))
    values_s1 = base_value_s1 + weekly_pattern_s1 + weekend_boost_s1 + noise_s1

    for i, date in enumerate(dates):
        data_points.append({
            'unique_id': 'STORE_001',
            'ds': date.strftime('%Y-%m-%d'),
            'y': max(0, values_s1[i])
        })

    # ===== Store 002: Growth with stockout event =====
    base_value_s2 = 300
    growth_s2 = np.linspace(0, 100, len(dates))
    weekly_s2 = 30 * np.sin(2 * np.pi * np.arange(len(dates)) / 7)

    # Simulate stockout event (July 2023 for 2 weeks)
    stockout_effect_s2 = np.zeros(len(dates))
    for i, date in enumerate(dates):
        if date.year == 2023 and date.month == 7 and 1 <= date.day <= 14:
            stockout_effect_s2[i] = -200  # Severe drop

    noise_s2 = np.random.normal(0, 12, len(dates))
    values_s2 = base_value_s2 + growth_s2 + weekly_s2 + stockout_effect_s2 + noise_s2

    for i, date in enumerate(dates):
        data_points.append({
            'unique_id': 'STORE_002',
            'ds': date.strftime('%Y-%m-%d'),
            'y': max(0, values_s2[i])
        })

    # ===== Region North: Seasonal business (high in winter) =====
    base_value_rn = 250
    # Strong annual seasonality (peak in winter)
    annual_seasonality_rn = 150 * np.cos(2 * np.pi * (np.arange(len(dates)) - 365) / 365)
    noise_rn = np.random.normal(0, 20, len(dates))
    values_rn = base_value_rn + annual_seasonality_rn + noise_rn

    for i, date in enumerate(dates):
        data_points.append({
            'unique_id': 'REGION_NORTH',
            'ds': date.strftime('%Y-%m-%d'),
            'y': max(0, values_rn[i])
        })

    # Create DataFrame
    df = pd.DataFrame(data_points)

    return df


def generate_events_data():
    """Generate events data (global and ID-specific)"""

    global_events = [
        {
            'event_name': 'Black Friday 2022',
            'event_date': '2022-11-25',
            'event_type': 'holiday',
            'description': 'Major shopping holiday with significant sales'
        },
        {
            'event_name': 'Christmas 2022',
            'event_date': '2022-12-25',
            'event_type': 'holiday',
            'description': 'Christmas holiday season'
        },
        {
            'event_name': 'New Year 2023',
            'event_date': '2023-01-01',
            'event_type': 'holiday',
            'description': 'New Year celebration'
        },
        {
            'event_name': 'Spring Campaign',
            'event_date': '2023-03-15',
            'event_type': 'campaign',
            'description': 'Marketing campaign launch'
        },
        {
            'event_name': 'Summer Sale',
            'event_date': '2023-06-01',
            'event_type': 'campaign',
            'description': 'Major summer sale event'
        },
        {
            'event_name': 'Black Friday 2023',
            'event_date': '2023-11-24',
            'event_type': 'holiday',
            'description': 'Black Friday sales event'
        },
        {
            'event_name': 'Price Increase',
            'event_date': '2023-09-01',
            'event_type': 'price_change',
            'description': '10% price increase across product line'
        }
    ]

    id_specific_events = [
        {
            'unique_id': 'STORE_002',
            'event_name': 'Stockout Event',
            'event_date': '2023-07-01',
            'event_type': 'stockout',
            'description': 'Major stockout lasting 2 weeks'
        },
        {
            'unique_id': 'PRODUCT_B',
            'event_name': 'Product Launch Promo',
            'event_date': '2023-04-15',
            'event_type': 'promotion',
            'description': 'Special promotional campaign for Product B'
        },
        {
            'unique_id': 'PRODUCT_C',
            'event_name': 'Discontinuation Notice',
            'event_date': '2023-10-01',
            'event_type': 'custom',
            'description': 'Product C marked for discontinuation'
        },
        {
            'unique_id': 'REGION_NORTH',
            'event_name': 'Weather Event',
            'event_date': '2023-02-10',
            'event_type': 'custom',
            'description': 'Severe winter storm affecting region'
        }
    ]

    return pd.DataFrame(global_events), pd.DataFrame(id_specific_events)


if __name__ == "__main__":
    print("Generating demo data...")

    # Generate time series data
    demo_df = generate_demo_data()
    demo_df.to_csv('demo_timeseries_data.csv', index=False)
    print(f"✓ Created demo_timeseries_data.csv with {len(demo_df)} rows")
    print(f"  - Time series IDs: {demo_df['unique_id'].unique().tolist()}")
    print(f"  - Date range: {demo_df['ds'].min()} to {demo_df['ds'].max()}")

    # Generate events data
    global_events_df, id_events_df = generate_events_data()
    global_events_df.to_csv('demo_global_events.csv', index=False)
    id_events_df.to_csv('demo_id_events.csv', index=False)
    print(f"✓ Created demo_global_events.csv with {len(global_events_df)} events")
    print(f"✓ Created demo_id_events.csv with {len(id_events_df)} events")

    # Print summary statistics
    print("\n📊 Data Summary:")
    for ts_id in demo_df['unique_id'].unique():
        ts_data = demo_df[demo_df['unique_id'] == ts_id]
        print(f"\n{ts_id}:")
        print(f"  Mean: {ts_data['y'].mean():.2f}")
        print(f"  Std: {ts_data['y'].std():.2f}")
        print(f"  Min: {ts_data['y'].min():.2f}")
        print(f"  Max: {ts_data['y'].max():.2f}")
        print(f"  Data points: {len(ts_data)}")

    print("\n✅ Demo data generation complete!")
