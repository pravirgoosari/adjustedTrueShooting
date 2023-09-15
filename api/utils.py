import time
import random
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retry():
    """Create a requests session with retry logic and realistic headers"""
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    
    return session

def safe_delay():
    """Add a random delay to avoid rate limiting"""
    delay = random.uniform(2, 5)  # 2-5 second delay
    time.sleep(delay)

def create_error_dataframe(season_end_year, error_message="Data Unavailable"):
    """Create a placeholder DataFrame when data fetching fails"""
    return {
        'Player': [error_message],
        'Team': ['N/A'],
        'Season': [f"{season_end_year-1}-{str(season_end_year)[2:]}"],
        'PPG': [0],
        'aTS%': [0],
        'TS%': [0],
        'DIFF': [0],
        'Usage Rate': [0],
        'Team 3PT%': [0],
        'Team 3PA': [0]
    }
