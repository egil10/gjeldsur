"""
Norges Bank statistics API adapter.
Handles SDMX-JSON format data from Norges Bank's statistics API.
"""
import logging
import pandas as pd
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from .base import session, safe_request, AdapterError, DataFetchError, DataParseError

logger = logging.getLogger(__name__)

def fetch_sdmx_json(endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Fetch data from Norges Bank SDMX-JSON API.
    
    Args:
        endpoint: API endpoint (e.g., "IR/M.KPRA.SD.")
        params: Query parameters
    
    Returns:
        Parsed JSON response
    """
    base_url = "https://data.norges-bank.no/api/data"
    url = f"{base_url}/{endpoint}"
    
    # Default parameters
    default_params = {
        "format": "sdmx-json",
        "startPeriod": "2000-01-01",
        "endPeriod": "2025-08-01",
        "locale": "no"
    }
    
    if params:
        default_params.update(params)
    
    try:
        logger.info(f"Fetching Norges Bank data from: {url}")
        response = safe_request("GET", url, params=default_params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Successfully fetched {len(response.text)} bytes from Norges Bank API")
        
        return data
        
    except requests.exceptions.RequestException as e:
        raise DataFetchError(f"Failed to fetch data from Norges Bank API: {e}")
    except json.JSONDecodeError as e:
        raise DataParseError(f"Failed to parse JSON response from Norges Bank API: {e}")

def parse_sdmx_json(data: Dict[str, Any]) -> pd.DataFrame:
    """
    Parse SDMX-JSON format into a pandas DataFrame.
    
    Args:
        data: SDMX-JSON response data
    
    Returns:
        DataFrame with columns: date, value
    """
    try:
        # Extract data from SDMX-JSON structure
        data_sets = data.get("dataSets", [])
        if not data_sets:
            raise DataParseError("No data sets found in SDMX-JSON response")
        
        data_set = data_sets[0]
        series = data_set.get("series", {})
        
        if not series:
            raise DataParseError("No series found in SDMX-JSON response")
        
        # Get the first series (assuming single series for now)
        series_key = list(series.keys())[0]
        series_data = series[series_key]
        
        # Extract observations
        observations = series_data.get("observations", {})
        
        # Get dimension information for time periods
        structure = data.get("structure", {})
        dimensions = structure.get("dimensions", {})
        
        # Find time dimension
        time_dim = None
        for dim in dimensions.get("observation", []):
            if dim.get("id") == "TIME_PERIOD":
                time_dim = dim
                break
        
        if not time_dim:
            raise DataParseError("Time dimension not found in SDMX-JSON structure")
        
        # Create mapping from observation index to time period
        time_periods = time_dim.get("values", [])
        time_mapping = {}
        
        for i, period in enumerate(time_periods):
            time_mapping[str(i)] = period.get("id")
        
        # Build DataFrame
        records = []
        for obs_idx, obs_data in observations.items():
            if obs_idx in time_mapping:
                date_str = time_mapping[obs_idx]
                # Convert date string to datetime (handle various formats)
                try:
                    if len(date_str) == 4:  # Year only
                        date = pd.to_datetime(f"{date_str}-01-01")
                    elif len(date_str) == 7:  # Year-Month
                        date = pd.to_datetime(f"{date_str}-01")
                    else:  # Full date
                        date = pd.to_datetime(date_str)
                    
                    # Get the first value (assuming single value per observation)
                    value = obs_data[0] if obs_data else None
                    
                    if value is not None:
                        records.append({
                            "date": date,
                            "value": float(value)
                        })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse date '{date_str}' or value: {e}")
                    continue
        
        if not records:
            raise DataParseError("No valid observations found in SDMX-JSON data")
        
        df = pd.DataFrame(records)
        df = df.sort_values("date").reset_index(drop=True)
        
        logger.info(f"Successfully parsed {len(df)} observations from SDMX-JSON")
        return df
        
    except Exception as e:
        raise DataParseError(f"Failed to parse SDMX-JSON data: {e}")

def fetch_data(endpoint: str, params: Dict[str, Any] = None) -> pd.DataFrame:
    """
    Fetch and normalize data from Norges Bank API.
    
    Args:
        endpoint: API endpoint (e.g., "IR/M.KPRA.SD.")
        params: Query parameters
    
    Returns:
        DataFrame with normalized data (columns: date, value)
    """
    data = fetch_sdmx_json(endpoint, params)
    return parse_sdmx_json(data)

def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize Norges Bank data to standard format.
    
    Args:
        df: Raw DataFrame
    
    Returns:
        Normalized DataFrame with columns: date, value
    """
    # Ensure we have the required columns
    if "date" not in df.columns or "value" not in df.columns:
        raise DataParseError("DataFrame must have 'date' and 'value' columns")
    
    # Convert date column to datetime if needed
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    
    # Remove rows with invalid dates or values
    df = df.dropna(subset=["date", "value"])
    
    # Sort by date
    df = df.sort_values("date").reset_index(drop=True)
    
    return df

def fetch_and_normalize(endpoint: str, params: Dict[str, Any] = None) -> pd.DataFrame:
    """
    Fetch and normalize data from Norges Bank API in one step.
    
    Args:
        endpoint: API endpoint
        params: Query parameters
    
    Returns:
        Normalized DataFrame with columns: date, value
    """
    df = fetch_data(endpoint, params)
    return normalize(df)
