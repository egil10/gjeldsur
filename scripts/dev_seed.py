"""
Development seed script to create mock data when APIs are unavailable.
Generates realistic-looking data for all indicators in the catalog.
"""
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yaml

logger = logging.getLogger(__name__)

def generate_mock_series(
    start_date: str = "2020-01-01",
    end_date: str = "2024-12-31",
    frequency: str = "monthly",
    base_value: float = 100.0,
    trend: float = 0.02,
    volatility: float = 0.05,
    seasonality: float = 0.1
) -> List[Dict[str, Any]]:
    """
    Generate realistic mock time series data.
    
    Args:
        start_date: Start date for the series
        end_date: End date for the series
        frequency: Data frequency (monthly, quarterly, yearly)
        base_value: Base value for the series
        trend: Annual trend rate
        volatility: Random volatility
        seasonality: Seasonal variation
    
    Returns:
        List of dictionaries with date and value
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    # Generate date range
    if frequency == "monthly":
        date_range = pd.date_range(start, end, freq='M')
    elif frequency == "quarterly":
        date_range = pd.date_range(start, end, freq='Q')
    elif frequency == "yearly":
        date_range = pd.date_range(start, end, freq='Y')
    else:
        date_range = pd.date_range(start, end, freq='M')
    
    # Generate values with trend, volatility, and seasonality
    n_periods = len(date_range)
    time_index = np.arange(n_periods)
    
    # Trend component
    trend_component = base_value * (1 + trend) ** (time_index / 12)
    
    # Seasonal component
    seasonal_component = seasonality * base_value * np.sin(2 * np.pi * time_index / 12)
    
    # Random component
    random_component = np.random.normal(0, volatility * base_value, n_periods)
    
    # Combine components
    values = trend_component + seasonal_component + random_component
    
    # Ensure positive values
    values = np.maximum(values, base_value * 0.5)
    
    # Create series data
    series = [
        {
            "date": date.strftime("%Y-%m-%d"),
            "value": float(value)
        }
        for date, value in zip(date_range, values)
    ]
    
    return series

def create_mock_indicator(
    indicator_id: str,
    title: str,
    unit: str,
    frequency: str,
    source_name: str,
    source_url: str,
    base_value: float = 100.0,
    trend: float = 0.02
) -> Dict[str, Any]:
    """
    Create mock data for a single indicator.
    
    Args:
        indicator_id: Unique identifier
        title: Display title
        unit: Unit of measurement
        frequency: Data frequency
        source_name: Data source name
        source_url: Data source URL
        base_value: Base value for the series
        trend: Annual trend rate
    
    Returns:
        Complete indicator data structure
    """
    # Generate series data
    series = generate_mock_series(
        frequency=frequency,
        base_value=base_value,
        trend=trend
    )
    
    # Calculate snapshot statistics
    values = [point["value"] for point in series]
    latest_value = values[-1]
    
    # Month-over-month change
    mom_pct = None
    if len(values) > 1:
        mom_pct = float((values[-1] / values[-2] - 1) * 100)
    
    # Year-over-year change
    yoy_pct = None
    if len(values) > 13:
        yoy_pct = float((values[-1] / values[-13] - 1) * 100)
    
    snapshot = {
        "latest_value": latest_value,
        "mom_pct": mom_pct,
        "yoy_pct": yoy_pct,
        "min": float(min(values)),
        "max": float(max(values))
    }
    
    # Create complete indicator structure
    indicator_data = {
        "id": indicator_id,
        "title": title,
        "unit": unit,
        "frequency": frequency,
        "source": {
            "name": source_name,
            "url": source_url
        },
        "last_updated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "series": series,
        "snapshot": snapshot,
        "politics_overlay": True
    }
    
    return indicator_data

def create_mock_data():
    """Create mock data for all indicators in the catalog."""
    logger.info("Creating mock data for development")
    
    # Load catalog to get indicator configurations
    catalog_path = Path(__file__).parent.parent / "pipelines" / "catalog.yaml"
    
    if catalog_path.exists():
        with open(catalog_path, 'r', encoding='utf-8') as f:
            catalog = yaml.safe_load(f)
        indicators = catalog["indicators"]
    else:
        # Fallback: create basic indicators
        indicators = [
            {
                "id": "cpi",
                "title": "Consumer Price Index (CPI)",
                "unit": "Index (2015=100)",
                "frequency": "monthly",
                "source": {"name": "SSB", "url": "https://www.ssb.no/en/statbank/table/03013"}
            },
            {
                "id": "unemployment",
                "title": "Unemployment Rate",
                "unit": "Percent",
                "frequency": "monthly",
                "source": {"name": "NAV", "url": "https://www.nav.no/arbeid/arbeidsledig"}
            },
            {
                "id": "gdp",
                "title": "Gross Domestic Product (GDP)",
                "unit": "Million NOK",
                "frequency": "quarterly",
                "source": {"name": "SSB", "url": "https://www.ssb.no/en/statbank/table/1087"}
            }
        ]
    
    # Create mock data for each indicator
    for indicator in indicators:
        indicator_id = indicator["id"]
        logger.info(f"Creating mock data for {indicator_id}")
        
        # Create output directory
        out_dir = Path("data") / indicator_id
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate mock data with appropriate parameters
        if indicator_id == "cpi":
            base_value = 120.0
            trend = 0.03  # 3% annual inflation
        elif indicator_id == "unemployment":
            base_value = 4.5
            trend = -0.01  # Slight decline
        elif indicator_id == "gdp":
            base_value = 1000000.0
            trend = 0.025  # 2.5% annual growth
        elif indicator_id == "interest_rate":
            base_value = 4.0
            trend = 0.005  # Slight increase
        elif indicator_id == "oil_price":
            base_value = 80.0
            trend = 0.02  # 2% annual growth
        elif indicator_id == "housing_prices":
            base_value = 120.0
            trend = 0.04  # 4% annual growth
        elif indicator_id == "trade_balance":
            base_value = 50000.0
            trend = 0.01  # 1% annual growth
        elif indicator_id == "government_debt":
            base_value = 2000000.0
            trend = 0.03  # 3% annual growth
        elif indicator_id == "population":
            base_value = 5500.0  # 5.5 million
            trend = 0.008  # 0.8% annual growth
        elif indicator_id == "wage_growth":
            base_value = 3.0  # 3% wage growth
            trend = 0.001  # Slight increase
        else:
            base_value = 100.0
            trend = 0.02
        
        mock_data = create_mock_indicator(
            indicator_id=indicator_id,
            title=indicator.get("title", indicator_id),
            unit=indicator.get("unit", ""),
            frequency=indicator.get("frequency", "monthly"),
            source_name=indicator.get("source", {}).get("name", "Mock"),
            source_url=indicator.get("source", {}).get("url", ""),
            base_value=base_value,
            trend=trend
        )
        
        # Write JSON output
        json_path = out_dir / "latest.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(mock_data, f, ensure_ascii=False, indent=2)
        
        # Write CSV output
        df = pd.DataFrame(mock_data["series"])
        csv_path = out_dir / "latest.csv"
        df.to_csv(csv_path, index=False)
        
        # Write Parquet output
        parquet_path = out_dir / "history.parquet"
        df.to_parquet(parquet_path, index=False)
        
        logger.info(f"Created mock data: {json_path}, {csv_path}, {parquet_path}")
    
    # Create global index
    index_data = {
        "indicators": [
            {
                "id": indicator["id"],
                "path": f"/data/{indicator['id']}/latest.json",
                "title": indicator.get("title", indicator["id"]),
                "unit": indicator.get("unit", ""),
                "frequency": indicator.get("frequency", "unknown"),
                "politics_overlay": indicator.get("politics_overlay", True)
            }
            for indicator in indicators
        ],
        "last_updated": json.dumps({"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    }
    
    index_path = Path("data/index.json")
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Created index file: {index_path}")
    logger.info("Mock data creation completed successfully!")

if __name__ == "__main__":
    create_mock_data()
