"""2. Futures markets and central counterparties - project"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from portfolio_simulator import Asset, Position
import pandas as pd
import matplotlib.pyplot as plt



# Adding a daily_pnl function in a new class to maintain object-oriented structure

class FuturesPosition(Position):

    def __init__(self, asset, size, direction, multiplier):
        super().__init__(asset, size, direction)
        self.multiplier = multiplier

    def daily_pnl(self):
        prices = self.asset.data["Close"].squeeze()
        daily_changes = prices.diff().dropna()
        if self.direction == "long":
            return daily_changes * self.size * self.multiplier
        if self.direction == "short":
            return -daily_changes * self.size * self.multiplier
        


# Implement the margin account simulation logic

def simulate_margin_account(variation_margin, initial_margin, maintenance_margin_requirement, capital):
    margin_calls = {}
    margin_account = pd.Series(index=variation_margin.index, dtype=float)
    margin_account.iloc[0] = initial_margin
    total_interest = 0

    current_balance = initial_margin
    for date, pnl in variation_margin.items():
        interest = initial_margin * (interest_rate / 360) * calendar_days[date] # Dividing the annual rate by 360 is the convention for most money markets instruments / As per the Hull, interest is only earned on the initial margin, not on the variation margin
        current_balance += pnl + interest
        total_interest += interest
        margin_account[date] = current_balance

        if current_balance < maintenance_margin_requirement * initial_margin:
            top_up = initial_margin - current_balance
            margin_calls[date] = top_up
            
            if top_up > capital:
                print(f"\nInsufficient capital to meet margin call. Position liquidated on {date.date()}")
                break
            else: 
                capital -= top_up
                current_balance += top_up


    margin_account = margin_account.dropna()
    return margin_account, margin_calls, capital, total_interest




if __name__ == "__main__":



    # Define all the variables we will use

    ticker = input("Please input the specific futures contract ticker (ROOT + MONTH_LETTER + TWO_DIGIT_YEAR + .EXCHANGE): ")
    start_date = input("Enter start date (YYYY-MM-DD): ")
    end_date = input("Enter end date (YYYY-MM-DD): ")
    underlying = Asset(ticker, start_date, end_date)


    while True:
        try:
            size = int(input("Please enter position size (in integer number of contracts): "))
            multiplier = int(input("Please enter the contract multiplier (how many units of underlying per contract): "))
            break
        except ValueError:
            print("Please enter a valid integer.")

    direction = input("Enter position direction (long/short): ").lower().strip()
    while direction not in ['long', 'short']: direction = input("Please enter 'long' or 'short': ").lower().strip()

    initial_capital = float(input("Please enter your available capital ($): "))
    initial_margin = float(input("Please enter the initial margin requirement ($): "))
    interest_rate = float(input("Please enter the annual interest rate earned on your margin (as a proportion, between 0 and 1): "))
    while not (0 <= interest_rate <= 1): interest_rate = float(input("Please enter a valid proportion (between 0 and 1): "))

    capital = initial_capital

    if initial_margin > capital: 
        print("Insufficient capital to meet initial margin.")
        sys.exit(1)
    else:
        capital -= initial_margin

    maintenance_margin_requirement = float(input("Please enter the maintenance margin requirement (between 0 and 1, as a proportion of initial margin): "))
    while not (0 <= maintenance_margin_requirement <= 1): maintenance_margin_requirement = float(input("Please enter a valid proportion (between 0 and 1): "))

    position = FuturesPosition(underlying, size, direction, multiplier)
    
    variation_margin = position.daily_pnl() # We have the right series, but starting at the second trading day with the first pnl value. We need to initialise at tradi ng day 1 with a pnl of 0.
    first_trading_day = position.asset.data["Close"].squeeze().index[0] 
    variation_margin = pd.concat([pd.Series([0], index=[first_trading_day]), variation_margin])

    dates = variation_margin.index
    calendar_days = dates.to_series().diff().dt.days.fillna(1) # Get the series of how many calendar days there are between each date (useful to compute interest)


    margin_account, margin_calls, capital, total_interest = simulate_margin_account(variation_margin, initial_margin, maintenance_margin_requirement, capital)
    variation_margin = variation_margin[:margin_account.index[-1]]
    total_pnl = margin_account.iloc[-1] + capital - initial_capital




    # Printing main results

    print(f"\nFinal margin account balance: ${margin_account.iloc[-1]:.2f}")
    print(f"Remaining capital: ${capital:.2f}")
    print(f"Total interest earned: ${total_interest:.2f}")
    print(f"Total P&L: ${total_pnl:.2f}")
    if margin_calls:
        print(f"\nMargin calls ({len(margin_calls)}):")
        for date, amount in margin_calls.items():
            print(f" {date.date()}: ${amount:.2f}")




    # Plotting results

    fig, ax = plt.subplots(figsize=(12, 6)) # Using ax for object-oriented style

    ax.plot(margin_account.index, margin_account, label="Margin Account Balance", linewidth=1)
    ax.plot(variation_margin.index, variation_margin.cumsum(), label="Cumulative P&L", linewidth=1)
    ax.axhline(y=initial_margin, color="green", linestyle="--", label="Initial Margin", alpha=0.7)
    ax.axhline(y=maintenance_margin_requirement * initial_margin, color="red", linestyle="--", label="Maintenance Margin", alpha=0.7)

    if margin_calls:
        call_dates = list(margin_calls.keys())
        call_balances = [margin_account[d] for d in call_dates]
        ax.scatter(call_dates, call_balances, color="red", zorder=5, s=100, label="Margin Calls", marker="v") # Puts a red triangle on the graph for every margin call event (at the matching date and account balance)

    ax.set_title(f"Futures Margin Account Simulation — {ticker} ({direction.upper()} {size} contracts)")
    ax.set_xlabel("Date")
    ax.set_ylabel("USD ($)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()