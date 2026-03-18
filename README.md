# Hull Projects

The purpose of this repository is to showcase my work through *Options, Futures, and Other Derivatives* by John C. Hull, with one Python project per chapter. Each project reuses key concepts from its associated chapter and aims to deepen my understanding and to confront the book's theoretical contents with practical applications.

## Chapters

| # | Title | Script |
|---|-------|--------|
| 1 | Introduction | [portfolio_simulator.py](ch01_introduction/portfolio_simulator.py) |
| 2 | Futures Markets and Central Counterparties | [futures_margin_simulator.py](ch02_futures_markets/futures_margin_simulator.py) |
| 3 | Hedging Strategies Using Futures | [hedge_ratio_calculator.py](ch03_hedging_futures/hedge_ratio_calculator.py) |
| 4 | Interest Rates | [yield_curve_bootstrap.py](ch04_interest_rates/yield_curve_bootstrap.py) |
| 5 | Determination of Forward and Futures Prices | [implied_carry_calculator.py](ch05_forward_futures_pricing/implied_carry_calculator.py) |
| 6 | Interest Rate Futures | [ctd_bond_finder.py](ch06_interest_rate_futures/ctd_bond_finder.py) |

## Setup

```bash
git clone https://github.com/0xClemand/hull-projects.git
cd hull-projects
pip install -r requirements.txt
```

Most scripts pull live data from public APIs; some chapters require local data files as noted in their README. Results are fully reproducible with the examples of user inputs in each chapter's README.