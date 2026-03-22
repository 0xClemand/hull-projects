"""Chapter 7: Swaps - cross-currency swap pricer with mark-to-market and sensitivity analysis"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ch04_interest_rates.yield_curve_bootstrap import fetch_treasury_yields, compute_zero_rates
from ch05_forward_futures_pricing.implied_carry_calculator import get_price, get_ttm
from scipy.interpolate import CubicSpline
from scipy.optimize import brentq
import numpy as np
import matplotlib.pyplot as plt

# Tickers for the foreign currency: change these to price a different currency swap.
# spot_ticker: Yahoo Finance spot FX ticker (e.g. "EURUSD=X", "GBPUSD=X")
# futures_tickers: list of CME FX futures tickers in expiry order, max ~2Y out

FOREIGN_SPOT_TICKER = "EURUSD=X"
FOREIGN_FUTURES_TICKERS = [
    "6EM26.CME",  # Jun 2026
    "6EU26.CME",  # Sep 2026
    "6EZ26.CME",  # Dec 2026
    "6EH27.CME",  # Mar 2027
    "6EM27.CME",  # Jun 2027
    "6EU27.CME",  # Sep 2027
    "6EZ27.CME",  # Dec 2027
]

DOMESTIC_NOTIONAL = 100_000
FOREIGN_NOTIONAL = None        # set one, leave the other as None
MATURITY = 2
FREQUENCY = 4
DOMESTIC_RATE = 0.04
DOMESTIC_LEG_TYPE = "fixed"
FOREIGN_RATE = None            # None = solve for fair rate
FOREIGN_LEG_TYPE = "fixed"
SOLVE_FOR = "foreign"


class ZeroCurve:
    def __init__(self, maturities, zero_rates):
        self.maturities = maturities
        self.zero_rates = zero_rates
        self._spline = CubicSpline(maturities, zero_rates)

    def discount(self, T):
        return np.exp(-self._spline(T) * T)

    def forward_rate(self, t1, t2):
        r1 = self._spline(t1)
        r2 = self._spline(t2)
        return (r2 * t2 - r1 * t1) / (t2 - t1)

    def shift(self, bps):
        return ZeroCurve(self.maturities, self.zero_rates + bps / 10_000)


class SwapLeg:
    def __init__(self, notional, leg_type, frequency, maturity, curve, rate=None):
        self.notional = notional
        self.leg_type = leg_type
        self.rate = rate
        self.frequency = frequency
        self.maturity = maturity
        self.curve = curve

    def payment_dates(self):
        return np.arange(1, self.maturity * self.frequency + 1) / self.frequency
    
    def pv(self):
        payment_dates = self.payment_dates() 
        pv = 0

        if self.leg_type == "fixed":
            for cf_date in payment_dates:
                cf = self.notional * self.rate / self.frequency
                pv += cf * self.curve.discount(cf_date)
            pv += self.notional * self.curve.discount(payment_dates[-1])
            return pv
        
        elif self.leg_type == "floating":
            t_prev = 0
            for t_curr in payment_dates:
                rate = self.curve.forward_rate(t_prev, t_curr)
                cf = self.notional * rate * (t_curr - t_prev)
                pv += cf * self.curve.discount(t_curr)
                t_prev = t_curr
            pv += self.notional * self.curve.discount(payment_dates[-1])
            return pv
        else:
            raise ValueError(f"Unknown leg type: {self.leg_type}")


    def cashflow_pvs(self):
        """Returns (payment_dates, coupon_pvs, principal_pv) for plotting."""
        dates = self.payment_dates()
        coupon_pvs = []

        if self.leg_type == "fixed":
            for t in dates:
                coupon_pvs.append(self.notional * self.rate / self.frequency * self.curve.discount(t))
        elif self.leg_type == "floating":
            t_prev = 0
            for t_curr in dates:
                rate = self.curve.forward_rate(t_prev, t_curr)
                coupon_pvs.append(self.notional * rate * (t_curr - t_prev) * self.curve.discount(t_curr))
                t_prev = t_curr

        principal_pv = self.notional * self.curve.discount(dates[-1])
        return dates, np.array(coupon_pvs), principal_pv


class CurrencySwap:
    def __init__(self, domestic_leg, foreign_leg, spot_fx):
        self.domestic_leg = domestic_leg
        self.foreign_leg = foreign_leg
        self.spot_fx = spot_fx

    def npv(self):
        return self.foreign_leg.pv() * self.spot_fx - self.domestic_leg.pv()

    def compute_fair_rate(self, solve_for="domestic"):
        leg = self.domestic_leg if solve_for == "domestic" else self.foreign_leg
        if leg.leg_type != "fixed":
            raise ValueError(f"Cannot solve for fair rate on a floating leg")

        def objective(r):
            leg.rate = r
            return self.npv()

        result = brentq(objective, 0.0001, 0.20)
        leg.rate = None
        return result


def fetch_foreign_zero_curve(spot_ticker, futures_tickers, usd_curve):
    """Derive a foreign zero curve from FX futures via covered interest parity.
    Returns (spot_fx, ZeroCurve)."""
    spot = get_price(spot_ticker)
    print(f"\nSpot FX ({spot_ticker}): {spot:.4f}")

    maturities, foreign_zero_rates = [], []
    for ticker in futures_tickers:
        F = get_price(ticker)
        T, expiry = get_ttm(ticker)
        r_domestic = float(usd_curve._spline(T))
        r_foreign = r_domestic - np.log(F / spot) / T
        maturities.append(T)
        foreign_zero_rates.append(r_foreign)
        print(f"  {expiry.strftime('%b %Y')}  T={T:.2f}Y  F={F:.4f}  r_USD={r_domestic*100:.3f}%  r_foreign={r_foreign*100:.3f}%")

    return spot, ZeroCurve(np.array(maturities), np.array(foreign_zero_rates))


def fx_sensitivity(swap, pct_range=0.05, steps=11):
    """NPV sensitivity to spot FX changes.
    Shows the MtM change of the value of the swap done at the current 
    spot fx rate for each instantaneous pct change in the spot price"""
    pct_changes = np.linspace(-pct_range, pct_range, steps)
    base_fx = swap.spot_fx
    npvs = []
    for pct in pct_changes:
        swap.spot_fx = base_fx * (1 + pct)
        npvs.append(swap.npv())
    swap.spot_fx = base_fx
    return pct_changes * 100, np.array(npvs)


def rate_sensitivity(swap, max_shift_bps=200, step=25):
    """NPV sensitivity to parallel shifts in zero curves."""

    shifts_bps = np.arange(-max_shift_bps, max_shift_bps + step, step)
    base_domestic_curve = swap.domestic_leg.curve
    base_foreign_curve = swap.foreign_leg.curve
    npvs_domestic, npvs_foreign, npvs_both = [], [], []

    for bp in shifts_bps:
        # Shift domestic only
        swap.domestic_leg.curve = base_domestic_curve.shift(bp)
        swap.foreign_leg.curve = base_foreign_curve
        npvs_domestic.append(swap.npv())

        # Shift foreign only
        swap.domestic_leg.curve = base_domestic_curve
        swap.foreign_leg.curve = base_foreign_curve.shift(bp)
        npvs_foreign.append(swap.npv())

        # Shift both
        swap.domestic_leg.curve = base_domestic_curve.shift(bp)
        swap.foreign_leg.curve = base_foreign_curve.shift(bp)
        npvs_both.append(swap.npv())

    swap.domestic_leg.curve = base_domestic_curve
    swap.foreign_leg.curve = base_foreign_curve
    return shifts_bps, np.array(npvs_domestic), np.array(npvs_foreign), np.array(npvs_both)


def plot_cashflows(swap):
    """Side-by-side bar chart: coupons only, with principal shown separately as annotations."""
    domestic_dates, domestic_coupons, domestic_principal = swap.domestic_leg.cashflow_pvs()
    _, foreign_coupons, foreign_principal = swap.foreign_leg.cashflow_pvs()
    foreign_coupons = foreign_coupons * swap.spot_fx
    foreign_principal = foreign_principal * swap.spot_fx

    fig, ax = plt.subplots(figsize=(12, 5))
    x = np.arange(len(domestic_dates))
    w = 0.15

    ax.bar(x - w, domestic_coupons, w * 2, label="Domestic coupons (pay)", color="steelblue", alpha=0.8)
    ax.bar(x + w, foreign_coupons, w * 2, label="Foreign coupons (receive)", color="darkorange", alpha=0.8)

    ax.set_xticks(x)
    ax.set_xticklabels([f"{t:.1f}Y" for t in domestic_dates])
    ax.set_xlabel("Payment date")
    ax.set_ylabel("PV (domestic currency)")
    ax.set_title(f"Currency Swap Coupon PV  |  Principal at maturity: domestic {domestic_principal:,.0f} / foreign {foreign_principal:,.0f}")
    ax.legend(fontsize=8)
    ax.grid(True, axis="y", linestyle="--", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cashflows_pv.png"), dpi=150, bbox_inches="tight")
    plt.show()


def plot_sensitivity(swap):
    """Two-panel chart: FX sensitivity (left) and rate sensitivity (right)."""
    fx_pcts, fx_npvs = fx_sensitivity(swap)
    shifts_bps, npvs_domestic, npvs_foreign, npvs_both = rate_sensitivity(swap)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # FX sensitivity
    ax1.plot(fx_pcts, fx_npvs, color="steelblue", linewidth=2)
    ax1.axhline(0, color="black", linewidth=0.5)
    ax1.axvline(0, color="grey", linewidth=0.5, linestyle="--")
    ax1.set_xlabel("Spot FX change (%)")
    ax1.set_ylabel("NPV (domestic currency)")
    ax1.set_title("NPV Sensitivity to Spot FX")
    ax1.grid(True, linestyle="--", alpha=0.3)

    # Rate sensitivity
    ax2.plot(shifts_bps, npvs_domestic, label="Domestic shift", color="steelblue", linewidth=2)
    ax2.plot(shifts_bps, npvs_foreign, label="Foreign shift", color="darkorange", linewidth=2)
    ax2.plot(shifts_bps, npvs_both, label="Both shift", color="green", linewidth=2, linestyle="--")
    ax2.axhline(0, color="black", linewidth=0.5)
    ax2.axvline(0, color="grey", linewidth=0.5, linestyle="--")
    ax2.set_xlabel("Parallel yield shift (bp)")
    ax2.set_ylabel("NPV (domestic currency)")
    ax2.set_title("NPV Sensitivity to Yield Curve Shifts")
    ax2.legend(fontsize=9)
    ax2.grid(True, linestyle="--", alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sensitivity_analysis.png"), dpi=150, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":

    maturities, par_yields = fetch_treasury_yields()
    zero_rates = compute_zero_rates(maturities, par_yields)
    domestic_zero_curve = ZeroCurve(maturities, zero_rates)

    spot_fx, foreign_zero_curve = fetch_foreign_zero_curve(FOREIGN_SPOT_TICKER, FOREIGN_FUTURES_TICKERS, domestic_zero_curve)

    if DOMESTIC_NOTIONAL is not None:
        domestic_notional = DOMESTIC_NOTIONAL
        foreign_notional = domestic_notional / spot_fx
    else:
        foreign_notional = FOREIGN_NOTIONAL
        domestic_notional = foreign_notional * spot_fx

    domestic_leg = SwapLeg(domestic_notional, DOMESTIC_LEG_TYPE, FREQUENCY, MATURITY, domestic_zero_curve, DOMESTIC_RATE)
    foreign_leg = SwapLeg(foreign_notional, FOREIGN_LEG_TYPE, FREQUENCY, MATURITY, foreign_zero_curve, FOREIGN_RATE)

    swap = CurrencySwap(domestic_leg, foreign_leg, spot_fx)
    fair_rate = swap.compute_fair_rate(solve_for=SOLVE_FOR)
    if SOLVE_FOR == "domestic":
        domestic_leg.rate = fair_rate
    else:
        foreign_leg.rate = fair_rate
    print(f"\nFair {SOLVE_FOR} fixed rate: {fair_rate*100:.4f}%")

    plot_cashflows(swap)
    plot_sensitivity(swap)