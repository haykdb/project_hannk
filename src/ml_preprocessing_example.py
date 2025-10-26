"""
Example: Using Binance EOD Data for ML Trading Model

This script demonstrates how to load and prepare the collected data
for machine learning-based portfolio weight generation.
"""

import pandas as pd
import numpy as np
from pathlib import Path


def load_data(data_path: str = "../data/all_pairs_eod.csv") -> pd.DataFrame:
    """Load the collected Binance EOD data"""
    df = pd.read_csv(data_path)
    df['date'] = pd.to_datetime(df['date'])
    return df


def filter_liquid_pairs(df: pd.DataFrame, min_avg_volume: float = 1000000, 
                        quote_currency: str = 'USDT') -> pd.DataFrame:
    """
    Filter for liquid trading pairs
    
    Args:
        df: Raw data DataFrame
        min_avg_volume: Minimum average daily volume in quote currency
        quote_currency: Quote currency to filter (USDT, BTC, etc.)
    
    Returns:
        Filtered DataFrame
    """
    # Filter for quote currency
    if quote_currency:
        df = df[df['symbol'].str.endswith(quote_currency)].copy()
    
    # Calculate average volume per symbol
    avg_volumes = df.groupby('symbol')['quote_volume'].mean()
    
    # Filter symbols with sufficient volume
    liquid_symbols = avg_volumes[avg_volumes >= min_avg_volume].index.tolist()
    
    print(f"Found {len(liquid_symbols)} liquid pairs with avg volume >= ${min_avg_volume:,.0f}")
    
    return df[df['symbol'].isin(liquid_symbols)].copy()


def create_price_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Create price matrix with dates as rows and symbols as columns"""
    return df.pivot(index='date', columns='symbol', values='close')


def create_volume_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Create volume matrix"""
    return df.pivot(index='date', columns='symbol', values='quote_volume')


def calculate_returns(price_df: pd.DataFrame, periods: int = 1) -> pd.DataFrame:
    """Calculate percentage returns"""
    return price_df.pct_change(periods=periods)


def calculate_log_returns(price_df: pd.DataFrame, periods: int = 1) -> pd.DataFrame:
    """Calculate log returns (more suitable for ML)"""
    return np.log(price_df / price_df.shift(periods))


def calculate_volatility(returns_df: pd.DataFrame, window: int = 30) -> pd.DataFrame:
    """Calculate rolling volatility"""
    return returns_df.rolling(window=window).std()


def calculate_momentum(price_df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    """Calculate momentum (ROC)"""
    return (price_df - price_df.shift(window)) / price_df.shift(window)


def calculate_rsi(price_df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    """Calculate Relative Strength Index"""
    delta = price_df.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calculate_sharpe_ratio(returns_df: pd.DataFrame, window: int = 30, 
                          risk_free_rate: float = 0.0) -> pd.DataFrame:
    """Calculate rolling Sharpe ratio"""
    mean_return = returns_df.rolling(window=window).mean()
    std_return = returns_df.rolling(window=window).std()
    return (mean_return - risk_free_rate / 252) / std_return


def generate_simple_weights(price_df: pd.DataFrame, volume_df: pd.DataFrame,
                           momentum_window: int = 14, 
                           volatility_window: int = 30) -> pd.Series:
    """
    Generate simple trading weights based on momentum and volatility
    
    Args:
        price_df: Price matrix
        volume_df: Volume matrix
        momentum_window: Window for momentum calculation
        volatility_window: Window for volatility calculation
    
    Returns:
        Series with portfolio weights (long/short)
    """
    # Calculate features
    returns = calculate_returns(price_df)
    momentum = calculate_momentum(price_df, window=momentum_window)
    volatility = calculate_volatility(returns, window=volatility_window)
    
    # Get latest values
    latest_momentum = momentum.iloc[-1]
    latest_volatility = volatility.iloc[-1]
    latest_volume = volume_df.iloc[-1]
    
    # Normalize momentum
    momentum_z = (latest_momentum - latest_momentum.mean()) / latest_momentum.std()
    
    # Calculate raw weights: momentum / volatility, weighted by volume
    raw_weights = momentum_z / latest_volatility
    
    # Apply volume filter (only trade liquid assets)
    volume_threshold = latest_volume.quantile(0.3)
    raw_weights = raw_weights.where(latest_volume >= volume_threshold, 0)
    
    # Normalize to sum to 0 (market neutral) or scale for long-short
    weights = raw_weights / raw_weights.abs().sum()
    
    return weights


def main():
    """Main example function"""
    
    print("=" * 70)
    print("BINANCE EOD DATA - ML PREPROCESSING EXAMPLE")
    print("=" * 70)
    
    # Load data
    print("\n1. Loading data...")
    df = load_data()
    
    print(f"   Total records: {len(df):,}")
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"   Unique symbols: {df['symbol'].nunique()}")
    
    # Filter for liquid USDT pairs
    print("\n2. Filtering for liquid USDT pairs...")
    df_filtered = filter_liquid_pairs(df, min_avg_volume=1_000_000, quote_currency='USDT')
    
    print(f"   Remaining symbols: {df_filtered['symbol'].nunique()}")
    
    # Create matrices
    print("\n3. Creating price and volume matrices...")
    price_matrix = create_price_matrix(df_filtered)
    volume_matrix = create_volume_matrix(df_filtered)
    
    print(f"   Price matrix shape: {price_matrix.shape}")
    print(f"   Date range: {price_matrix.index.min()} to {price_matrix.index.max()}")
    
    # Calculate features
    print("\n4. Calculating features...")
    returns_1d = calculate_returns(price_matrix, periods=1)
    returns_7d = calculate_returns(price_matrix, periods=7)
    log_returns = calculate_log_returns(price_matrix, periods=1)
    volatility = calculate_volatility(returns_1d, window=30)
    momentum = calculate_momentum(price_matrix, window=14)
    rsi = calculate_rsi(price_matrix, window=14)
    sharpe = calculate_sharpe_ratio(returns_1d, window=30)
    
    print(f"   ✓ Returns (1-day, 7-day)")
    print(f"   ✓ Log returns")
    print(f"   ✓ Volatility (30-day)")
    print(f"   ✓ Momentum (14-day)")
    print(f"   ✓ RSI (14-day)")
    print(f"   ✓ Sharpe Ratio (30-day)")
    
    # Generate weights
    print("\n5. Generating portfolio weights...")
    weights = generate_simple_weights(price_matrix, volume_matrix)
    
    # Display results
    print("\n" + "=" * 70)
    print("PORTFOLIO WEIGHTS (Top 10 Long / Top 10 Short)")
    print("=" * 70)
    
    # Top 10 long positions
    long_weights = weights[weights > 0].sort_values(ascending=False).head(10)
    print("\nLONG Positions:")
    for symbol, weight in long_weights.items():
        print(f"  {symbol:15s}: {weight:+.4f} ({weight*100:+.2f}%)")
    
    # Top 10 short positions
    short_weights = weights[weights < 0].sort_values().head(10)
    print("\nSHORT Positions:")
    for symbol, weight in short_weights.items():
        print(f"  {symbol:15s}: {weight:+.4f} ({weight*100:+.2f}%)")
    
    # Summary statistics
    print("\n" + "=" * 70)
    print("PORTFOLIO STATISTICS")
    print("=" * 70)
    print(f"Total long exposure:  {weights[weights > 0].sum():+.4f} ({weights[weights > 0].sum()*100:+.2f}%)")
    print(f"Total short exposure: {weights[weights < 0].sum():+.4f} ({weights[weights < 0].sum()*100:+.2f}%)")
    print(f"Net exposure:         {weights.sum():+.4f} ({weights.sum()*100:+.2f}%)")
    print(f"Number of positions:  {(weights != 0).sum()}")
    print(f"Long positions:       {(weights > 0).sum()}")
    print(f"Short positions:      {(weights < 0).sum()}")
    
    # Feature summary
    print("\n" + "=" * 70)
    print("LATEST FEATURE SUMMARY (Top 5 by momentum)")
    print("=" * 70)
    
    top_momentum = momentum.iloc[-1].nlargest(5)
    for symbol in top_momentum.index:
        print(f"\n{symbol}:")
        print(f"  Price:      ${price_matrix[symbol].iloc[-1]:,.2f}")
        print(f"  Return 1D:  {returns_1d[symbol].iloc[-1]*100:+.2f}%")
        print(f"  Return 7D:  {returns_7d[symbol].iloc[-1]*100:+.2f}%")
        print(f"  Momentum:   {momentum[symbol].iloc[-1]*100:+.2f}%")
        print(f"  Volatility: {volatility[symbol].iloc[-1]*100:.2f}%")
        print(f"  RSI:        {rsi[symbol].iloc[-1]:.1f}")
        print(f"  Sharpe:     {sharpe[symbol].iloc[-1]:.2f}")
    
    print("\n" + "=" * 70)
    print("Ready for ML model training!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Build feature matrix from calculated indicators")
    print("2. Train your ML model (Random Forest, XGBoost, Neural Network, etc.)")
    print("3. Generate predictions for expected returns")
    print("4. Optimize portfolio weights based on predictions")
    print("5. Backtest your strategy")
    print("6. Deploy for live trading")


if __name__ == "__main__":
    main()
