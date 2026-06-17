## Data source

Day-ahead auction prices for France 2024 from
[Energy Charts](https://energy-charts.info) — FR bidding zone, hourly resolution.

> Raw data is not pushed to GitHub. Run `python data/loader.py` to generate
> the processed file from your local raw CSV.

## Install

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

**1. Load and clean price data**
```bash
python data/loader.py
# → generates data/processed/epex_fr_2024.csv
```

**2. Test a battery profile**
```bash
# Default profile (small)
python models/battery.py

# Specific profile
python models/battery.py --profile small
python models/battery.py --profile medium
python models/battery.py --profile large
```

## Battery profiles

Defined in `config.yaml` — three reference profiles :

| Profile | Capacity | Power | RTE   | Cycle life |
|---------|----------|-------|-------|------------|
| small   | 2 MWh    | 1 MW  | 90.2% | 4000       |
| medium  | 4 MWh    | 2 MW  | 90.2% | 4000       |
| large   | 10 MWh   | 5 MW  | 84.6% | 3500       |

## Roadmap

- [x] Project structure and data pipeline
- [x] BatteryModel — physical model with SoC evolution and aging
- [ ] BESS MILP optimizer — deterministic dispatch
- [ ] Backtest on 2024 data — P&L simulation
- [ ] Stochastic layer — Monte Carlo price scenarios
- [ ] Performance analysis and visualization

## Status

🔧 In progress — Week 2 · BatteryModel complete