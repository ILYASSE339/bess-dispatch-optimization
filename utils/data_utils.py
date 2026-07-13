import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import date as date_type
import pandas as pd

def load_day(df: pd.DataFrame, day: str) -> pd.DataFrame:
    """
    Extract a single day from the loaded DataFrame.
    day format: 'YYYY-MM-DD'
    Returns DataFrame with 24 rows (hourly prices).
    """
    target = pd.Timestamp(day).date()
    mask = df["date"] == target
    day_df = df[mask].reset_index(drop=True)
    
    if len(day_df) == 0:
        raise ValueError(f"No data found for {day}")
    
    return day_df