# Chapter 4 - Interest Rates

**Script:** `ch04_interest_rates/yield_curve_bootstrap.py`

Fetches live US Treasury yields from FRED, bootstraps a zero-coupon curve, computes period forward rates, and prices a bond against the zero curve.

```bash
python ch04_interest_rates/yield_curve_bootstrap.py
```

Edit `BOND` at the top of the script to change the bond.

---

## What it does

| Step | Detail |
|------|--------|
| Data | 11 Treasury CMT maturities (1M-30Y) pulled live from FRED |
| Zero rates | Bootstrapped from par yields using iterative coupon stripping |
| Forward rates | Period forward rates f(T1, T2) = (r2*T2 - r1*T1) / (T2 - T1) |
| Bond pricing | Each cash flow discounted at the interpolated zero rate |

All internal calculations use continuously compounded rates. Par yields from FRED are semi-annual BEY (bond-equivalent yield), converted to CC before bootstrapping. All three rate curves are plotted in BEY for consistency and to respect BEY convention for Treasury Yields.

---

## Parameters

Edit the `BOND` dict at the top of the script.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `face` | `1000` | Face value ($) |
| `coupon` | `0.045` | Annual coupon rate (4.5%) |
| `maturity` | `10` | Years to maturity |
| `freq` | `2` | Coupon payments per year |

---

## Output

### Console

```
Fetching US Treasury yields from FRED...
  DGS1MO   ( 0.083Y): 3.74%
  DGS3MO   ( 0.250Y): 3.68%
  DGS6MO   ( 0.500Y): 3.61%
  DGS1     ( 1.000Y): 3.52%
  DGS2     ( 2.000Y): 3.42%
  DGS3     ( 3.000Y): 3.46%
  DGS5     ( 5.000Y): 3.57%
  DGS7     ( 7.000Y): 3.78%
  DGS10    (10.000Y): 4.02%
  DGS20    (20.000Y): 4.60%
  DGS30    (30.000Y): 4.67%

Bond price (10Y, 4.50% coupon): $1039.4820
```

### Chart

Single figure with par yield, zero rate, and forward rate curves (all in BEY):

- Smooth spline curves for par and zero rates, with scatter dots at the 11 data points
- Step plot for forward rates, each step within its maturity interval [Ti, Ti+1]

---

## Data source

US Treasury constant-maturity yields via [FRED](https://fred.stlouisfed.org).

| FRED Series | Maturity |
|-------------|----------|
| DGS1MO | 1-Month |
| DGS3MO | 3-Month |
| DGS6MO | 6-Month |
| DGS1 | 1-Year |
| DGS2 | 2-Year |
| DGS3 | 3-Year |
| DGS5 | 5-Year |
| DGS7 | 7-Year |
| DGS10 | 10-Year |
| DGS20 | 20-Year |
| DGS30 | 30-Year |
