"""
SSB PXWeb adapter for fetching data from Statistics Norway.
Handles CSV/JSON data fetching and normalization to tidy format.
"""
import logging
from typing import Dict, Any, Optional
import pandas as pd
from io import StringIO

from .base import safe_request, DataFetchError, DataParseError

logger = logging.getLogger(__name__)

def fetch_csv(dataset: int, lang: str = "en") -> pd.DataFrame:
    """
    Fetch CSV data from SSB PXWeb API.
    
    Args:
        dataset: SSB dataset ID
        lang: Language code (en/no)
    
    Returns:
        DataFrame with raw SSB data
    """
    url = f"https://data.ssb.no/api/v0/dataset/{dataset}.csv?lang={lang}"
    
    try:
        resp = safe_request(url)
        df = pd.read_csv(StringIO(resp.text))
        logger.info(f"Fetched SSB dataset {dataset}: {len(df)} rows, {len(df.columns)} columns")
        return df
    except Exception as e:
        raise DataFetchError(f"Failed to fetch SSB dataset {dataset}: {e}")

def normalize(df: pd.DataFrame, date_field_guess: Optional[list] = None, 
              value_field_guess: Optional[list] = None) -> pd.DataFrame:
    """
    Normalize SSB DataFrame to tidy format (date, value).
    
    Args:
        df: Raw SSB DataFrame
        date_field_guess: List of possible date column names
        value_field_guess: List of possible value column names
    
    Returns:
        Normalized DataFrame with columns: date, value
    """
    if df.empty:
        raise DataParseError("Empty DataFrame provided")
    
    # Default guesses for date and value columns
    if date_field_guess is None:
        date_field_guess = ["Month", "time", "Tid", "måned", "år", "year"]
    
    if value_field_guess is None:
        value_field_guess = ["value", "values", "CPI", "KPI", "CPI total index"]
    
    # Try to find date column
    date_col = None
    for col in df.columns:
        if col.lower() in [x.lower() for x in date_field_guess]:
            date_col = col
            break
    
    # Fallback: find first datetime-parsable column
    if not date_col:
        for col in df.columns:
            try:
                pd.to_datetime(df[col].iloc[:10])  # Test first 10 rows
                date_col = col
                break
            except:
                continue
    
    # Try to find value column
    value_col = None
    for col in df.columns:
        if col.lower() in [x.lower() for x in value_field_guess]:
            value_col = col
            break
    
    # Fallback: find last numeric column
    if not value_col:
        for col in df.columns[::-1]:
            if pd.api.types.is_numeric_dtype(df[col]):
                value_col = col
                break
    
    if not date_col or not value_col:
        raise DataParseError(
            f"Could not infer date/value columns. "
            f"Available columns: {df.columns.tolist()}"
        )
    
    # Create normalized DataFrame
    out = df[[date_col, value_col]].copy()
    out.columns = ["date", "value"]
    
    # Convert date column
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    
    # Clean and sort
    out = out.dropna(subset=["date", "value"]).sort_values("date").reset_index(drop=True)
    
    if out.empty:
        raise DataParseError("No valid data after normalization")
    
    logger.info(f"Normalized data: {len(out)} rows from {out['date'].min()} to {out['date'].max()}")
    return out

def fetch_and_normalize(dataset: int, lang: str = "en", 
                       date_field_guess: Optional[list] = None,
                       value_field_guess: Optional[list] = None) -> pd.DataFrame:
    """
    Fetch and normalize SSB data in one step.
    
    Args:
        dataset: SSB dataset ID
        lang: Language code
        date_field_guess: Possible date column names
        value_field_guess: Possible value column names
    
    Returns:
        Normalized DataFrame with columns: date, value
    """
    df = fetch_csv(dataset, lang)
    return normalize(df, date_field_guess, value_field_guess)
