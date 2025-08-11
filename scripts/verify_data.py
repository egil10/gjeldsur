"""
Data verification script to check JSON schema and data quality.
Validates all indicator data files for required keys, data types, and ranges.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import yaml

logger = logging.getLogger(__name__)

def validate_json_schema(data: Dict[str, Any], indicator_id: str) -> List[str]:
    """
    Validate JSON schema for indicator data.
    
    Args:
        data: Indicator data dictionary
        indicator_id: Indicator identifier for error messages
    
    Returns:
        List of validation errors
    """
    errors = []
    
    # Required top-level keys
    required_keys = [
        "id", "title", "unit", "frequency", "source", 
        "last_updated_utc", "series", "snapshot", "politics_overlay"
    ]
    
    for key in required_keys:
        if key not in data:
            errors.append(f"{indicator_id}: Missing required key '{key}'")
    
    # Validate source structure
    if "source" in data:
        source = data["source"]
        if not isinstance(source, dict):
            errors.append(f"{indicator_id}: 'source' must be an object")
        else:
            if "name" not in source:
                errors.append(f"{indicator_id}: 'source' missing 'name'")
            if "url" not in source:
                errors.append(f"{indicator_id}: 'source' missing 'url'")
    
    # Validate series structure
    if "series" in data:
        series = data["series"]
        if not isinstance(series, list):
            errors.append(f"{indicator_id}: 'series' must be an array")
        else:
            for i, point in enumerate(series):
                if not isinstance(point, dict):
                    errors.append(f"{indicator_id}: series[{i}] must be an object")
                else:
                    if "date" not in point:
                        errors.append(f"{indicator_id}: series[{i}] missing 'date'")
                    if "value" not in point:
                        errors.append(f"{indicator_id}: series[{i}] missing 'value'")
                    elif not isinstance(point["value"], (int, float)):
                        errors.append(f"{indicator_id}: series[{i}] 'value' must be numeric")
    
    # Validate snapshot structure
    if "snapshot" in data:
        snapshot = data["snapshot"]
        if not isinstance(snapshot, dict):
            errors.append(f"{indicator_id}: 'snapshot' must be an object")
        else:
            required_snapshot_keys = ["latest_value", "min", "max"]
            for key in required_snapshot_keys:
                if key not in snapshot:
                    errors.append(f"{indicator_id}: 'snapshot' missing '{key}'")
                elif not isinstance(snapshot[key], (int, float)) and snapshot[key] is not None:
                    errors.append(f"{indicator_id}: 'snapshot.{key}' must be numeric or null")
    
    return errors

def validate_data_quality(data: Dict[str, Any], indicator_id: str) -> List[str]:
    """
    Validate data quality and business rules.
    
    Args:
        data: Indicator data dictionary
        indicator_id: Indicator identifier for error messages
    
    Returns:
        List of validation errors
    """
    errors = []
    
    # Check if series is sorted by date
    if "series" in data and len(data["series"]) > 1:
        dates = [point["date"] for point in data["series"]]
        try:
            parsed_dates = [datetime.strptime(date, "%Y-%m-%d") for date in dates]
            if parsed_dates != sorted(parsed_dates):
                errors.append(f"{indicator_id}: Series dates are not sorted")
        except ValueError:
            errors.append(f"{indicator_id}: Invalid date format in series")
    
    # Check for NaN values
    if "series" in data:
        for i, point in enumerate(data["series"]):
            if "value" in point and (point["value"] is None or str(point["value"]).lower() == "nan"):
                errors.append(f"{indicator_id}: series[{i}] contains NaN value")
    
    # Check last updated date is not in the future
    if "last_updated_utc" in data:
        try:
            last_updated = datetime.strptime(data["last_updated_utc"], "%Y-%m-%dT%H:%M:%SZ")
            if last_updated > datetime.utcnow() + timedelta(hours=1):  # Allow 1 hour buffer
                errors.append(f"{indicator_id}: 'last_updated_utc' is in the future")
        except ValueError:
            errors.append(f"{indicator_id}: Invalid 'last_updated_utc' format")
    
    # Check latest value is not None
    if "snapshot" in data and "latest_value" in data["snapshot"]:
        if data["snapshot"]["latest_value"] is None:
            errors.append(f"{indicator_id}: 'snapshot.latest_value' is null")
    
    return errors

def validate_value_ranges(data: Dict[str, Any], indicator_id: str) -> List[str]:
    """
    Validate that values are within plausible ranges for each indicator type.
    
    Args:
        data: Indicator data dictionary
        indicator_id: Indicator identifier for error messages
    
    Returns:
        List of validation errors
    """
    errors = []
    
    if "series" not in data:
        return errors
    
    values = [point["value"] for point in data["series"] if point["value"] is not None]
    if not values:
        return errors
    
    # Define plausible ranges for different indicator types
    ranges = {
        "cpi": (50, 200),  # CPI index values
        "unemployment": (0, 20),  # Unemployment rate percentage
        "gdp": (100000, 10000000),  # GDP in million NOK
        "interest_rate": (-5, 20),  # Interest rate percentage
        "oil_price": (0, 200),  # Oil price USD per barrel
        "housing_prices": (50, 200),  # Housing price index
        "trade_balance": (-1000000, 1000000),  # Trade balance in million NOK
        "government_debt": (0, 10000000),  # Government debt in million NOK
        "population": (1000, 100000),  # Population in thousands
        "wage_growth": (-20, 50)  # Wage growth percentage
    }
    
    if indicator_id in ranges:
        min_val, max_val = ranges[indicator_id]
        for i, value in enumerate(values):
            if value < min_val or value > max_val:
                errors.append(f"{indicator_id}: series[{i}] value {value} outside plausible range [{min_val}, {max_val}]")
    
    return errors

def verify_indicator_file(file_path: Path) -> List[str]:
    """
    Verify a single indicator JSON file.
    
    Args:
        file_path: Path to the JSON file
    
    Returns:
        List of validation errors
    """
    errors = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON in {file_path}: {e}"]
    except Exception as e:
        return [f"Error reading {file_path}: {e}"]
    
    indicator_id = data.get("id", file_path.parent.name)
    
    # Run all validations
    errors.extend(validate_json_schema(data, indicator_id))
    errors.extend(validate_data_quality(data, indicator_id))
    errors.extend(validate_value_ranges(data, indicator_id))
    
    return errors

def verify_all_data() -> Dict[str, Any]:
    """
    Verify all indicator data files.
    
    Returns:
        Dictionary with verification results
    """
    logger.info("Starting data verification")
    
    data_dir = Path("data")
    if not data_dir.exists():
        return {
            "status": "error",
            "message": "Data directory not found",
            "errors": []
        }
    
    all_errors = []
    verified_files = []
    
    # Find all latest.json files
    json_files = list(data_dir.rglob("latest.json"))
    
    if not json_files:
        return {
            "status": "error",
            "message": "No indicator data files found",
            "errors": []
        }
    
    for file_path in json_files:
        logger.info(f"Verifying {file_path}")
        errors = verify_indicator_file(file_path)
        
        if errors:
            all_errors.extend(errors)
        else:
            verified_files.append(str(file_path))
    
    # Check if index.json exists and is valid
    index_path = data_dir / "index.json"
    if index_path.exists():
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            if "indicators" not in index_data:
                all_errors.append("index.json missing 'indicators' key")
            else:
                logger.info(f"Index file contains {len(index_data['indicators'])} indicators")
        except Exception as e:
            all_errors.append(f"Error reading index.json: {e}")
    else:
        all_errors.append("index.json not found")
    
    # Summary
    total_files = len(json_files)
    successful_files = len(verified_files)
    failed_files = total_files - successful_files
    
    result = {
        "status": "success" if not all_errors else "error",
        "total_files": total_files,
        "successful_files": successful_files,
        "failed_files": failed_files,
        "verified_files": verified_files,
        "errors": all_errors
    }
    
    logger.info(f"Verification completed: {successful_files}/{total_files} files passed")
    
    if all_errors:
        logger.error("Validation errors found:")
        for error in all_errors:
            logger.error(f"  {error}")
    
    return result

def main():
    """Main verification execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify indicator data quality")
    parser.add_argument("--file", help="Verify specific file only")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    
    if args.file:
        # Verify single file
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            return 1
        
        errors = verify_indicator_file(file_path)
        if errors:
            print("Validation errors:")
            for error in errors:
                print(f"  {error}")
            return 1
        else:
            print(f"✓ {file_path} passed validation")
            return 0
    else:
        # Verify all data
        result = verify_all_data()
        
        if result["status"] == "success":
            print(f"✓ All {result['successful_files']} files passed validation")
            return 0
        else:
            print(f"✗ {result['failed_files']} files failed validation")
            for error in result["errors"]:
                print(f"  {error}")
            return 1

if __name__ == "__main__":
    exit(main())
