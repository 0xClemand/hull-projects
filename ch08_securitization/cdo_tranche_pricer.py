"""Chapter 8: Securitization and the Financial Crisis of 2007–8 - CDO tranche pricer with Gaussian copula simulation"""

import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
from fredapi import Fred
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


FRED_API_KEY = os.environ.get("FRED_API_KEY")

N_CREDITS = 100
RECOVERY_RATE = 0.40
CORRELATION = 0.20
MATURITY = 5
N_SIMULATIONS = 50_000

TRANCHES = [
    {"name": "Equity",     "attach": 0.00, "detach": 0.05},
    {"name": "Mezzanine",  "attach": 0.05, "detach": 0.20},
    {"name": "Senior",     "attach": 0.20, "detach": 1.00},
]

CREDIT_SPREAD_SERIES = "BAMLC0A4CBBB"


def fetch_default_probability(maturity=MATURITY):
    fred = Fred(api_key=FRED_API_KEY)
    spread_bps = fred.get_series(CREDIT_SPREAD_SERIES).dropna().iloc[-1]
    spread = spread_bps / 100

    pd_annual = spread / (1 - RECOVERY_RATE)
    pd_cumulative = 1 - (1 - pd_annual) ** maturity

    print(f"Credit spread (BBB):  {spread * 100:.2f}%")
    print(f"Implied annual PD:    {pd_annual * 100:.2f}%")
    print(f"Cumulative PD ({maturity}Y):   {pd_cumulative * 100:.2f}%")

    return pd_cumulative


def simulate_portfolio_losses(pd_cumulative):
    M = np.random.standard_normal(N_SIMULATIONS)
    Z = np.random.standard_normal((N_SIMULATIONS, N_CREDITS))
    X = np.sqrt(CORRELATION) * M[:, None] + np.sqrt(1 - CORRELATION) * Z

    threshold = norm.ppf(pd_cumulative)
    defaults = X < threshold
    n_defaults = defaults.sum(axis=1)
    losses = n_defaults * (1 - RECOVERY_RATE) / N_CREDITS

    print(f"\nSimulation ({N_SIMULATIONS:,} scenarios):")
    print(f"Mean portfolio loss:  {losses.mean() * 100:.2f}%")
    print(f"Max portfolio loss:   {losses.max() * 100:.2f}%")
    print(f"P(any default):       {(n_defaults > 0).mean() * 100:.1f}%")

    return losses


def allocate_tranche_losses(losses):
    print("\nTranche expected losses:")
    results = []
    for tranche in TRANCHES:
        width = tranche["detach"] - tranche["attach"]
        tranche_loss = np.clip(losses - tranche["attach"], 0, width) / width
        expected_loss = tranche_loss.mean()
        results.append({"name": tranche["name"], "expected_loss": expected_loss, "tranche_loss": tranche_loss})
        print(f"{tranche['name']:<14} {expected_loss * 100:.2f}%")
    return results


def compute_fair_spreads(tranche_results):
    print("\nFair spreads (annualized):")
    for result in tranche_results:
        spread_bps = result["expected_loss"] / MATURITY * 10_000
        result["fair_spread_bps"] = spread_bps
        print(f"{result['name']:<14} {spread_bps:.0f} bps")
    return tranche_results


def correlation_sensitivity(pd_cumulative):
    correlations = np.arange(0.0, 0.85, 0.05)
    sensitivity = {tranche["name"]: [] for tranche in TRANCHES}

    for rho in correlations:
        M = np.random.standard_normal(N_SIMULATIONS)
        Z = np.random.standard_normal((N_SIMULATIONS, N_CREDITS))
        X = np.sqrt(rho) * M[:, None] + np.sqrt(1 - rho) * Z

        threshold = norm.ppf(pd_cumulative)
        defaults = X < threshold
        losses = defaults.sum(axis=1) * (1 - RECOVERY_RATE) / N_CREDITS

        for tranche in TRANCHES:
            width = tranche["detach"] - tranche["attach"]
            tranche_loss = np.clip(losses - tranche["attach"], 0, width) / width
            sensitivity[tranche["name"]].append(tranche_loss.mean())

    return correlations, sensitivity


def plot_loss_distribution(losses, tranche_results):
    fig, ax = plt.subplots(figsize=(9, 5))

    loss_step = (1 - RECOVERY_RATE) / N_CREDITS * 100
    bins = np.arange(0, losses.max() * 100 + loss_step, loss_step)
    ax.hist(losses * 100, bins=bins, color="steelblue", edgecolor="white", linewidth=0.3)
    for result in tranche_results:
        tranche = next(t for t in TRANCHES if t["name"] == result["name"])
        ax.axvline(tranche["attach"] * 100, color="red", linestyle="--", linewidth=0.8)
    ax.set_xlabel("Portfolio loss (%)")
    ax.set_ylabel("Frequency")
    ax.set_title(f"Portfolio loss distribution (ρ = {CORRELATION})")

    plt.tight_layout()
    plt.savefig(os.path.join(SCRIPT_DIR, "loss_distribution.png"), dpi=150, bbox_inches="tight")
    plt.show()


def plot_correlation_sensitivity(correlations, sensitivity):
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = {"Equity": "#e74c3c", "Mezzanine": "#f39c12", "Senior": "#2ecc71"}

    for name, losses in sensitivity.items():
        ax.plot(correlations * 100, np.array(losses) * 100, marker="o", markersize=4, label=name, color=colors[name])

    ax.axvline(CORRELATION * 100, color="gray", linestyle="--", linewidth=0.8, label=f"Base ρ = {CORRELATION}")
    ax.set_xlabel("Correlation ρ (%)")
    ax.set_ylabel("Expected loss (%)")
    ax.set_title("Tranche expected loss vs. default correlation")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(SCRIPT_DIR, "correlation_sensitivity.png"), dpi=150, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    pd_cumulative = fetch_default_probability()
    losses = simulate_portfolio_losses(pd_cumulative)
    tranche_results = allocate_tranche_losses(losses)
    tranche_results = compute_fair_spreads(tranche_results)
    correlations, sensitivity = correlation_sensitivity(pd_cumulative)
    plot_loss_distribution(losses, tranche_results)
    plot_correlation_sensitivity(correlations, sensitivity)