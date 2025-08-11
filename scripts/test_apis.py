#!/usr/bin/env python3
"""
Test the real APIs provided by the user.
"""

import requests
import json
import pandas as pd
from datetime import datetime

def test_norges_bank_apis():
    """Test the Norges Bank APIs provided by the user."""
    
    apis = {
        "exchange_rates": "https://data.norges-bank.no/api/data/EXR/M.USD+EUR+GBP.NOK.SP?format=sdmx-json&startPeriod=2000-01-01&endPeriod=2025-08-01&locale=no",
        "interest_rate": "https://data.norges-bank.no/api/data/IR/M.KPRA.SD.?format=sdmx-json&startPeriod=2000-01-01&endPeriod=2025-08-01&locale=no"
    }
    
    for name, url in apis.items():
        print(f"\n=== Testing {name.upper()} API ===")
        print(f"URL: {url}")
        
        try:
            response = requests.get(url, timeout=30)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response size: {len(response.text)} bytes")
                
                # Try to extract some basic info
                if "data" in data and "dataSets" in data["data"]:
                    datasets = data["data"]["dataSets"]
                    print(f"Number of datasets: {len(datasets)}")
                    
                    if datasets:
                        dataset = datasets[0]
                        series = dataset.get("series", {})
                        print(f"Number of series: {len(series)}")
                        
                        if series:
                            # Get first series
                            first_series_key = list(series.keys())[0]
                            first_series = series[first_series_key]
                            observations = first_series.get("observations", {})
                            print(f"Number of observations: {len(observations)}")
                            
                            # Show a few sample observations
                            sample_obs = list(observations.items())[:3]
                            print("Sample observations:")
                            for obs_key, obs_value in sample_obs:
                                print(f"  {obs_key}: {obs_value}")
                
                print("✅ API working correctly")
                
            else:
                print(f"❌ API failed with status {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Error testing API: {e}")

def test_ssb_apis():
    """Test some common SSB APIs."""
    
    # Common SSB table IDs for economic indicators
    ssb_tables = {
        "cpi": "03013",  # Consumer Price Index
        "gdp": "1087",   # GDP
        "unemployment": "08974"  # Unemployment
    }
    
    for name, table_id in ssb_tables.items():
        print(f"\n=== Testing SSB {name.upper()} API ===")
        url = f"https://data.ssb.no/api/v0/en/table/{table_id}"
        
        try:
            response = requests.get(url, timeout=30)
            print(f"URL: {url}")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response size: {len(response.text)} bytes")
                print("✅ SSB API working correctly")
            else:
                print(f"❌ SSB API failed with status {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing SSB API: {e}")

if __name__ == "__main__":
    print("Testing real APIs...")
    print("=" * 50)
    
    test_norges_bank_apis()
    print("\n" + "=" * 50)
    test_ssb_apis()
    
    print("\n" + "=" * 50)
    print("API testing completed!")
