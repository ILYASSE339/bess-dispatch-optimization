import numpy as np


class BatteryModel:
    """
    Physical model of a BESS.
    Encapsulates capacity, efficiency, SoC bounds and evolution.
    Aging reduces capacity over full equivalent cycles.
    """

    def __init__(
        self,
        e_max: float = 2.0,       # MWh — nominal capacity
        p_max: float = 1.0,       # MW  — max charge/discharge power
        soc_min_pct: float = 0.1, # minimum SoC as fraction of capacity
        soc_init_pct: float = 0.5,# initial SoC as fraction of capacity
        eta_c: float = 0.95,      # charge efficiency
        eta_d: float = 0.95,      # discharge efficiency
        cycle_life: int = 4000,   # full cycles before end of life
    ):
        self.e_max_nominal = e_max
        self.e_max = e_max        # current capacity — degrades with aging
        self.p_max = p_max
        self.soc_min_pct = soc_min_pct
        self.soc_init_pct = soc_init_pct
        self.eta_c = eta_c
        self.eta_d = eta_d
        self.cycle_life = cycle_life
        self.cycles_done = 0.0    # cumulative full equivalent cycles

    # ── SOC BOUNDS ─────────────────────────────────────────

    @property
    def soc_min(self) -> float:
        """Minimum SoC in MWh — absolute value from percentage."""
        return self.soc_min_pct * self.e_max

    @property
    def soc_max(self) -> float:
        """Maximum SoC in MWh — current capacity after aging."""
        return self.e_max

    @property
    def soc_init(self) -> float:
        """Initial SoC in MWh."""
        return self.soc_init_pct * self.e_max

    # ── SOC EVOLUTION ──────────────────────────────────────

    def soc_next(self, soc: float, c: float, d: float, dt: float = 1.0) -> float:
        """
        Compute next SoC given current state and charge/discharge actions.

        Parameters
        ----------
        soc : current state of charge in MWh
        c   : charge power in MW
        d   : discharge power in MW
        dt  : time step in hours

        Returns
        -------
        next SoC in MWh
        """
        return soc + self.eta_c * c * dt - (d / self.eta_d) * dt

    def validate_action(self, c: float, d: float) -> None:
        """
        Raise error if charge or discharge exceeds p_max.
        Used for simulation validation — not inside the optimizer.
        """
        if c * np.sqrt(self.eta_c * self.eta_d) > self.p_max:
            raise ValueError(f"Charge power {c:.2f} exceeds P_max {self.p_max}")
        if d / np.sqrt(self.eta_c * self.eta_d) > self.p_max:
            raise ValueError(f"Discharge power {d:.2f} exceeds P_max {self.p_max}")

    # ── AGING ──────────────────────────────────────────────

    def update_aging(self, c_profile: np.ndarray, dt: float = 1.0) -> None:
        """
        Update capacity after a dispatch period based on energy throughput.
        One full equivalent cycle = charging e_max MWh once.

        Parameters
        ----------
        c_profile : array of charge power values over the period (MW)
        dt        : time step in hours
        """
        energy_charged = np.sum(c_profile) * dt          # MWh charged
        full_equiv_cycles = energy_charged / self.e_max   # fraction of full cycle
        self.cycles_done += full_equiv_cycles

        # Linear degradation model : capacity drops to 80% at end of life
        degradation = 1.0 - 0.2 * (self.cycles_done / self.cycle_life)
        self.e_max = max(self.e_max_nominal * degradation, 0.0)

    # ── SUMMARY ────────────────────────────────────────────

    def summary(self) -> dict:
        """Return current battery state as a dict."""
        return {
            "e_max_nominal_MWh": self.e_max_nominal,
            "e_max_current_MWh": round(self.e_max, 4),
            "p_max_MW":          self.p_max,
            "soc_min_MWh":       round(self.soc_min, 4),
            "soc_max_MWh":       round(self.soc_max, 4),
            "soc_init_MWh":      round(self.soc_init, 4),
            "eta_c":             self.eta_c,
            "eta_d":             self.eta_d,
            "RTE":               round(self.eta_c * self.eta_d, 4),
            "cycles_done":       round(self.cycles_done, 2),
            "capacity_pct":      round(self.e_max / self.e_max_nominal * 100, 1),
        }


if __name__ == "__main__":
    battery = BatteryModel(e_max=2.0, p_max=1.0)

    print("── Initial battery state ──")
    for k, v in battery.summary().items():
        print(f"  {k:<25} : {v}")

    print(f"\n── SoC evolution test ──")
    soc = battery.soc_init
    print(f"  t=0  SoC={soc:.3f} MWh")
    soc = battery.soc_next(soc, c=1.0, d=0.0)
    print(f"  t=1  SoC={soc:.3f} MWh  (charged 1 MW for 1h)")
    soc = battery.soc_next(soc, c=0.0, d=1.0)
    print(f"  t=2  SoC={soc:.3f} MWh  (discharged 1 MW for 1h)")

    print(f"\n── Aging test ──")
    fake_charge = np.ones(24) * 0.5
    battery.update_aging(fake_charge)
    print(f"  After 1 day heavy cycling :")
    print(f"  cycles done : {battery.cycles_done:.3f}")
    print(f"  capacity    : {battery.e_max:.4f} MWh ({battery.e_max/battery.e_max_nominal*100:.2f}%)")    