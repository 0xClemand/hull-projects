"""1. Introduction - project"""

import yfinance as yf 
import matplotlib.pyplot as plt 
import pandas as pd



class Asset:

    """Represents the financial asset corresponding to the ticker input by the user"""


    def __init__(self, ticker, start_date, end_date):
        self.ticker = ticker
        self.data = self.fetch_data(start_date, end_date)
        if not self.data.empty: print(f"Data for {self.ticker} from {start_date} to {end_date} fetched successfully.")
        self.currency = yf.Ticker(ticker).info.get('currency', 'USD')
        if self.currency!= 'USD': 
            self.convert_to_usd(start_date, end_date) 

    def convert_to_usd(self, start_date, end_date):
        fx_pair= f"{self.currency}USD=X" 
        fx = yf.download(fx_pair, start=start_date, end=end_date)['Close'].squeeze()
        if fx.empty: 
            print(f"Warning: No FX data found for {fx_pair}. Prices will not be converted to USD.") 
            return
        else: fx = fx.reindex(self.data.index).ffill().bfill() # Align FX data with asset data, forward and backward fill to handle any missing dates
        self.data['Close'] = self.data['Close'].squeeze() * fx 
        print(f"{self.ticker} prices converted from {self.currency} to USD.")

    def fetch_data(self, start_date, end_date):
        return yf.download(self.ticker, start=start_date, end=end_date)
    


class Position:

    """Represents a position in the asset"""


    def __init__(self, asset, size, direction):
        self.asset = asset
        self.size = size
        self.direction = direction
        self.entry_price = asset.data['Close'].iloc[0].item()
        self.exit_price = asset.data['Close'].iloc[-1].item()

    def calculate_pnl(self):
        if self.direction == 'long':
            return (self.exit_price - self.entry_price) * self.size
        elif self.direction == 'short':
            return (self.entry_price - self.exit_price) * self.size
        else: raise ValueError("Direction must be 'long' or 'short'")
        
    def daily_cum_pnl(self): 
        if self.direction == 'long':
            return (self.asset.data['Close'].squeeze() - self.entry_price) * self.size #.squeeze() converts from DataFrame to Series if only one column, then we can do element-wise operations
        elif self.direction == 'short':
            return (self.entry_price - self.asset.data['Close'].squeeze()) * self.size
        else: raise ValueError("Direction must be 'long' or 'short'")



if __name__ == "__main__":


    portfolio = []
    portfolio_pnl = 0

    while True:

        add = input("\nDo you want to add a position? (yes/no): ").lower().strip()
        while add not in ['yes', 'no']: add = input("Please enter 'yes' or 'no': ").lower().strip()
        if add == 'no':break
        ticker = input("Enter ticker symbol: ")
        start_date = input("Enter start date (YYYY-MM-DD): ")
        end_date = input("Enter end date (YYYY-MM-DD): ")
        
        asset = Asset(ticker, start_date, end_date)
        if asset.data.empty:
            print("No data found for that ticker/date range")
            continue

        direction = input("Enter position direction (long/short): ").lower().strip()
        while direction not in ['long', 'short']: direction = input("Please enter 'long' or 'short': ").lower().strip()

        try:
            size = float(input("Enter position size: "))
        except ValueError:
            print("Please enter a valid number for position size.")
            continue

        position = Position(asset, size, direction)
        portfolio.append(position)

    for pos in portfolio:
        pnl = pos.calculate_pnl()
        portfolio_pnl += pnl
        print(f"{pos.direction.upper()} position in {pos.asset.ticker} has a P&L of: ${pnl:.2f}")

    print(f"\nTotal Portfolio P&L: ${portfolio_pnl:.2f}\n")


    if portfolio: # Only plot if there are positions in the portfolio

        pnl_df = pd.DataFrame({f"{i+1}. {pos.direction.upper()} {pos.asset.ticker}": pos.daily_cum_pnl() for i, pos in enumerate(portfolio)}) # Use position number to allow for multiple positions in the same ticker without replacing columns in the df
        pnl_df = pnl_df.ffill().fillna(0) # Forward fill to handle different date ranges, then fill any remaining NaNs with 0. Necessary to align the P&L curves for plotting and ensure the portfolio P&L is cumulative across all positions
        pnl_df['Total Portfolio P&L'] = pnl_df.sum(axis=1)

        ax = pnl_df.drop(columns=['Total Portfolio P&L']).plot(figsize=(12, 6), grid = True, alpha = 0.7, title = "Cumulative P&L of Portfolio Over Time", xlabel = "Date", ylabel = "Cumulative P&L ($)")
        ax.plot(pnl_df.index, pnl_df['Total Portfolio P&L'], label='Total Portfolio P&L', color='black', linewidth=2) # Plot total portfolio P&L separately as a bold black line
        plt.legend()
        plt.tight_layout()
        plt.show()  