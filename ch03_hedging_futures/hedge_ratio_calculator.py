"""Chapter 3: Hedging Strategies Using Futures - optimal hedge ratio calculator with regression analysis and hedge performance"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from portfolio_simulator import Asset, Position
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from datetime import datetime
from dateutil.relativedelta import relativedelta


def calculate_hedge_ratio(spot_prices, futures_prices):

    """Calculate h_star as the slope of the linear regression of spot price changes against futures price changes in the past 6 months before the start date of the hedge"""


    spot_prices, futures_prices = spot_prices.align(futures_prices, join='inner') # In case of date discrepencies, keep only the dates present in both series

    spot_delta = np.diff(spot_prices)
    futures_delta = np.diff(futures_prices)

    results = stats.linregress(futures_delta, spot_delta) # X=futures and Y=spot, so regressing spot changes on futures changes
    h_star = results.slope
    rho = results.rvalue
    effectiveness = rho ** 2

    # Plot regression

    plt.scatter(futures_delta, spot_delta)
    plt.plot(futures_delta, h_star*futures_delta, label=f'Regression (h_star={h_star:.2f})')
    plt.xlabel('Delta futures')
    plt.ylabel('Delta spot')
    plt.title('Linear regression of daily price changes (from 6 months before to the start of the hedge)')
    plt.legend()
    plt.tight_layout()
    plt.show(block=False)

    return h_star, rho, effectiveness




if __name__ == "__main__":

    ticker_spot = input("Please input the ticker of the spot asset you want to hedge: ")
    ticker_futures = input("Please enter the specific ticker of the futures contract used to hedge the asset (ROOT + MONTH_LETTER + TWO_DIGIT_YEAR + .EXCHANGE): ")
    start_date = input("Please enter the date of the beginning of the hedge (YYYY-MM-DD): ")
    end_date = input("Please enter the date of the ending of the hedge (YYYY-MM-DD): ")

    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    today = datetime.today()
    backtest_end_date = min(end_dt, today)

    if start_dt > today:
        print("The hedge will occur in the future and cannot be backtested.")
        sys.exit(1)

    spot = Asset(ticker_spot, start_date, backtest_end_date)
    futures = Asset(ticker_futures, start_date, backtest_end_date)


    estimation_start = start_dt - relativedelta(months=6)
    spot_est = Asset(ticker_spot, estimation_start, start_date)
    futures_est = Asset(ticker_futures, estimation_start, start_date)
    spot_prices = spot_est.data['Close'].squeeze()
    futures_prices = futures_est.data['Close'].squeeze()

    if spot_est.data.empty or futures_est.data.empty: 
        print("Not enough data for estimation. Please try a different window.")
        sys.exit(1)

    h_star, rho, effectiveness = calculate_hedge_ratio(spot_prices, futures_prices)

    print(f"results: \nOptimal hedge ratio: {h_star:.4f} \nCorrelation: {rho:.2f} \nEffectiveness (R^2):{effectiveness:.2f}")


    # Effective results of the hedge

    spot_direction = input("Please indicate the direction of your spot exposure (long/short): ").lower().strip()
    while spot_direction not in ['long', 'short']: 
        spot_direction = input("Please enter 'long' or 'short': ").lower().strip()
    if spot_direction == "long":
        futures_direction = "short"
    else:
        futures_direction = "long"
    spot_size = float(input("Please input the size of your spot position: "))
    futures_multiplier = float(input("Please input the number of units included in each futures contract: "))
    futures_size = (h_star * spot_size) / futures_multiplier # Computing the optimal number of contracts

    spot_position = Position(spot, spot_size, spot_direction)
    futures_position = Position(futures, futures_size * futures_multiplier, futures_direction) # Size passed as total units (contracts × multiplier) so Position computes P&L correctly as ΔPrice × total_units
    spot_pnl = spot_position.calculate_pnl()
    futures_pnl = futures_position.calculate_pnl()
    hedged_pnl = spot_pnl + futures_pnl


    print(f"\nSpot position ({spot_direction} {spot_size:.2f} shares of {ticker_spot}) PNL: ${spot_pnl:.2f}")
    print(f"Futures position ({futures_direction} {futures_size:.2f} contracts of {ticker_futures}) PNL: ${futures_pnl:.2f}")
    print(f"Hedged position PNL: ${hedged_pnl:.2f}")


    spot_daily_cum_pnl = spot_position.daily_cum_pnl()
    futures_daily_cum_pnl = futures_position.daily_cum_pnl()
    spot_daily_cum_pnl, futures_daily_cum_pnl = spot_daily_cum_pnl.align(futures_daily_cum_pnl, join='inner')
    hedged_daily_cum_pnl = spot_daily_cum_pnl + futures_daily_cum_pnl

    spot_daily_pnl = spot_daily_cum_pnl.diff().dropna()
    hedged_daily_pnl = hedged_daily_cum_pnl.diff().dropna()

    var_spot = spot_daily_pnl.var()
    var_hedged = hedged_daily_pnl.var()
    variance_reduction = 1 - (var_hedged / var_spot)

    print(f"\nVariance of spot daily P&L: ${var_spot:.2f}")
    print(f"Variance of hedged daily P&L: ${var_hedged:.2f}")
    print(f"Variance reduction: {variance_reduction:.2%}")


    fig, ax = plt.subplots(figsize=(12,6))

    ax.plot(spot_daily_cum_pnl.index, spot_daily_cum_pnl, label=f"PNL of the spot exposure ({spot_direction} {spot_size:.2f} shares of {ticker_spot})")
    ax.plot(futures_daily_cum_pnl.index, futures_daily_cum_pnl, label=f"PNL of the hedge ({futures_direction} {futures_size:.2f} contracts of {ticker_futures})")
    ax.plot(hedged_daily_cum_pnl.index, hedged_daily_cum_pnl, label="PNL of the hedged position", color='Black', linewidth=2)
    ax.set_title("Daily cumulative PNL of the hedging of a spot exposure using futures contracts")
    ax.set_xlabel("Date")
    ax.set_ylabel("$USD")
    ax.legend()
    ax.grid(True, alpha=0.5)
    plt.tight_layout()
    plt.show()