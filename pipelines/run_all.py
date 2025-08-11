"""
Main pipeline orchestrator for processing all economic indicators.
Loads catalog.yaml and runs fetch→enrich→write for each indicator.
"""
import argparse
import importlib
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List
import yaml

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.dev_seed import create_mock_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_catalog() -> Dict[str, Any]:
    """
    Load the indicator catalog from YAML file.
    
    Returns:
        Dictionary with catalog configuration
    """
    catalog_path = Path(__file__).parent / "catalog.yaml"
    
    if not catalog_path.exists():
        raise FileNotFoundError(f"Catalog file not found: {catalog_path}")
    
    with open(catalog_path, 'r', encoding='utf-8') as f:
        catalog = yaml.safe_load(f)
    
    logger.info(f"Loaded catalog with {len(catalog['indicators'])} indicators")
    return catalog

def process_indicator(indicator_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single indicator: fetch, enrich, write outputs.
    
    Args:
        indicator_config: Indicator configuration from catalog
    
    Returns:
        Dictionary with processing results
    """
    indicator_id = indicator_config["id"]
    logger.info(f"Processing indicator: {indicator_id}")
    
    try:
        # Import the indicator module
        module_name = f"pipelines.indicators.{indicator_id}_ssb_03013"
        if indicator_id == "cpi":
            # Special case for CPI (our reference implementation)
            module = importlib.import_module(module_name)
        else:
            # For other indicators, try different naming patterns
            possible_names = [
                f"pipelines.indicators.{indicator_id}",
                f"pipelines.indicators.{indicator_id}_{indicator_config['adapter']}",
                module_name
            ]
            
            module = None
            for name in possible_names:
                try:
                    module = importlib.import_module(name)
                    break
                except ImportError:
                    continue
            
            if module is None:
                logger.warning(f"No module found for indicator {indicator_id}, skipping")
                return {
                    "id": indicator_id,
                    "status": "skipped",
                    "error": "Module not found"
                }
        
        # Fetch data
        df = module.fetch(indicator_config["params"])
        
        # Enrich with statistics
        meta = module.enrich(df)
        
        # Write outputs
        out_dir = Path(indicator_config["out_dir"])
        module.write_outputs(df, meta, out_dir)
        
        # Create plot if function exists
        if hasattr(module, 'create_plot'):
            try:
                module.create_plot(df, out_dir)
            except Exception as e:
                logger.warning(f"Failed to create plot for {indicator_id}: {e}")
        
        logger.info(f"Successfully processed {indicator_id}")
        return {
            "id": indicator_id,
            "status": "success",
            "rows": len(df),
            "latest_value": meta.get("latest_value")
        }
        
    except Exception as e:
        logger.error(f"Failed to process {indicator_id}: {e}")
        return {
            "id": indicator_id,
            "status": "error",
            "error": str(e)
        }

def create_index(indicators: List[Dict[str, Any]]) -> None:
    """
    Create a global index.json file listing all indicators.
    
    Args:
        indicators: List of indicator configurations
    """
    index_data = {
        "indicators": [
            {
                "id": indicator["id"],
                "path": f"/data/{indicator['id']}/latest.json",
                "title": indicator.get("title", indicator["id"]),
                "unit": indicator.get("unit", ""),
                "frequency": indicator.get("frequency", "unknown"),
                "politics_overlay": indicator.get("politics_overlay", False)
            }
            for indicator in indicators
        ],
        "last_updated": json.dumps({"timestamp": "2024-01-01T00:00:00Z"})
    }
    
    index_path = Path("data/index.json")
    index_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Created index file: {index_path}")

def main():
    """Main pipeline execution."""
    parser = argparse.ArgumentParser(description="Process all economic indicators")
    parser.add_argument("--seed", action="store_true", help="Create mock data if APIs fail")
    parser.add_argument("--dry-run", action="store_true", help="Validate configuration without processing")
    args = parser.parse_args()
    
    try:
        # Load catalog
        catalog = load_catalog()
        
        if args.dry_run:
            logger.info("Dry run mode - validating configuration only")
            for indicator in catalog["indicators"]:
                logger.info(f"Would process: {indicator['id']} -> {indicator['out_dir']}")
            return
        
        # Process each indicator
        results = []
        for indicator in catalog["indicators"]:
            result = process_indicator(indicator)
            results.append(result)
        
        # Create global index
        create_index(catalog["indicators"])
        
        # Summary
        successful = [r for r in results if r["status"] == "success"]
        failed = [r for r in results if r["status"] == "error"]
        skipped = [r for r in results if r["status"] == "skipped"]
        
        logger.info(f"Pipeline completed: {len(successful)} successful, {len(failed)} failed, {len(skipped)} skipped")
        
        if failed:
            logger.warning("Failed indicators:")
            for result in failed:
                logger.warning(f"  {result['id']}: {result['error']}")
        
        # If all failed and seed mode is enabled, create mock data
        if not successful and args.seed:
            logger.info("All indicators failed, creating mock data")
            create_mock_data()
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
