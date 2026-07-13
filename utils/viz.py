"""
Visualisations — Backtest & Dispatch
=====================================
Strategic KPI visualisations for the flexible asset optimisation project.
All plots exported as interactive HTML (plotly).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os

# ── STYLE ─────────────────────────────────────────────────────
COLORS = {
    "profit":    "#00D4A8",
    "loss":      "#FF5C57",
    "price":     "#7C6FFF",
    "soc":       "#F5C842",
    "capacity":  "#FF8C69",
    "charge":    "#7EDDB0",
    "discharge": "#B8A9FF",
    "neutral":   "#7A7888",
}

LAYOUT = dict(
    paper_bgcolor="#0C0C10",
    plot_bgcolor="#13131A",
    font=dict(family="JetBrains Mono, monospace", color="#A8A6BC", size=11),
    title_font=dict(family="Bebas Neue, sans-serif", color="#F0EDE6", size=22),
    margin=dict(l=60, r=40, t=60, b=60),
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", zeroline=False),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", zeroline=False),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(255,255,255,0.1)"),
)

OUTPUT_DIR = "viz/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _save(fig: go.Figure, name: str) -> str:
    path = f"{OUTPUT_DIR}/{name}.html"
    fig.write_html(path)
    print(f"  Saved → {path}")
    return path


# ── 1. PROFIT CUMULATIF ───────────────────────────────────────
def plot_cumulative_profit(bt: pd.DataFrame) -> str:
    """Cumulative P&L over the backtest period."""
    valid = bt.dropna(subset=["profit_eur"]).copy()
    valid["cumulative"] = valid["profit_eur"].cumsum()

    fig = go.Figure()

    # Area under curve
    fig.add_trace(go.Scatter(
        x=valid["date"],
        y=valid["cumulative"],
        fill="tozeroy",
        fillcolor="rgba(0,212,168,0.1)",
        line=dict(color=COLORS["profit"], width=2),
        name="P&L cumulatif",
        hovertemplate="<b>%{x}</b><br>P&L cumulatif : %{y:.2f} EUR<extra></extra>",
    ))

    # Zero line
    fig.add_hline(y=0, line_color="rgba(255,255,255,0.15)", line_dash="dash")

    fig.update_layout(
        **LAYOUT,
        title="P&L Cumulatif — Arbitrage Spot BESS",
        xaxis_title="Date",
        yaxis_title="EUR",
    )
    return _save(fig, "01_cumulative_profit")


# ── 2. PROFIT PAR JOUR ────────────────────────────────────────
def plot_daily_profit(bt: pd.DataFrame) -> str:
    """Daily profit — green positive, red negative."""
    valid = bt.dropna(subset=["profit_eur"]).copy()
    colors = [COLORS["profit"] if p > 0 else COLORS["loss"] for p in valid["profit_eur"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=valid["date"],
        y=valid["profit_eur"],
        marker_color=colors,
        name="Profit journalier",
        hovertemplate="<b>%{x}</b><br>Profit : %{y:.2f} EUR<extra></extra>",
    ))

    fig.add_hline(y=0, line_color="rgba(255,255,255,0.2)")

    # Annotate best day
    best_idx = valid["profit_eur"].idxmax()
    best = valid.loc[best_idx]
    fig.add_annotation(
        x=best["date"], y=best["profit_eur"],
        text=f"Best : {best['profit_eur']:.0f} EUR",
        showarrow=True, arrowhead=2,
        font=dict(color=COLORS["profit"]),
        arrowcolor=COLORS["profit"],
    )

    fig.update_layout(
        **LAYOUT,
        title="Profit Journalier",
        xaxis_title="Date",
        yaxis_title="EUR / jour",
        bargap=0.1,
    )
    return _save(fig, "02_daily_profit")


# ── 3. DISTRIBUTION DES PROFITS ───────────────────────────────
def plot_profit_distribution(bt: pd.DataFrame) -> str:
    """Histogram of daily profits."""
    valid = bt.dropna(subset=["profit_eur"])

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=valid["profit_eur"],
        nbinsx=40,
        marker_color=COLORS["profit"],
        marker_line=dict(color="rgba(0,0,0,0.3)", width=0.5),
        opacity=0.85,
        name="Distribution",
        hovertemplate="Profit : %{x:.1f} EUR<br>Jours : %{y}<extra></extra>",
    ))

    # Mean line
    mean = valid["profit_eur"].mean()
    fig.add_vline(
        x=mean,
        line_color=COLORS["soc"],
        line_dash="dash",
        annotation_text=f"Moyenne : {mean:.1f} EUR",
        annotation_font_color=COLORS["soc"],
    )

    fig.add_vline(x=0, line_color=COLORS["loss"], line_dash="dot")

    fig.update_layout(
        **LAYOUT,
        title="Distribution des Profits Journaliers",
        xaxis_title="Profit (EUR)",
        yaxis_title="Nombre de jours",
    )
    return _save(fig, "03_profit_distribution")


# ── 4. DÉGRADATION CAPACITÉ ───────────────────────────────────
def plot_capacity_degradation(bt: pd.DataFrame) -> str:
    """Battery capacity degradation over time."""
    valid = bt.dropna(subset=["capacity"]).copy()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=valid["date"],
        y=valid["capacity"],
        mode="lines",
        line=dict(color=COLORS["capacity"], width=2),
        fill="tozeroy",
        fillcolor="rgba(255,140,105,0.08)",
        name="Capacité actuelle",
        hovertemplate="<b>%{x}</b><br>Capacité : %{y:.4f} MWh<extra></extra>",
    ))

    # Nominal capacity reference
    nominal = valid["capacity"].iloc[0]
    fig.add_hline(
        y=nominal,
        line_color="rgba(255,255,255,0.15)",
        line_dash="dash",
        annotation_text=f"Nominal : {nominal:.2f} MWh",
        annotation_font_color="rgba(255,255,255,0.4)",
    )

    # 80% threshold (end of life)
    eol = nominal * 0.8
    fig.add_hline(
        y=eol,
        line_color=COLORS["loss"],
        line_dash="dash",
        annotation_text="Fin de vie (80%)",
        annotation_font_color=COLORS["loss"],
    )

    fig.update_layout(
        **LAYOUT,
        title="Dégradation de la Capacité — Aging BESS",
        xaxis_title="Date",
        yaxis_title="Capacité (MWh)",
    )
    return _save(fig, "04_capacity_degradation")


# ── 5. SOC START vs END ───────────────────────────────────────
def plot_soc_evolution(bt: pd.DataFrame) -> str:
    """SoC start and end for each day."""
    valid = bt.dropna(subset=["soc_start", "soc_end"]).copy()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=valid["date"],
        y=valid["soc_start"],
        mode="lines",
        line=dict(color=COLORS["charge"], width=1.5),
        name="SoC début de journée",
        hovertemplate="<b>%{x}</b><br>SoC début : %{y:.3f} MWh<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=valid["date"],
        y=valid["soc_end"],
        mode="lines",
        line=dict(color=COLORS["discharge"], width=1.5),
        name="SoC fin de journée",
        hovertemplate="<b>%{x}</b><br>SoC fin : %{y:.3f} MWh<extra></extra>",
    ))

    fig.update_layout(
        **LAYOUT,
        title="Évolution du SoC — Début vs Fin de Journée",
        xaxis_title="Date",
        yaxis_title="SoC (MWh)",
    )
    return _save(fig, "05_soc_evolution")


# ── 6. PRIX SPOT + JOURS PROFITABLES ──────────────────────────
def plot_prices_vs_profit(
    df_prices: pd.DataFrame,
    bt: pd.DataFrame
) -> str:
    """Daily mean price with profitable days highlighted."""
    daily_price = df_prices.groupby("date")["price_eur_mwh"].mean().reset_index()
    daily_price["date"] = daily_price["date"].astype(str)

    valid = bt.dropna(subset=["profit_eur"]).copy()
    valid["date"] = valid["date"].astype(str)
    merged = daily_price.merge(valid[["date", "profit_eur"]], on="date", how="left")

    colors = [
        COLORS["profit"] if (p is not None and p > 0) else
        COLORS["loss"]   if (p is not None and p <= 0) else
        COLORS["neutral"]
        for p in merged["profit_eur"]
    ]

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.6, 0.4],
        vertical_spacing=0.06,
    )

    # Top : mean daily price
    fig.add_trace(go.Scatter(
        x=merged["date"],
        y=merged["price_eur_mwh"],
        mode="lines",
        line=dict(color=COLORS["price"], width=1.5),
        name="Prix moyen journalier",
        hovertemplate="<b>%{x}</b><br>Prix moyen : %{y:.1f} EUR/MWh<extra></extra>",
    ), row=1, col=1)

    # Bottom : daily profit bars
    fig.add_trace(go.Bar(
        x=merged["date"],
        y=merged["profit_eur"],
        marker_color=colors,
        name="Profit journalier",
        hovertemplate="<b>%{x}</b><br>Profit : %{y:.2f} EUR<extra></extra>",
    ), row=2, col=1)

    fig.update_layout(
        **LAYOUT,
        title="Prix Spot vs Profit Journalier",
        height=520,
    )
    fig.update_yaxes(title_text="EUR/MWh", row=1, col=1,
                     gridcolor="rgba(255,255,255,0.05)")
    fig.update_yaxes(title_text="EUR", row=2, col=1,
                     gridcolor="rgba(255,255,255,0.05)")

    return _save(fig, "06_prices_vs_profit")


# ── 7. DISPATCH JOURNALIER ────────────────────────────────────
def plot_daily_dispatch(
    result: dict,
    day: str,
) -> str:
    """
    Charge / discharge / SoC profile for a single day.

    Parameters
    ----------
    result : output of solve_dispatch()
    day    : date string for title
    """
    T = result["T"]
    hours = list(range(T))

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.55, 0.45],
        vertical_spacing=0.06,
        subplot_titles=["Prix spot & Dispatch", "État de charge (SoC)"],
    )

    # ── Row 1 : prices + charge/discharge ──
    fig.add_trace(go.Scatter(
        x=hours, y=result["prices"],
        mode="lines",
        line=dict(color=COLORS["price"], width=2),
        name="Prix spot (EUR/MWh)",
        hovertemplate="h%{x} — Prix : %{y:.1f} EUR/MWh<extra></extra>",
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=hours, y=result["c"],
        marker_color=COLORS["charge"],
        name="Charge (MW)",
        opacity=0.8,
        hovertemplate="h%{x} — Charge : %{y:.3f} MW<extra></extra>",
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=hours, y=[-d for d in result["d"]],
        marker_color=COLORS["discharge"],
        name="Décharge (MW)",
        opacity=0.8,
        hovertemplate="h%{x} — Décharge : %{y:.3f} MW<extra></extra>",
    ), row=1, col=1)

    # ── Row 2 : SoC ──
    fig.add_trace(go.Scatter(
        x=list(range(T + 1)),
        y=result["soc"],
        mode="lines+markers",
        line=dict(color=COLORS["soc"], width=2),
        marker=dict(size=4),
        fill="tozeroy",
        fillcolor="rgba(245,200,66,0.08)",
        name="SoC (MWh)",
        hovertemplate="h%{x} — SoC : %{y:.3f} MWh<extra></extra>",
    ), row=2, col=1)

    fig.update_layout(
        **LAYOUT,
        title=f"Dispatch BESS — {day}",
        height=520,
        barmode="overlay",
    )
    fig.update_yaxes(title_text="EUR/MWh  |  MW", row=1, col=1,
                     gridcolor="rgba(255,255,255,0.05)")
    fig.update_yaxes(title_text="MWh", row=2, col=1,
                     gridcolor="rgba(255,255,255,0.05)")
    fig.update_xaxes(title_text="Heure", row=2, col=1)

    return _save(fig, f"07_dispatch_{day}")


# ── 8. DASHBOARD COMPLET ──────────────────────────────────────
def plot_dashboard(bt: pd.DataFrame) -> str:
    """4-panel summary dashboard."""
    valid = bt.dropna(subset=["profit_eur"]).copy()
    valid["cumulative"] = valid["profit_eur"].cumsum()

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "P&L Cumulatif",
            "Profit Journalier",
            "Distribution des Profits",
            "Dégradation Capacité",
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.08,
    )

    # P&L cumulatif
    fig.add_trace(go.Scatter(
        x=valid["date"], y=valid["cumulative"],
        fill="tozeroy", fillcolor="rgba(0,212,168,0.1)",
        line=dict(color=COLORS["profit"], width=2), name="P&L cumulatif",
        showlegend=False,
    ), row=1, col=1)

    # Daily profit
    colors = [COLORS["profit"] if p > 0 else COLORS["loss"] for p in valid["profit_eur"]]
    fig.add_trace(go.Bar(
        x=valid["date"], y=valid["profit_eur"],
        marker_color=colors, name="Profit/jour",
        showlegend=False,
    ), row=1, col=2)

    # Distribution
    fig.add_trace(go.Histogram(
        x=valid["profit_eur"], nbinsx=30,
        marker_color=COLORS["profit"], opacity=0.8,
        showlegend=False,
    ), row=2, col=1)

    # Capacity
    fig.add_trace(go.Scatter(
        x=valid["date"], y=valid["capacity"],
        line=dict(color=COLORS["capacity"], width=2),
        fill="tozeroy", fillcolor="rgba(255,140,105,0.08)",
        showlegend=False,
    ), row=2, col=2)

    fig.update_layout(
        **LAYOUT,
        title="Dashboard — Flexible Asset Optimisation",
        height=600,
    )
    for i in range(1, 3):
        for j in range(1, 3):
            fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)", row=i, col=j)
            fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)", row=i, col=j)

    return _save(fig, "00_dashboard")


# ── MAIN ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Loading backtest results...")
    bt = pd.read_csv("data/processed/backtest_results.csv")

    print("Generating plots...\n")
    plot_cumulative_profit(bt)
    plot_daily_profit(bt)
    plot_profit_distribution(bt)
    plot_capacity_degradation(bt)
    plot_soc_evolution(bt)
    plot_dashboard(bt)

    # Prix vs profit
    from data.loader import load_processed
    df_prices = load_processed("data/processed/epex_fr_2024.csv")
    plot_prices_vs_profit(df_prices, bt)

    print("\nDone. Open viz/output/ to view the HTML files.")