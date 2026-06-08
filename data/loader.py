# Imports

import pandas as pd

# Functions

def load_day_ahead_prices(filepath: str) -> pd.DataFrame:
    """
    Load Energy Charts day-ahead price CSV for France.
    Skips the license header and metadata rows.
    Returns a clean DataFrame with timestamp and price columns.
    """
    df = pd.read_csv(
        filepath,
        skiprows=3,          # skip license text + empty row + unit row
        names=["timestamp", "price_eur_mwh"],
        parse_dates=["timestamp"]
    )

    # Drop any rows where price is missing
    df = df.dropna(subset=["price_eur_mwh"])

    # Ensure price is numeric
    df["price_eur_mwh"] = pd.to_numeric(df["price_eur_mwh"], errors="coerce")

    # Sort by time
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert("Europe/Paris")
    df["date"] = df["timestamp"].dt.date
    df["time"] = df["timestamp"].dt.time
    df = df[["timestamp","date", "time", "price_eur_mwh"]]
    return df


if __name__ == "__main__":
    filepath = "data/raw/energy-charts_Electricity_production_and_spot_prices_in_France_in_2024.csv"
    df = load_day_ahead_prices(filepath)

    print(f"Rows loaded      : {len(df)}")
    print(f"Period           : {df.timestamp.min()} → {df.timestamp.max()}")
    print(f"Price min        : {df.price_eur_mwh.min():.2f} EUR/MWh")
    print(f"Price max        : {df.price_eur_mwh.max():.2f} EUR/MWh")
    print(f"Price mean       : {df.price_eur_mwh.mean():.2f} EUR/MWh")
    print(f"Negative prices  : {(df.price_eur_mwh < 0).sum()} hours")
    print(f"\nFirst 5 rows :")
    print(df.head())

    df.to_csv("data/processed/epex_fr_2024.csv", index=False)
    print("Saved → data/processed/epex_fr_2024.csv")


