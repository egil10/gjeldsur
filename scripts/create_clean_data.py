#!/usr/bin/env python3
"""
Create clean working data for the MVP.
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import numpy as np

# Political periods
POLITICAL_PERIODS = [
    {"start": "2000-03-17", "end": "2001-10-19", "color": "#E03C31", "name": "Jens Stoltenbergs første regjering"},
    {"start": "2001-10-19", "end": "2005-10-17", "color": "#005AA3", "name": "Kjell Magne Bondeviks andre regjering"},
    {"start": "2005-10-17", "end": "2013-10-16", "color": "#E03C31", "name": "Jens Stoltenbergs andre regjering"},
    {"start": "2013-10-16", "end": "2021-10-14", "color": "#005AA3", "name": "Erna Solbergs regjering"},
    {"start": "2021-10-14", "end": "2025-12-31", "color": "#E03C31", "name": "Jonas Gahr Støres regjering"}
]

def create_clean_data():
    """Create clean working data."""
    
    # Create data directory
    data_dir = Path("web/data")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate realistic data for each indicator
    indicators = [
        {
            "id": "cpi",
            "title": "Consumer Price Index (CPI)",
            "unit": "Index (2015=100)",
            "base_value": 100,
            "trend": 0.002,
            "volatility": 0.01
        },
        {
            "id": "unemployment",
            "title": "Unemployment Rate",
            "unit": "Percent",
            "base_value": 4.5,
            "trend": -0.001,
            "volatility": 0.3
        },
        {
            "id": "production",
            "title": "Industrial Production",
            "unit": "Index (2015=100)",
            "base_value": 100,
            "trend": 0.003,
            "volatility": 0.05
        },
        {
            "id": "construction",
            "title": "Construction Costs",
            "unit": "Index (2015=100)",
            "base_value": 100,
            "trend": 0.004,
            "volatility": 0.02
        }
    ]
    
    # Generate data for each indicator
    for indicator in indicators:
        print(f"Creating {indicator['id']}...")
        
        # Create date range
        dates = pd.date_range('2000-03-01', '2024-12-01', freq='M')
        
        # Generate realistic values
        np.random.seed(42 + len(indicator['id']))
        values = []
        current_value = indicator['base_value']
        
        for date in dates:
            # Add trend
            current_value += indicator['trend'] * current_value
            
            # Add random walk
            current_value += np.random.normal(0, indicator['volatility'] * current_value)
            
            # Ensure reasonable bounds
            if indicator['id'] == 'unemployment':
                current_value = max(2.0, min(8.0, current_value))
            else:
                current_value = max(current_value * 0.7, current_value)
            
            values.append(current_value)
        
        # Create DataFrame
        df = pd.DataFrame({
            'date': dates,
            'value': values
        })
        
        # Add political coloring
        df['political_period'] = None
        df['political_color'] = None
        
        for _, row in df.iterrows():
            date = row['date']
            for period in POLITICAL_PERIODS:
                start = pd.to_datetime(period['start'])
                end = pd.to_datetime(period['end'])
                
                if start <= date <= end:
                    df.loc[df['date'] == date, 'political_period'] = period['name']
                    df.loc[df['date'] == date, 'political_color'] = period['color']
                    break
        
        # Calculate statistics
        latest_value = values[-1]
        mom_pct = ((values[-1] / values[-2] - 1) * 100) if len(values) > 1 else 0
        yoy_pct = ((values[-1] / values[-13] - 1) * 100) if len(values) > 13 else 0
        
        # Create indicator data
        indicator_data = {
            "indicator": indicator['id'],
            "title": indicator['title'],
            "unit": indicator['unit'],
            "frequency": "monthly",
            "latest_value": round(latest_value, 2),
            "mom_pct": round(mom_pct, 2),
            "yoy_pct": round(yoy_pct, 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "data": [
                {
                    "date": row['date'].strftime("%Y-%m-%d"),
                    "value": round(row['value'], 2),
                    "political_period": row['political_period'],
                    "political_color": row['political_color']
                }
                for _, row in df.iterrows()
            ],
            "last_updated": datetime.now().isoformat() + "Z"
        }
        
        # Save to file
        indicator_dir = data_dir / indicator['id']
        indicator_dir.mkdir(exist_ok=True)
        
        with open(indicator_dir / "latest.json", "w") as f:
            json.dump(indicator_data, f, indent=2)
        
        print(f"  ✅ {indicator['title']}: {len(values)} data points")
    
    # Create index.json
    index_data = {
        "indicators": [
            {
                "id": indicator['id'],
                "path": f"/data/{indicator['id']}/latest.json",
                "title": indicator['title'],
                "unit": indicator['unit'],
                "frequency": "monthly",
                "politics_overlay": True
            }
            for indicator in indicators
        ],
        "last_updated": datetime.now().isoformat() + "Z"
    }
    
    with open(data_dir / "index.json", "w") as f:
        json.dump(index_data, f, indent=2)
    
    print(f"\n🎉 Clean data created!")
    print(f"✅ 4 indicators with realistic values")
    print(f"✅ Political period coloring")
    print(f"✅ Data saved to {data_dir}/")

if __name__ == "__main__":
    create_clean_data()
