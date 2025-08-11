"""
Base adapter with resilient network stack for data fetching.
Handles retries, TLS, timeouts, and structured error handling.
"""
import os
import logging
from typing import Optional
import requests
import certifi
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

logger = logging.getLogger(__name__)

def session() -> requests.Session:
    """
    Create a resilient requests session with:
    - Exponential backoff retries
    - TLS verification (configurable)
    - Proper timeouts
    """
    s = requests.Session()
    
    # Configure retries with exponential backoff
    retries = Retry(
        total=5,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    
    # Mount adapters for both HTTP and HTTPS
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.mount("http://", HTTPAdapter(max_retries=retries))
    
    # Configure TLS verification
    if os.getenv("INSECURE") == "1":
        logger.warning("TLS verification disabled - INSECURE=1")
        s.verify = False
    else:
        s.verify = certifi.where()
    
    # Set default timeout
    s.timeout = 30
    
    return s

def safe_request(
    url: str, 
    method: str = "GET", 
    **kwargs
) -> requests.Response:
    """
    Make a safe HTTP request with proper error handling.
    
    Args:
        url: Target URL
        method: HTTP method
        **kwargs: Additional arguments for requests
    
    Returns:
        Response object
        
    Raises:
        requests.RequestException: For network/HTTP errors
    """
    try:
        resp = session().request(method, url, **kwargs)
        resp.raise_for_status()
        logger.info(f"Successfully fetched {url} - {resp.status_code}")
        return resp
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        raise

class AdapterError(Exception):
    """Base exception for adapter errors."""
    pass

class DataFetchError(AdapterError):
    """Raised when data fetching fails."""
    pass

class DataParseError(AdapterError):
    """Raised when data parsing fails."""
    pass
