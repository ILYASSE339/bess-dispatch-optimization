def load_day(df: pd.DataFrame, day: str) -> pd.DataFrame:
    """
    Extract a single day from the loaded DataFrame.
    day format: 'YYYY-MM-DD'
    Returns DataFrame with 24 rows (hourly prices).
    """
    mask = df["date"] == pd.Timestamp(day).date()
    day_df = df[mask].reset_index(drop=True)
    
    if len(day_df) == 0:
        raise ValueError(f"No data found for {day}")
    
    return day_df