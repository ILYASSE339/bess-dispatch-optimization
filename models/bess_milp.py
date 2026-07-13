"""
Optimal dispatch of a Battery Energy Storage System (BESS)
on the day-ahead spot market.

Formulation:
    max  Σ p_spot(t) · (d(t) - c(t))
    s.t. physical constraints on SoC, power, and simultaneity
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cvxpy as cp
import pandas as pd
import numpy as np
from models.Battery import BatteryModel


def solve_dispatch(
    prices: pd.Series,
    battery: BatteryModel,
    verbose: bool = False
) -> dict:
    """
    Solve the MILP dispatch problem for a single day.

    Parameters
    ----------
    prices   : pd.Series of spot prices (EUR/MWh), hourly, length T
    battery  : BatteryModel instance with physical specs
    verbose  : print solver output

    Returns
    -------
    dict with keys: status, profit, c, d, soc, prices
    """

    T = len(prices)
    p = prices.values  # shape (T,)

    # ── VARIABLES ────────────────────────────────────────
    c   = cp.Variable(T, nonneg=True, name="charge")       # MW
    d   = cp.Variable(T, nonneg=True, name="discharge")    # MW
    soc = cp.Variable(T + 1, nonneg=True, name="soc")      # MWh
    u_c = cp.Variable(T, boolean=True, name="u_charge")    # binary
    u_d = cp.Variable(T, boolean=True, name="u_discharge") # binary

    # ── OBJECTIVE ────────────────────────────────────────
    # Profit = revenue from discharge - cost of charge
    profit = cp.sum(cp.multiply(p, d - c))
    objective = cp.Maximize(profit)

    # ── CONSTRAINTS ──────────────────────────────────────
    constraints = []

    # Initial and final SoC
    constraints += [
        soc[0] == battery.soc_init,
        soc[T] >= battery.soc_min,   # don't end empty
    ]

    for t in range(T):
        # SoC evolution
        constraints += [
            soc[t + 1] == soc[t]
                        + battery.eta_c * c[t]
                        - d[t] / battery.eta_d
        ]

        # SoC bounds
        constraints += [
            soc[t + 1] >= battery.soc_min,
            soc[t + 1] <= battery.soc_max,
        ]

        # Power bounds linked to binary variables
        constraints += [
            c[t] <= battery.p_max * u_c[t],
            d[t] <= battery.p_max * u_d[t],
        ]

        # No simultaneous charge and discharge
        constraints += [
            u_c[t] + u_d[t] <= 1
        ]

    # ── SOLVE ────────────────────────────────────────────
    problem = cp.Problem(objective, constraints)
    problem.solve(solver=cp.GLPK_MI, verbose=verbose)

    if problem.status not in ["optimal", "optimal_inaccurate"]:
        return {"status": problem.status, "profit": None}

    return {
        "status":  problem.status,
        "profit":  float(problem.value),
        "c":       c.value,
        "d":       d.value,
        "soc":     soc.value,
        "prices":  p,
        "T":       T,
    }


if __name__ == "__main__":
    from data.loader import load_processed

    from utils.data_utils import load_day

    # Load data
    df = load_processed("data/processed/epex_fr_2024.csv")
    
    # Pick a day
    day = "2024-01-15"
    day_df = load_day(df, day)
    prices = day_df["price_eur_mwh"]

    # Battery specs
    battery = BatteryModel(
        e_max=2.0,        # MWh
        p_max=1.0,        # MW
        eta_c=0.95,
        eta_d=0.95,
        soc_min_pct=0.1,
        soc_init_pct=0.5,
    )

    # Solve
    result = solve_dispatch(prices, battery, verbose=False)

    if result["profit"] is not None:
        print(f"\nDay       : {day}")
        print(f"Status    : {result['status']}")
        print(f"Profit    : {result['profit']:.2f} EUR")
        print(f"\nHour | Price | Charge | Discharge | SoC")
        print("-" * 50)
        for t in range(result["T"]):
            print(
                f"  {t:02d} | {result['prices'][t]:6.1f} | "
                f"{result['c'][t]:6.3f} | "
                f"{result['d'][t]:9.3f} | "
                f"{result['soc'][t]:.3f}"
            )
    else:
        print(f"Solver failed: {result['status']}")