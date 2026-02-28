"""Chapter 4: Interest Rates - yield curve bootstrapping, forward rates computation, and bond pricing"""

import numpy as np
import requests
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline


# (maturity in years, FRED series ID)

FRED_SERIES = [
    (1/12, "DGS1MO"),
    (3/12, "DGS3MO"),
    (6/12, "DGS6MO"),
    (1.0,  "DGS1"),
    (2.0,  "DGS2"),
    (3.0,  "DGS3"),
    (5.0,  "DGS5"),
    (7.0,  "DGS7"),
    (10.0, "DGS10"),
    (20.0, "DGS20"),
    (30.0, "DGS30"),
]

FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"

BOND = {
    "face":     1000,   # face value ($)
    "coupon":   0.045,  # annual coupon rate
    "maturity": 10,     # years to maturity
    "freq":     2,      # coupon payments per year
}


def fetch_treasury_yields():

    """Fetch the latest available US Treasury CMT yields from FRED. FRED returns bond-equivalent yields (BEY, compounded twice a year as a convention) in percent."""

    maturities, yields = [], []
    print("Fetching US Treasury yields from FRED...")
    for T, series_id in FRED_SERIES:
        try:
            response = requests.get(FRED_URL.format(series_id), timeout=10)
            response.raise_for_status()
            lines = response.text.strip().split("\n")[1:]  # skip header row
            for line in reversed(lines):                   # get the last updated data first to keep the latest yield
                parts = line.split(",")
                if len(parts) == 2 and parts[1].strip() not in (".", ""):
                    value = float(parts[1]) / 100          # Divide by 100 to turn percentages into decimal values
                    maturities.append(T)
                    yields.append(value)
                    print(f"  {series_id:8s} ({T:6.3f}Y): {value * 100:.2f}%")
                    break
        except Exception as e:
            print(f"  {series_id} skipped: {e}")
    return np.array(maturities), np.array(yields)


# compounding conversions:

def bey_to_cc(y_bey):

    """Semi-annual BEY to continuously compounded rate."""

    return 2 * np.log(1 + y_bey / 2)

def cc_to_bey(y_cc):

    """Continuously compounded rate to semi-annual BEY."""

    return 2 * (np.exp(y_cc / 2) - 1)



def compute_zero_rates(maturities, par_yields):

    """Compute the zero rates from the par yield data"""

    zero_rates = bey_to_cc(par_yields)  # exact for T ≤ 0.5Y (zero-coupon T-bills); estimate for longer maturities, this serves as an initialization.
    for i, (T, y) in enumerate(zip(maturities, par_yields)):
        if T <= 0.5:
            continue  

        n_coupons = int(round(T * 2))                     # number of semi-annual payments (must be int for range)
        c = y / 2                                         # semi-annual coupon per $1 face value

        pv_coupons = 0
        for j in range(1, n_coupons):                     # all payments except the last one
            t_j = j * 0.5                                 # j-th payment is always at j × 0.5 years
            r_j = np.interp(t_j, maturities, zero_rates)  # look up zero rate at t_j
            pv_coupons += c * np.exp(-r_j * t_j)

        # 1 = pv_coupons + (1 + c) * exp(-r * T), we solve for r
        df = (1 - pv_coupons) / (1 + c)
        zero_rates[i] = -np.log(df) / T

    return zero_rates


def compute_forward_rates(maturities, zero_rates):

    """Calculate forward rates between each maturity from zero rates"""

    forward_rates = np.zeros(len(maturities) - 1)  # n maturities: n-1 forward rates

    for i in range(0, len(maturities) - 1):        # stop right before the last maturity as formula computes rate between [i] and [i+1]
        forward_rates[i] = ((zero_rates[i+1] * maturities[i+1]) - (zero_rates[i] * maturities[i])) / (maturities[i+1] - maturities[i])

    return forward_rates


def plot_curves(maturities, par_yields, zero_rates, forward_rates):

    """Plot yield curve, zero curve and forward rates curve (all in BEY %)"""

    T_fine = np.linspace(maturities[0], maturities[-1], 300)

    par_smooth  = CubicSpline(maturities, par_yields * 100)(T_fine) 
    zero_smooth = CubicSpline(maturities, cc_to_bey(zero_rates) * 100)(T_fine) # convert CC to BEY to plot all rates with the same compounding frequency

    plt.figure(figsize=(10, 5))
    plt.plot(T_fine, par_smooth, label="Par yield (BEY)", color="steelblue")
    plt.plot(T_fine, zero_smooth, label="Zero rate (BEY)", color="darkorange")
    forward_bey = np.append(cc_to_bey(forward_rates), cc_to_bey(forward_rates[-1])) * 100  # repeat last value to close the step at T[-1], otherwise the last rate isn't being plotted
    plt.step(maturities, forward_bey, where="post", label="Forward rate (BEY)", color="green", linestyle="--")

    plt.scatter(maturities, par_yields * 100, color="steelblue", zorder=5, s=30)
    plt.scatter(maturities, cc_to_bey(zero_rates) * 100, color="darkorange", zorder=5, s=30)

    plt.xlabel("Maturity (years)")
    plt.ylabel("Rate (% BEY)")
    plt.title("US Treasury Yield Curve - Par Yield, Zero Rates, and Forward Rates")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.show()


def price_bond(curve_maturities, zero_rates, bond):

    """Price a bond by discounting each cash flow at the interpolated zero rate."""
    # We are pricing a Treasury bond so using zero rates derived from Treasury Yields is appropriate. For derivatives pricing though, we would use OIS rates.

    face     = bond["face"]
    coupon   = bond["coupon"]
    maturity = bond["maturity"]
    freq     = bond["freq"]

    n_coupons  = int(round(maturity * freq)) # total number of coupon payments
    cf_per_period = coupon / freq * face     # coupon cash flow per period

    price = 0
    for j in range(1, n_coupons + 1):
        t_j = j / freq                                         # payment date in years
        r_j = np.interp(t_j, curve_maturities, zero_rates)     # zero rate at t_j (CC)
        cf  = cf_per_period + (face if j == n_coupons else 0)  # add face value on last payment
        price += cf * np.exp(-r_j * t_j)

    return price


if __name__ == "__main__":

    maturities, par_yields = fetch_treasury_yields()
    zero_rates = compute_zero_rates(maturities, par_yields)
    forward_rates = compute_forward_rates(maturities, zero_rates)

    price = price_bond(maturities, zero_rates, BOND)
    print(f"\nBond price ({BOND['maturity']}Y, {BOND['coupon']*100:.2f}% coupon): ${price:.2f}")

    plot_curves(maturities, par_yields, zero_rates, forward_rates)

