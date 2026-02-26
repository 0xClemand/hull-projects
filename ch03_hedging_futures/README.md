# Chapter 3 - Hedging Strategies Using Futures

Implements the minimum-variance hedge ratio (h*) from Hull Chapter 3. Estimates h* via OLS regression of spot vs. futures price changes over the 6 months preceding the hedge, then simulates the hedged position over the hedge period and compares P&L variance against the P&L variance of the unhedged spot exposure.

```bash
# run from the project root
python ch03_hedging_futures/hedge_ratio_calculator.py
```

## Parameters

| Prompt | Description | Example |
|--------|-------------|---------|
| Spot ticker | Asset being hedged | `XOM`, `GLD`, `QQQ` |
| Futures ticker | Hedging instrument (see format below) | `CLZ25.NYM` |
| Start date | Beginning of hedge period | `2025-07-01` |
| End date | End of hedge period | `2025-11-14` |
| Spot direction | Direction of your exposure | `long` / `short` |
| Spot size | Number of shares/units held | `1000` |
| Contract multiplier | Units of underlying per futures contract | `1000` for crude, `100` for gold, `20` for NQ |

The script automatically fetches the 6-month estimation window before your start date to compute h*.

### Ticker format

```
ROOT + MONTH_LETTER + TWO_DIGIT_YEAR + .EXCHANGE
```

Use **specific expiring contracts**, not continuous front-month tickers like `CL=F`, those are rolling based on today's date and would give different results depending on when the script is run.

| Month | Code | | Exchange | Code |
|-------|------|-|----------|------|
| January | F | | COMEX (gold, silver) | `.CMX` |
| February | G | | NYMEX (crude oil, nat. gas) | `.NYM` |
| March | H | | CME (S&P, Nasdaq) | `.CME` |
| April | J | | CBOT (grains) | `.CBT` |
| May | K | | | |
| June | M | | | |
| July | N | | | |
| August | Q | | | |
| September | U | | | |
| October | V | | | |
| November | X | | | |
| December | Z | | | |

> The same futures ticker is used for both the 6-month estimation window and the hedge period. Make sure the chosen contract was already actively trading 6 months before the start date.


## Example 1 - Hedge gold ETF with gold futures (H2 2025)

GLD tracks the gold spot price very closely. This produces a very high correlation with substantial variance reduction; a near-perfect hedge. 

```
Spot ticker:          GLD
Futures ticker:       GCZ25.CMX
Start:                2025-07-01
End:                  2025-11-25
Spot direction:       long
Spot size:            500 shares
Contract multiplier:  100
```

Results:

```
Optimal hedge ratio:  0.0818 
Correlation:          0.95 
Effectiveness (R^2):  0.91

Spot position (long 500.00 shares of GLD) PNL:             $36325.01
Futures position (short 0.41 contracts of GCZ25.CMX) PNL:  $-28170.18
Hedged position PNL:                                       $8154.83

Variance of spot daily P&L:    $5511780.26
Variance of hedged daily P&L:  $710404.28
Variance reduction:             87.11%
```

---

## Example 2 - Cross-hedge: gold miners ETF with gold futures (H2 2025)

GDX holds gold mining companies, which are correlated with gold but not as tightly as GLD: miners also carry equity risk, operational leverage, and currency exposure. This makes it a cross-hedge: the hedging instrument (gold futures) is related to but not the same as the underlying risk. The correlation and variance reduction we get are lower, but still significant.

```
Spot ticker:          GDX
Futures ticker:       GCZ25.CMX
Start:                2025-07-01
End:                  2025-11-25
Spot direction:       long
Spot size:            1000 shares
Contract multiplier:  100
```

Results:

```
Optimal hedge ratio:  0.0202 
Correlation:          0.81 
Effectiveness (R^2):  0.65

Spot position (long 1000.00 shares of GDX) PNL:            $25733.11
Futures position (short 0.20 contracts of GCZ25.CMX) PNL:  $-13915.07
Hedged position PNL:                                       $11818.04

Variance of spot daily P&L:    $3067619.35
Variance of hedged daily P&L:  $1366102.95
Variance reduction:             55.47%
```