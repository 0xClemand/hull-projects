# Hull Projects

The purpose of this repository is to showcase my work through *Options, Futures, and Other Derivatives* by John C. Hull, with one Python project per chapter. Each project reuses key concepts from its associated chapter and aims to deepen my understanding and to confront the book's theoretical contents with practical applications.

## Chapters

| # | Title | Script |
|---|-------|--------|
| 1 | Introduction | [portfolio_simulator.py](portfolio_simulator.py) |
| 2 | Futures Markets and Central Counterparties | [futures_margin_simulator.py](ch02_futures_markets/futures_margin_simulator.py) |
| 3 | Hedging Strategies Using Futures | [hedge_ratio_calculator.py](ch03_hedging_futures/hedge_ratio_calculator.py) |

## Setup

```bash
pip install -r requirements.txt
```

All scripts pull live historical data from public APIs; no local data files needed. Results are fully reproducible with the examples of user inputs in each chapter's README.

> `portfolio_simulator.py` is a shared module imported by later chapters, in order to use the 'Asset' and 'Position' classes.

---

## Chapter 1 — Introduction

**Script:** `portfolio_simulator.py`

Builds a portfolio of long/short positions on any Yahoo Finance ticker, computes per-position and total P&L, and plots cumulative P&L curves over the holding period. Non-USD assets are automatically converted. The script handles different holding periods smoothly.

```bash
python portfolio_simulator.py
```

The script prompts you for each position interactively. Type `no` when done adding positions.

### Parameters

| Prompt | Example |
|--------|---------|
| Ticker | `AAPL`, `SPY`, `MSFT` |
| Start date | `2024-01-02` |
| End date | `2024-06-28` |
| Direction | `long` / `short` |
| Size | `100` |

---

### Example 1 — Multi-currency: global equity basket (H1 2024)

Tests the automatic FX conversion. Toyota is in JPY, ASML and LVMH are in EUR. The Nikkei had a strong H1 2024 on the weak-yen tailwind and Buffett's Japan trade; ASML was buoyed by AI chip demand; LVMH was weak on the China luxury slowdown.

```
position 1:  7203.T   |  2024-01-02  |  2024-06-28  |  long   |  500 shares   (Toyota, JPY)
position 2:  ASML.AS  |  2024-01-02  |  2024-06-28  |  long   |  10 shares    (ASML, EUR)
position 3:  MC.PA    |  2024-01-02  |  2024-06-28  |  short  |  15 shares    (LVMH, EUR)
```

```
LONG position in 7203.T has a P&L of:   $1002.53
LONG position in ASML.AS has a P&L of:  $2903.72
SHORT position in MC.PA has a P&L of:   $383.53
Total Portfolio P&L:                     $4289.78
```

---

### Example 2 — Different holding periods: semiconductor cycle (2024)

Each position has a different start date, which tests the forward-fill logic in the cumulative P&L chart. NVDA is held for the full year; the INTC short is only opened in May after the bad earnings print that kicked off its decline; ARM is added in March once the post-IPO lockup noise settles.

```
position 1:  NVDA  |  2024-01-02  |  2024-12-31  |  long   |  30 shares
position 2:  INTC  |  2024-05-01  |  2024-12-31  |  short  |  200 shares
position 3:  ARM   |  2024-03-01  |  2024-12-31  |  long   |  50 shares
```

```
LONG position in NVDA has a P&L of:   $2679.34
SHORT position in INTC has a P&L of:  $2047.30
LONG position in ARM has a P&L of:    $-785.50
Total Portfolio P&L:                   $3941.13
```