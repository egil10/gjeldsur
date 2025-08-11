#!/usr/bin/env python3
"""
FAST MVP: Create real data with political party coloring for 6 key indicators.
"""

import json
import pandas as pd
import requests
from pathlib import Path
from datetime import datetime
import numpy as np

# Political periods from March 2000 onwards
POLITICAL_PERIODS = [
    {
        "start": "2000-03-17",
        "end": "2001-10-19", 
        "parties": ["Ap"],
        "color": "#E03C31",
        "name": "Jens Stoltenbergs første regjering"
    },
    {
        "start": "2001-10-19",
        "end": "2005-10-17",
        "parties": ["KrF", "H", "V"],
        "color": "#005AA3", 
        "name": "Kjell Magne Bondeviks andre regjering"
    },
    {
        "start": "2005-10-17",
        "end": "2013-10-16",
        "parties": ["Ap", "SV", "Sp"],
        "color": "#E03C31",
        "name": "Jens Stoltenbergs andre regjering"
    },
    {
        "start": "2013-10-16",
        "end": "2021-10-14",
        "parties": ["H", "FrP", "V", "KrF"],
        "color": "#005AA3",
        "name": "Erna Solbergs regjering"
    },
    {
        "start": "2021-10-14",
        "end": "2025-12-31",  # Fixed the overflow date
        "parties": ["Ap", "Sp"],
        "color": "#E03C31",
        "name": "Jonas Gahr Støres regjering"
    }
]

# 6 key indicators to fetch
INDICATORS = [
    {
        "id": "cpi",
        "title": "Consumer Price Index (CPI)",
        "unit": "Index (2015=100)",
        "dataset_id": "1086",  # Consumer Price Index - All-item-index
        "field_guess": "value"
    },
    {
        "id": "unemployment", 
        "title": "Unemployment Rate",
        "unit": "Percent",
        "dataset_id": "1054",  # Labour force, employment and unemployment
        "field_guess": "value"
    },
    {
        "id": "house_prices",
        "title": "House Price Index",
        "unit": "Index (2015=100)", 
        "dataset_id": "1060",  # House price index
        "field_guess": "value"
    },
    {
        "id": "production",
        "title": "Industrial Production",
        "unit": "Index (2015=100)",
        "dataset_id": "27002",  # Index of production
        "field_guess": "value"
    },
    {
        "id": "retail_sales",
        "title": "Retail Sales",
        "unit": "Index (2015=100)",
        "dataset_id": "1064",  # Index of wholesale and retail sales
        "field_guess": "value"
    },
    {
        "id": "construction",
        "title": "Construction Costs",
        "unit": "Index (2015=100)",
        "dataset_id": "1056",  # Construction cost index
        "field_guess": "value"
    }
]

def fetch_ssb_data(dataset_id):
    """Fetch data from SSB API."""
    url = f"https://data.ssb.no/api/v0/dataset/{dataset_id}.json?lang=en"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch dataset {dataset_id}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching dataset {dataset_id}: {e}")
        return None

def parse_ssb_data_simple(data, field_guess):
    """Simple parsing of SSB data."""
    if not data or 'dataset' not in data:
        return None
    
    dataset = data['dataset']
    
    # Get time dimension
    time_dim = dataset.get('dimension', {}).get('Tid', {})
    if not time_dim:
        return None
    
    # Get time categories
    time_categories = time_dim.get('category', {})
    time_labels = time_categories.get('label', {})
    time_index = time_categories.get('index', {})
    
    # Get values
    values = dataset.get('value', [])
    
    if not values or not time_index:
        return None
    
    # Create DataFrame
    records = []
    for time_key, time_idx in time_index.items():
        if time_idx < len(values):
            value = values[time_idx]
            if isinstance(value, (int, float)) and value != 0:
                # Parse date
                try:
                    if 'M' in time_key:
                        date = pd.to_datetime(time_key, format='%YM%m')
                    elif 'Q' in time_key:
                        date = pd.to_datetime(time_key, format='%YQ%q')
                    else:
                        date = pd.to_datetime(time_key)
                    
                    records.append({
                        'date': date,
                        'value': value
                    })
                except:
                    continue
    
    if not records:
        return None
    
    df = pd.DataFrame(records)
    
    # Filter from March 2000 onwards
    df = df[df['date'] >= '2000-03-01']
    df = df.dropna()
    df = df.sort_values('date')
    
    return df

def add_political_coloring(df):
    """Add political period coloring to the data."""
    df['political_period'] = None
    df['political_color'] = None
    df['political_name'] = None
    
    for _, row in df.iterrows():
        date = row['date']
        for period in POLITICAL_PERIODS:
            start = pd.to_datetime(period['start'])
            end = pd.to_datetime(period['end'])
            
            if start <= date <= end:
                df.loc[df['date'] == date, 'political_period'] = period['name']
                df.loc[df['date'] == date, 'political_color'] = period['color']
                df.loc[df['date'] == date, 'political_name'] = period['name']
                break
    
    return df

def create_indicator_data(df, indicator):
    """Create the final indicator data structure."""
    if df is None or df.empty:
        return None
    
    # Calculate statistics
    latest_value = df['value'].iloc[-1]
    mom_pct = ((df['value'].iloc[-1] / df['value'].iloc[-2] - 1) * 100) if len(df) > 1 else 0
    yoy_pct = ((df['value'].iloc[-1] / df['value'].iloc[-13] - 1) * 100) if len(df) > 13 else 0
    
    return {
        "indicator": indicator['id'],
        "title": indicator['title'],
        "unit": indicator['unit'],
        "frequency": "monthly",
        "latest_value": round(latest_value, 2),
        "mom_pct": round(mom_pct, 2),
        "yoy_pct": round(yoy_pct, 2),
        "min": round(df['value'].min(), 2),
        "max": round(df['value'].max(), 2),
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

def main():
    """Main function to create MVP data."""
    print("🚀 Creating FAST MVP with real SSB data...")
    
    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    successful_indicators = []
    
    for indicator in INDICATORS:
        print(f"\n📊 Fetching {indicator['title']}...")
        
        # Fetch data
        data = fetch_ssb_data(indicator['dataset_id'])
        if data is None:
            print(f"  ❌ Failed to fetch {indicator['id']}")
            continue
        
        # Parse data
        df = parse_ssb_data_simple(data, indicator['field_guess'])
        if df is None or df.empty:
            print(f"  ❌ Failed to parse {indicator['id']}")
            continue
        
        # Add political coloring
        df = add_political_coloring(df)
        
        # Create indicator data
        indicator_data = create_indicator_data(df, indicator)
        if indicator_data is None:
            print(f"  ❌ Failed to create data for {indicator['id']}")
            continue
        
        # Save to file
        indicator_dir = data_dir / indicator['id']
        indicator_dir.mkdir(exist_ok=True)
        
        with open(indicator_dir / "latest.json", "w") as f:
            json.dump(indicator_data, f, indent=2)
        
        print(f"  ✅ {indicator['title']}: {len(df)} data points")
        successful_indicators.append(indicator)
    
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
            for indicator in successful_indicators
        ],
        "last_updated": datetime.now().isoformat() + "Z"
    }
    
    with open(data_dir / "index.json", "w") as f:
        json.dump(index_data, f, indent=2)
    
    print(f"\n🎉 MVP Complete!")
    print(f"✅ Created {len(successful_indicators)} indicators with political coloring")
    print(f"✅ Data saved to {data_dir}/")
    print(f"✅ Political periods from March 2000 onwards")
    
    return successful_indicators

if __name__ == "__main__":
    main()
