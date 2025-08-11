#!/usr/bin/env python3
"""
Generate synthetic data for all indicators to test the website.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import random

def generate_synthetic_data():
    """Generate synthetic data for all indicators."""
    
    # Base configuration
    base_date = datetime(2020, 1, 1)
    end_date = datetime.now()
    
    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Indicator configurations
    indicators = {
        "cpi": {
            "title": "Consumer Price Index (CPI)",
            "unit": "Index (2015=100)",
            "frequency": "monthly",
            "base_value": 100,
            "volatility": 0.02,
            "trend": 0.001
        },
        "unemployment": {
            "title": "Unemployment Rate",
            "unit": "Percent",
            "frequency": "monthly",
            "base_value": 4.5,
            "volatility": 0.3,
            "trend": -0.001
        },
        "gdp": {
            "title": "Gross Domestic Product (GDP)",
            "unit": "Million NOK",
            "frequency": "quarterly",
            "base_value": 1200000,
            "volatility": 0.05,
            "trend": 0.002
        },
        "interest_rate": {
            "title": "Key Policy Rate (Styringsrenten)",
            "unit": "Percent",
            "frequency": "monthly",
            "base_value": 1.5,
            "volatility": 0.1,
            "trend": 0.001
        },
        "oil_price": {
            "title": "Oil Price (Brent)",
            "unit": "USD per barrel",
            "frequency": "monthly",
            "base_value": 70,
            "volatility": 0.15,
            "trend": 0.001
        },
        "housing_prices": {
            "title": "Housing Price Index",
            "unit": "Index (2015=100)",
            "frequency": "monthly",
            "base_value": 120,
            "volatility": 0.03,
            "trend": 0.002
        },
        "trade_balance": {
            "title": "Trade Balance",
            "unit": "Million NOK",
            "frequency": "monthly",
            "base_value": 50000,
            "volatility": 0.2,
            "trend": 0.001
        },
        "government_debt": {
            "title": "Government Debt",
            "unit": "Million NOK",
            "frequency": "quarterly",
            "base_value": 800000,
            "volatility": 0.02,
            "trend": 0.003
        },
        "population": {
            "title": "Population",
            "unit": "Thousands",
            "frequency": "quarterly",
            "base_value": 5400,
            "volatility": 0.001,
            "trend": 0.0005
        },
        "wage_growth": {
            "title": "Wage Growth",
            "unit": "Percent",
            "frequency": "quarterly",
            "base_value": 3.0,
            "volatility": 0.5,
            "trend": 0.0001
        },
        "exchange_rates": {
            "title": "Exchange Rates (USD, EUR, GBP to NOK)",
            "unit": "NOK per foreign currency",
            "frequency": "monthly",
            "base_value": 10.5,
            "volatility": 0.08,
            "trend": 0.0002
        }
    }
    
    # Generate data for each indicator
    for indicator_id, config in indicators.items():
        print(f"Generating data for {indicator_id}...")
        
        # Create indicator directory
        indicator_dir = data_dir / indicator_id
        indicator_dir.mkdir(exist_ok=True)
        
        # Generate time series
        if config["frequency"] == "monthly":
            date_range = pd.date_range(base_date, end_date, freq='M')
        else:  # quarterly
            date_range = pd.date_range(base_date, end_date, freq='Q')
        
        # Generate synthetic values
        np.random.seed(42 + hash(indicator_id) % 1000)  # Consistent but different for each indicator
        values = []
        current_value = config["base_value"]
        
        for i, date in enumerate(date_range):
            # Add trend
            current_value += config["trend"] * current_value
            
            # Add random walk
            current_value += np.random.normal(0, config["volatility"] * current_value)
            
            # Ensure positive values for most indicators
            if indicator_id not in ["trade_balance"]:  # trade balance can be negative
                current_value = max(current_value, config["base_value"] * 0.5)
            
            values.append(current_value)
        
        # Create DataFrame
        df = pd.DataFrame({
            'date': date_range,
            'value': values
        })
        
        # Calculate statistics
        latest_value = values[-1]
        mom_pct = ((values[-1] / values[-2] - 1) * 100) if len(values) > 1 else 0
        yoy_pct = ((values[-1] / values[-13] - 1) * 100) if len(values) > 13 else 0
        
        # Create latest.json
        latest_data = {
            "indicator": indicator_id,
            "title": config["title"],
            "unit": config["unit"],
            "frequency": config["frequency"],
            "latest_value": round(latest_value, 2),
            "mom_pct": round(mom_pct, 2),
            "yoy_pct": round(yoy_pct, 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "data": [
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "value": round(value, 2)
                }
                for date, value in zip(date_range, values)
            ],
            "last_updated": datetime.now().isoformat() + "Z"
        }
        
        # Save latest.json
        with open(indicator_dir / "latest.json", "w") as f:
            json.dump(latest_data, f, indent=2)
        
        # Save CSV
        df.to_csv(indicator_dir / "latest.csv", index=False)
        
        print(f"  ✓ Generated {len(values)} data points for {indicator_id}")
    
    # Create/update index.json
    index_data = {
        "indicators": [
            {
                "id": indicator_id,
                "path": f"/data/{indicator_id}/latest.json",
                "title": config["title"],
                "unit": config["unit"],
                "frequency": config["frequency"],
                "politics_overlay": True
            }
            for indicator_id, config in indicators.items()
        ],
        "last_updated": datetime.now().isoformat() + "Z"
    }
    
    with open(data_dir / "index.json", "w") as f:
        json.dump(index_data, f, indent=2)
    
    print(f"\n✓ Generated synthetic data for {len(indicators)} indicators")
    print(f"✓ Updated index.json")
    print(f"✓ Data saved to {data_dir}/")

if __name__ == "__main__":
    generate_synthetic_data()
