"""Chapter 5: Determination of Forward and Futures Prices - implied carry calculator for stocks, commodities, and currencies"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ch04_interest_rates.yield_curve_bootstrap import fetch_treasury_yields, compute_zero_rates
import yfinance as yf
from datetime import date
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


ASSETS = [
    {"name": "S&P 500",   "type": "equity_index", "spot": "^GSPC",    "futures": ["ESM26.CME", "ESU26.CME", "ESZ26.CME", "ESH27.CME"]},
    {"name": "WTI Crude", "type": "commodity",    "spot": "CL=F",     "futures": ["CLM26.NYM", "CLU26.NYM", "CLZ26.NYM", "CLH27.NYM", "CLM27.NYM", "CLZ27.NYM"]},  # front-month used as spot proxy (standard for commodities)
    {"name": "EUR/USD",   "type": "currency",     "spot": "EURUSD=X", "futures": ["6EM26.CME", "6EU26.CME", "6EZ26.CME", "6EH27.CME"]},
]

MONTH_CODES = {
    "F": 1, "G": 2, "H": 3, "J": 4, "K": 5,  "M": 6,
    "N": 7, "Q": 8, "U": 9, "V": 10, "X": 11, "Z": 12,
}


def get_price(ticker):
    """Returns latest closing price as a float"""
    return float(yf.Ticker(ticker).history(period="5d")["Close"].iloc[-1])


def get_ttm(ticker):
    """Returns (T, expiry): time to maturity in years and the expiry date"""
    root = ticker.split(".")[0]
    year = 2000 + int(root[-2:])
    month = MONTH_CODES[root[-3]]
    expiry = date(year, month, 15)  # 15th of the expiry month as approximation
    T = (expiry - date.today()).days / 365.25
    return T, expiry


def implied_carry(S, F, r, T):
    """For all asset types: F = S * exp((r - carry) * T). We solve for carry"""
    return r - (np.log(F / S) / T)


def plot_results(asset_results):

    today = date.today()
    n = len(asset_results)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 5))
    if n == 1:
        axes = [axes]
    fig.suptitle("Implied Carry vs Futures Curve", fontsize=13, fontweight="bold")

    for ax, asset_data in zip(axes, asset_results):
        expiries  = [c["expiry"] for c in asset_data["contracts"]]
        f_prices  = [c["F"]      for c in asset_data["contracts"]]
        carries   = [c["carry"] * 100 for c in asset_data["contracts"]]
        r_vals    = [c["r"] * 100     for c in asset_data["contracts"]]

        x_today    = mdates.date2num(today)
        x_expiries = [mdates.date2num(e) for e in expiries]

        # Left y-axis: spot + futures price curve
        color_price = "steelblue"
        ax.plot([x_today] + x_expiries, [asset_data["S"]] + f_prices, "o-", color=color_price, zorder=3, label="Futures")
        ax.scatter([x_today], [asset_data["S"]], color="black", s=60, zorder=4, label="Spot")
        ax.set_ylabel("Price", color=color_price)
        ax.tick_params(axis="y", labelcolor=color_price)
        ax.xaxis_date()
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
        padding = 15  # days of padding beyond last expiry
        ax.set_xlim(x_today - padding, x_expiries[-1] + padding)
        ax.set_xticks([x_today] + x_expiries)

        # Right y-axis: implied carry bars + risk-free rate dashed line
        carry_labels = {
            "equity_index": "Dividend yield (q)",
            "commodity":    "Net convenience yield (y − u)",
            "currency":     "Foreign rate (r_f)",
        }
        carry_label = carry_labels.get(asset_data["type"], "Implied carry")
        ax2 = ax.twinx()
        bar_colors = ["seagreen" if c >= 0 else "tomato" for c in carries]
        ax2.bar(x_expiries, carries, color=bar_colors, alpha=0.55, width=25, label=carry_label)
        ax2.plot(x_expiries, r_vals, "--", color="gray", linewidth=1.5, label="r (risk-free rate)")
        ax2.axhline(0, color="black", linewidth=0.5)
        ax2.set_ylim(min(0, min(carries)), max(max(carries), max(r_vals)) * 1.4)
        ax2.set_ylabel("Implied carry (%)")
        handles1, labels1 = ax.get_legend_handles_labels()
        handles2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(handles1 + handles2, labels1 + labels2, loc="upper right", fontsize=8)

        ax.set_title(asset_data["name"], fontweight="bold")
        ax.set_xlabel("Expiry")

    fig.autofmt_xdate()
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "implied_carry.png"), dpi=150, bbox_inches="tight")
    plt.show()



if __name__ == "__main__":

    maturities, par_yields = fetch_treasury_yields()
    zero_rates = compute_zero_rates(maturities, par_yields)

    asset_results = []
    for asset in ASSETS:
        S = get_price(asset["spot"])
        print(f"\n{asset['name']} (spot = ${S:.4f})")
        contracts = []
        for futures_ticker in asset["futures"]:
            F = get_price(futures_ticker)
            T, expiry = get_ttm(futures_ticker)
            r = np.interp(T, maturities, zero_rates)
            carry = implied_carry(S, F, r, T)
            contracts.append({"ticker": futures_ticker, "F": F, "T": T, "expiry": expiry, "r": r, "carry": carry})
            print(f"  {expiry.strftime('%b %Y')} contract: {futures_ticker}  F = ${F:.4f}  T = {T:.2f}Y  r = {100 * r:.2f}%  carry = {100 * carry:.2f}%")
        asset_results.append({"name": asset["name"], "type": asset["type"], "S": S, "contracts": contracts})

    plot_results(asset_results)