"""
Backtest — Rolling day-by-day dispatch
=======================================
Solves one MILP per day over the full price history.
SoC at end of day t becomes initial SoC of day t+1.
Outputs a P&L DataFrame and summary statistics.
"""

import pandas as pd
import numpy as np
from data.loader import load_day_ahead_prices
from data.loader import load_processed
from models.Battery import BatteryModel
from models.bess_milp import solve_dispatch


def run_backtest(
    df: pd.DataFrame,
    battery: BatteryModel,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Run rolling day-by-day MILP dispatch over full DataFrame.

    Parameters
    ----------
    df      : full price DataFrame from loader
    battery : BatteryModel instance
    verbose : print progress

    Returns
    -------
    DataFrame with one row per day : date, profit, soc_start, soc_end, status
    """

    results = []
    days = sorted(df["date"].unique())
    soc_carry = battery.soc_init  # carries across days

    for i, day in enumerate(days):
        day_df = df[df["date"] == day].reset_index(drop=True)
        prices = day_df["price_eur_mwh"]

        # Skip incomplete days
        if len(prices) < 24:
            if verbose:
                print(f"  [{i+1}/{len(days)}] {day} — skipped ({len(prices)} hours)")
            continue

        # Carry SoC from previous day
        battery.soc_init_pct = soc_carry / battery.e_max

        # Solve
        result = solve_dispatch(prices, battery, verbose=False)

        if result["profit"] is not None:
            soc_end = float(result["soc"][-1])

            # Update aging
            battery.update_aging(result["c"])

            results.append({
                "date":       str(day),
                "profit_eur": round(result["profit"], 2),
                "soc_start":  round(soc_carry, 4),
                "soc_end":    round(soc_end, 4),
                "capacity":   round(battery.e_max, 4),
                "status":     result["status"],
            })

            soc_carry = soc_end

            if verbose:
                print(f"  [{i+1}/{len(days)}] {day} — profit: {result['profit']:7.2f} EUR  |  SoC: {soc_carry:.3f} MWh  |  cap: {battery.e_max:.4f} MWh")
        else:
            if verbose:
                print(f"  [{i+1}/{len(days)}] {day} — FAILED ({result['status']})")
            results.append({
                "date":       str(day),
                "profit_eur": None,
                "soc_start":  round(soc_carry, 4),
                "soc_end":    None,
                "capacity":   round(battery.e_max, 4),
                "status":     result["status"],
            })

    return pd.DataFrame(results)


def print_summary(bt: pd.DataFrame) -> None:
    """Print backtest summary statistics."""
    valid = bt.dropna(subset=["profit_eur"])
    total  = valid["profit_eur"].sum()
    mean   = valid["profit_eur"].mean()
    best   = valid.loc[valid["profit_eur"].idxmax()]
    worst  = valid.loc[valid["profit_eur"].idxmin()]
    pos    = (valid["profit_eur"] > 0).sum()
    neg    = (valid["profit_eur"] <= 0).sum()

    print("\n═══════════════════════════════════════")
    print("  BACKTEST SUMMARY")
    print("═══════════════════════════════════════")
    print(f"  Days solved       : {len(valid)} / {len(bt)}")
    print(f"  Total profit      : {total:,.2f} EUR")
    print(f"  Mean daily profit : {mean:.2f} EUR")
    print(f"  Best day          : {best['date']}  →  {best['profit_eur']:.2f} EUR")
    print(f"  Worst day         : {worst['date']}  →  {worst['profit_eur']:.2f} EUR")
    print(f"  Profitable days   : {pos}")
    print(f"  Loss days         : {neg}")
    print(f"  Final capacity    : {bt['capacity'].iloc[-1]:.4f} MWh")
    print("═══════════════════════════════════════\n")


if __name__ == "__main__":
    # Load data
    print("Loading prices...")
    df = load_processed("data/processed/epex_fr_2024.csv")
    print(f"  {len(df)} rows — {df['date'].nunique()} days\n")

    # Battery
    battery = BatteryModel(
        e_max=2.0,
        p_max=1.0,
        eta_c=0.95,
        eta_d=0.95,
        soc_min_pct=0.1,
        soc_init_pct=0.5,
    )

    # Run
    print("Running backtest...")
    bt = run_backtest(df, battery, verbose=True)

    # Summary
    print_summary(bt)

    # Save
    bt.to_csv("data/processed/backtest_results.csv", index=False)
    print("Saved → data/processed/backtest_results.csv")