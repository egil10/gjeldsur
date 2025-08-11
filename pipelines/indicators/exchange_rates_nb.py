#!/usr/bin/env python3
"""
Exchange Rates indicator using Norges Bank API.
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from adapters.norges_bank import fetch_and_normalize

OUT = Path("data/exchange_rates")
OUT.mkdir(parents=True, exist_ok=True)

def fetch(params):
    """Fetch exchange rate data from Norges Bank."""
    endpoint = "EXR/M.USD+EUR+GBP.NOK.SP"
    api_params = {
        "startPeriod": "2000-01-01",
        "endPeriod": "2025-08-01",
        "locale": "no"
    }
    
    return fetch_and_normalize(endpoint, api_params)

def enrich(df):
    """Enrich the data with calculated statistics."""
    if df.empty:
        return None
    
    # Get the latest values for each currency
    latest_data = {}
    for currency in ['USD', 'EUR', 'GBP']:
        currency_data = df[df['CURRENCY'] == currency]['value']
        if not currency_data.empty:
            latest_data[currency] = {
                'latest': float(currency_data.iloc[-1]),
                'mom_pct': float((currency_data.iloc[-1]/currency_data.iloc[-2]-1)*100) if len(currency_data) > 1 else None,
                'yoy_pct': float((currency_data.iloc[-1]/currency_data.iloc[-13]-1)*100) if len(currency_data) > 13 else None,
                'min': float(currency_data.min()),
                'max': float(currency_data.max())
            }
    
    return {
        'latest_data': latest_data,
        'last_updated': datetime.now().isoformat() + "Z"
    }

def write_outputs(df, meta, out_dir=OUT):
    """Write the processed data to files."""
    if df.empty:
        print("No data to write")
        return
    
    # Save CSV
    df.to_csv(out_dir / "latest.csv", index=False)
    
    # Save JSON
    latest_data = {
        "indicator": "exchange_rates",
        "title": "Exchange Rates (USD, EUR, GBP to NOK)",
        "unit": "NOK per foreign currency",
        "frequency": "monthly",
        "currencies": meta['latest_data'],
        "data": [
            {
                "date": row['date'].strftime("%Y-%m-%d"),
                "currency": row['CURRENCY'],
                "value": round(row['value'], 4)
            }
            for _, row in df.iterrows()
        ],
        "last_updated": meta['last_updated']
    }
    
    with open(out_dir / "latest.json", "w") as f:
        json.dump(latest_data, f, indent=2)
    
    print(f"Exchange rates data saved to {out_dir}/")

if __name__ == "__main__":
    # Test the indicator
    print("Fetching exchange rates data...")
    df = fetch({})
    if df is not None and not df.empty:
        meta = enrich(df)
        if meta:
            write_outputs(df, meta)
            print("✓ Exchange rates indicator completed successfully")
        else:
            print("✗ Failed to enrich exchange rates data")
    else:
        print("✗ Failed to fetch exchange rates data")
