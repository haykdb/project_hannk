"""
Example: Analyzing Collected Crypto Data

This script demonstrates how to load and analyze the collected data.
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


def load_data():
    """Load the collected crypto data"""
    data_file = Path('data/crypto_data.csv')
    
    if not data_file.exists():
        print("Error: No data file found. Run data collection first.")
        return None
    
    df = pd.read_csv(data_file)
    df['date'] = pd.to_datetime(df['date'])
    
    print("Data loaded successfully!")
    print(f"Total rows: {len(df):,}")
    print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"Unique pairs: {df['symbol'].nunique()}")
    print(f"Unique assets: {df['base_asset'].nunique()}")
    
    return df


def show_top_coins(df, n=10):
    """Show top N coins by market cap"""
    latest = df[df['date'] == df['date'].max()].copy()
    top_coins = latest.nlargest(n, 'market_cap')[['symbol', 'base_asset', 'price', 'market_cap', 'volume']]
    
    print(f"\n📊 Top {n} Coins by Market Cap (Latest Data):")
    print("=" * 80)
    for idx, row in top_coins.iterrows():
        print(f"{row['symbol']:15} | {row['base_asset']:8} | "
              f"${row['price']:>12,.2f} | "
              f"MCap: ${row['market_cap']/1e9:>8,.2f}B | "
              f"Vol: ${row['volume']/1e9:>8,.2f}B")


def calculate_returns(df, symbol, days=30):
    """Calculate returns for a given symbol"""
    coin_data = df[df['symbol'] == symbol].sort_values('date').tail(days + 1)
    
    if len(coin_data) < 2:
        print(f"Not enough data for {symbol}")
        return
    
    initial_price = coin_data.iloc[0]['price']
    final_price = coin_data.iloc[-1]['price']
    return_pct = ((final_price - initial_price) / initial_price) * 100
    
    print(f"\n📈 {symbol} - {days} Day Performance:")
    print(f"  Initial Price: ${initial_price:,.2f}")
    print(f"  Final Price:   ${final_price:,.2f}")
    print(f"  Return:        {return_pct:+.2f}%")
    
    return return_pct


def plot_price_history(df, symbols, days=90):
    """Plot price history for given symbols"""
    plt.figure(figsize=(12, 6))
    
    for symbol in symbols:
        coin_data = df[df['symbol'] == symbol].sort_values('date').tail(days)
        
        if not coin_data.empty:
            plt.plot(coin_data['date'], coin_data['price'], 
                    label=symbol, linewidth=2)
    
    plt.title(f'Price History - Last {days} Days', fontsize=14, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Price (USD)', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    output_file = 'price_history.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n📊 Chart saved to: {output_file}")
    plt.close()


def compare_market_caps(df, symbols):
    """Compare market cap evolution"""
    plt.figure(figsize=(12, 6))
    
    for symbol in symbols:
        coin_data = df[df['symbol'] == symbol].sort_values('date')
        
        if not coin_data.empty:
            plt.plot(coin_data['date'], coin_data['market_cap'] / 1e9,
                    label=symbol, linewidth=2)
    
    plt.title('Market Cap Evolution', fontsize=14, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Market Cap (Billions USD)', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    output_file = 'market_cap_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"📊 Chart saved to: {output_file}")
    plt.close()


def get_statistics(df, symbol):
    """Calculate statistics for a symbol"""
    coin_data = df[df['symbol'] == symbol].copy()
    
    print(f"\n📊 Statistics for {symbol}:")
    print("=" * 60)
    print(f"  Data points:       {len(coin_data)}")
    print(f"  Date range:        {coin_data['date'].min().date()} to {coin_data['date'].max().date()}")
    print(f"\n  Price:")
    print(f"    Current:         ${coin_data['price'].iloc[-1]:,.2f}")
    print(f"    Mean:            ${coin_data['price'].mean():,.2f}")
    print(f"    Min:             ${coin_data['price'].min():,.2f}")
    print(f"    Max:             ${coin_data['price'].max():,.2f}")
    print(f"    Std Dev:         ${coin_data['price'].std():,.2f}")
    print(f"\n  Market Cap:")
    print(f"    Current:         ${coin_data['market_cap'].iloc[-1]/1e9:,.2f}B")
    print(f"    Mean:            ${coin_data['market_cap'].mean()/1e9:,.2f}B")
    print(f"\n  Volume:")
    print(f"    Current 24h:     ${coin_data['volume'].iloc[-1]/1e9:,.2f}B")
    print(f"    Average 24h:     ${coin_data['volume'].mean()/1e9:,.2f}B")


def main():
    """Main analysis"""
    print("=" * 80)
    print("Crypto Data Analysis Examples")
    print("=" * 80)
    
    # Load data
    df = load_data()
    if df is None:
        return
    
    # Show top coins
    show_top_coins(df, n=10)
    
    # Calculate returns for major coins
    major_coins = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    print("\n" + "=" * 80)
    print("30-Day Returns:")
    print("=" * 80)
    
    for symbol in major_coins:
        if symbol in df['symbol'].values:
            calculate_returns(df, symbol, days=30)
    
    # Get statistics for Bitcoin
    if 'BTCUSDT' in df['symbol'].values:
        get_statistics(df, 'BTCUSDT')
    
    # Create visualizations
    print("\n" + "=" * 80)
    print("Creating Visualizations...")
    print("=" * 80)
    
    # Price history
    plot_symbols = [s for s in ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'] if s in df['symbol'].values]
    if plot_symbols:
        plot_price_history(df, plot_symbols, days=90)
        compare_market_caps(df, plot_symbols)
    
    print("\n" + "=" * 80)
    print("Analysis Complete!")
    print("=" * 80)


if __name__ == '__main__':
    # Optional: Install matplotlib if not present
    try:
        import matplotlib
    except ImportError:
        print("Installing matplotlib...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'matplotlib'])
        print("Please run the script again.")
        exit()
    
    main()
