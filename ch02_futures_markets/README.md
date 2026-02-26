# Chapter 2 — Futures Markets and Central Counterparties

Simulates a futures margin account over a holding period. Tracks daily variation margin (mark-to-market settlement), interest earned on the initial margin, margin calls when the balance drops below the maintenance threshold, and liquidation if capital runs out.

```bash
# run from the project root
python ch02_futures_markets/futures_margin_simulator.py
```

## Parameters

| Prompt | Description | Example |
|--------|-------------|---------|
| Ticker | Specific futures contract (see format below) | `GCZ25.CMX` |
| Start / End date | Holding period — must fall within the contract's active window | `2025-07-01` / `2025-11-25` |
| Position size | Number of contracts (integer) | `1` |
| Contract multiplier | Units of underlying per contract | `100` for gold, `1000` for crude oil, `50` for E-mini S&P |
| Direction | `long` / `short` | |
| Available capital | Total capital available excluding initial margin | `$15000` |
| Initial margin | Margin required to open position | `$8000` |
| Annual interest rate | Rate earned on margin balance (as proportion) | `0.05` |
| Maintenance margin | Fraction of initial margin below which a call is triggered | `0.75` |

### Ticker format

```
ROOT + MONTH_LETTER + TWO_DIGIT_YEAR + .EXCHANGE
```

Use **specific expiring contracts**, not continuous front-month tickers like `GC=F` — those roll over daily and would give different results depending on when the script is run.

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

---

## Example 1 — Long gold, H2 2025

Gold remained elevated and bullish in H2 2025. The leverage trade is a success with a substantial P&L and liquidation was averted despite the high leverage and two margin calls.

```
Ticker:                 GCZ25.CMX
Start:                  2025-07-01
End:                    2025-11-25
Size:                   1 contract
Multiplier:             100
Direction:              long
Capital:                $15000
Initial margin:         $8000
Interest rate:          0.05
Maintenance margin:     0.75
```

Results:

```
Final margin account balance:  $82688.87
Remaining capital:             $1384.44
Total interest earned:         $163.33
Total P&L:                     $69073.32

Margin calls (2):
 2025-07-08: $3241.11
 2025-07-31: $2374.44
```


## Example 2 — Short gold, H2 2025 (liquidation)

Same contract as Example 1, opposite direction. Gold remaining at high levels means consecutive negative daily settlements for the short position. With only $5000 available after posting the initial margin, the capital is too thin to absorb more than one or two top-ups before a call exceeds what's left and the position is liquidated. The end date is nominal; the script exits early and print the liquidation date.

```
Ticker:                 GCZ25.CMX
Start:                  2025-07-01
End:                    2025-11-25
Size:                   1 contract
Multiplier:             100
Direction:              short
Capital:                $15000
Initial margin:         $8000
Interest rate:          0.05
Maintenance margin:     0.75
```

Results:

```
Insufficient capital to meet margin call. Position liquidated on 2025-07-22

Final margin account balance: $4111.10
Remaining capital: $1243.35
Total interest earned: $24.44
Total P&L: $-9645.55

Margin calls (2):
 2025-07-21: $5756.65
 2025-07-22: $3888.90
```