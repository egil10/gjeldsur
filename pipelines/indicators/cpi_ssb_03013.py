"""
Consumer Price Index (CPI) indicator from SSB dataset 03013.
Reference implementation for indicator modules.
"""
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any
import pandas as pd

from adapters.ssb_px import fetch_and_normalize

logger = logging.getLogger(__name__)

# Output directory
OUT = Path("data/cpi")
OUT.mkdir(parents=True, exist_ok=True)

def fetch(params: Dict[str, Any]) -> pd.DataFrame:
    """
    Fetch CPI data from SSB.
    
    Args:
        params: Configuration parameters from catalog.yaml
    
    Returns:
        DataFrame with columns: date, value
    """
    logger.info("Fetching CPI data from SSB")
    
    try:
        df = fetch_and_normalize(
            dataset=params["dataset"],
            lang=params.get("lang", "en"),
            date_field_guess=params.get("date_field_guess"),
            value_field_guess=params.get("value_field_guess")
        )
        
        logger.info(f"Successfully fetched {len(df)} CPI data points")
        return df
        
    except Exception as e:
        logger.error(f"Failed to fetch CPI data: {e}")
        raise

def enrich(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute snapshot statistics from CPI data.
    
    Args:
        df: DataFrame with columns: date, value
    
    Returns:
        Dictionary with snapshot statistics
    """
    if df.empty:
        return {
            "latest_value": None,
            "mom_pct": None,
            "yoy_pct": None,
            "min": None,
            "max": None
        }
    
    s = df["value"]
    
    # Latest value
    latest_value = float(s.iloc[-1])
    
    # Month-over-month change (if we have at least 2 points)
    mom_pct = None
    if len(s) > 1:
        mom_pct = float((s.iloc[-1] / s.iloc[-2] - 1) * 100)
    
    # Year-over-year change (if we have at least 13 points for monthly data)
    yoy_pct = None
    if len(s) > 13:
        yoy_pct = float((s.iloc[-1] / s.iloc[-13] - 1) * 100)
    
    # Min and max values
    min_val = float(s.min())
    max_val = float(s.max())
    
    snapshot = {
        "latest_value": latest_value,
        "mom_pct": mom_pct,
        "yoy_pct": yoy_pct,
        "min": min_val,
        "max": max_val
    }
    
    logger.info(f"CPI snapshot: {latest_value:.1f} (MoM: {mom_pct:+.1f}%, YoY: {yoy_pct:+.1f}%)")
    return snapshot

def write_outputs(df: pd.DataFrame, meta: Dict[str, Any], out_dir: Path = OUT) -> None:
    """
    Write CPI data outputs in all required formats.
    
    Args:
        df: DataFrame with columns: date, value
        meta: Snapshot statistics
        out_dir: Output directory
    """
    logger.info(f"Writing CPI outputs to {out_dir}")
    
    # Ensure output directory exists
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare series data for JSON
    series = [
        {"date": d.strftime("%Y-%m-%d"), "value": float(v)}
        for d, v in df.values
    ]
    
    # Create the complete output structure
    output = {
        "id": "cpi",
        "title": "Consumer Price Index (CPI)",
        "unit": "Index (2015=100)",
        "frequency": "monthly",
        "source": {
            "name": "SSB",
            "table": "03013",
            "url": "https://www.ssb.no/en/statbank/table/03013"
        },
        "last_updated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "series": series,
        "snapshot": meta,
        "politics_overlay": True
    }
    
    # Write JSON output
    json_path = out_dir / "latest.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # Write CSV output
    csv_path = out_dir / "latest.csv"
    df.to_csv(csv_path, index=False)
    
    # Append to history Parquet file
    parquet_path = out_dir / "history.parquet"
    if parquet_path.exists():
        # Read existing history and append
        history_df = pd.read_parquet(parquet_path)
        # Remove duplicates and append new data
        combined_df = pd.concat([history_df, df]).drop_duplicates(subset=['date']).sort_values('date')
        combined_df.to_parquet(parquet_path, index=False)
    else:
        # Create new history file
        df.to_parquet(parquet_path, index=False)
    
    logger.info(f"Wrote CPI outputs: {json_path}, {csv_path}, {parquet_path}")

def create_plot(df: pd.DataFrame, out_dir: Path = OUT) -> None:
    """
    Create a static plot of CPI data (optional).
    
    Args:
        df: DataFrame with columns: date, value
        out_dir: Output directory
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot data
        ax.plot(df['date'], df['value'], linewidth=2, color='#005AA3')
        
        # Formatting
        ax.set_title('Consumer Price Index (CPI)', fontsize=16, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Index (2015=100)')
        ax.grid(True, alpha=0.3)
        
        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.set_major_locator(mdates.YearLocator())
        
        # Rotate x-axis labels
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Tight layout
        plt.tight_layout()
        
        # Save plot
        plot_path = out_dir / "cpi.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Created CPI plot: {plot_path}")
        
    except ImportError:
        logger.warning("matplotlib not available, skipping plot creation")
    except Exception as e:
        logger.error(f"Failed to create CPI plot: {e}")

def main():
    """Main function for standalone execution."""
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent))
    
    # Default parameters
    params = {
        "dataset": 1086,
        "lang": "en",
        "date_field_guess": ["Month", "time", "Tid"],
        "value_field_guess": ["value", "CPI total index"]
    }
    
    try:
        # Fetch data
        df = fetch(params)
        
        # Enrich with statistics
        meta = enrich(df)
        
        # Write outputs
        write_outputs(df, meta)
        
        # Create plot
        create_plot(df)
        
        print("CPI indicator processing completed successfully!")
        
    except Exception as e:
        logger.error(f"CPI processing failed: {e}")
        raise

if __name__ == "__main__":
    main()
