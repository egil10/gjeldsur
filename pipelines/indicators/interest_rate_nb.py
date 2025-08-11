"""
Norges Bank Interest Rate indicator.
Fetches key policy rate data from Norges Bank API.
"""
import pandas as pd
import json
import time
from pathlib import Path
from datetime import datetime

from adapters.norges_bank import fetch_and_normalize

def fetch(params: dict) -> pd.DataFrame:
    """
    Fetch interest rate data from Norges Bank API.
    
    Args:
        params: Configuration parameters including endpoint
    
    Returns:
        DataFrame with columns: date, value
    """
    endpoint = params.get("endpoint", "IR/M.KPRA.SD.")
    api_params = params.get("api_params", {})
    
    df = fetch_and_normalize(endpoint, api_params)
    return df

def enrich(df: pd.DataFrame) -> dict:
    """
    Calculate snapshot statistics for interest rate data.
    
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
    
    # Month-over-month change (if we have at least 2 data points)
    mom = None
    if len(s) >= 2:
        mom = (s.iloc[-1] - s.iloc[-2]) * 100  # Interest rate changes in basis points
    
    # Year-over-year change (if we have at least 13 data points for monthly data)
    yoy = None
    if len(s) >= 13:
        yoy = (s.iloc[-1] - s.iloc[-13]) * 100
    
    return {
        "latest_value": float(s.iloc[-1]),
        "mom_pct": float(mom) if mom is not None else None,
        "yoy_pct": float(yoy) if yoy is not None else None,
        "min": float(s.min()),
        "max": float(s.max())
    }

def write_outputs(df: pd.DataFrame, meta: dict, out_dir: Path):
    """
    Write indicator data to output files.
    
    Args:
        df: DataFrame with columns: date, value
        meta: Snapshot statistics
        out_dir: Output directory path
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Create the output structure
    output = {
        "id": "interest_rate",
        "title": "Key Policy Rate (Styringsrenten)",
        "unit": "Percent",
        "frequency": "monthly",
        "source": {
            "name": "Norges Bank",
            "table": "M.KPRA.SD.",
            "url": "https://data.norges-bank.no/api/data/IR/M.KPRA.SD."
        },
        "last_updated_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "series": [
            {"date": d.strftime("%Y-%m-%d"), "value": float(v)}
            for d, v in df[["date", "value"]].values
        ],
        "snapshot": meta,
        "politics_overlay": True
    }
    
    # Write JSON file
    with open(out_dir / "latest.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # Write CSV file
    df.to_csv(out_dir / "latest.csv", index=False)
    
    # Write Parquet file (append to history)
    history_file = out_dir / "history.parquet"
    if history_file.exists():
        # Read existing history and append new data
        existing = pd.read_parquet(history_file)
        # Ensure date column is datetime in both DataFrames
        existing["date"] = pd.to_datetime(existing["date"])
        df["date"] = pd.to_datetime(df["date"])
        combined = pd.concat([existing, df], ignore_index=True)
        # Remove duplicates and sort
        combined = combined.drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)
        combined.to_parquet(history_file, index=False)
    else:
        # Create new history file
        df.to_parquet(history_file, index=False)

def create_plot(df: pd.DataFrame, out_dir: Path):
    """
    Create a static plot of the interest rate data.
    
    Args:
        df: DataFrame with columns: date, value
        out_dir: Output directory path
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        
        plt.figure(figsize=(12, 6))
        plt.plot(df["date"], df["value"], linewidth=2, color="#005AA3")
        plt.fill_between(df["date"], df["value"], alpha=0.3, color="#005AA3")
        
        plt.title("Norges Bank Key Policy Rate (Styringsrenten)", fontsize=14, fontweight="bold")
        plt.xlabel("Date")
        plt.ylabel("Interest Rate (%)")
        plt.grid(True, alpha=0.3)
        
        # Format x-axis
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        plt.gca().xaxis.set_major_locator(mdates.YearLocator(2))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # Save plot
        plot_path = out_dir / "interest_rate.png"
        plt.savefig(plot_path, dpi=300, bbox_inches="tight")
        plt.close()
        
        print(f"Plot saved to: {plot_path}")
        
    except ImportError:
        print("matplotlib not available, skipping plot generation")
    except Exception as e:
        print(f"Error creating plot: {e}")
