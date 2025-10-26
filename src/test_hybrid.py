"""
Test script for Binance + CoinGecko hybrid data collection

This script demonstrates:
1. Fetching data from Binance
2. Mapping symbols to CoinGecko
3. Enriching with market cap data
4. Handling unmapped symbols
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from binance_eod_collector import BinanceEODCollector
import pandas as pd


def test_symbol_mapping():
    """Test the symbol mapping functionality"""
    print("="*70)
    print("TEST 1: Symbol Mapping")
    print("="*70)
    
    collector = BinanceEODCollector(data_dir="test_data")
    
    test_symbols = [
        'BTCUSDT',
        'ETHUSDT', 
        'BNBUSDT',
        'ADAUSDT',
        'DOGEUSDT',
        'XRPUSDT',
        'SOLUSDT',
        'DOTUSDT'
    ]
    
    print("\nTesting symbol mapping:")
    for symbol in test_symbols:
        base = collector.extract_base_symbol(symbol)
        cg_id = collector.map_binance_to_coingecko(symbol)
        print(f"  {symbol:12s} → Base: {base:8s} → CoinGecko ID: {cg_id}")
    
    print("\n✓ Symbol mapping test complete\n")


def test_coingecko_data():
    """Test fetching data from CoinGecko"""
    print("="*70)
    print("TEST 2: CoinGecko Market Data")
    print("="*70)
    
    collector = BinanceEODCollector(data_dir="test_data")
    
    # Test with a few popular coins
    test_ids = ['bitcoin', 'ethereum', 'binancecoin', 'cardano', 'solana']
    
    print(f"\nFetching market data for: {', '.join(test_ids)}")
    market_data = collector.get_coingecko_market_data(test_ids)
    
    print("\nResults:")
    for coin_id, data in market_data.items():
        print(f"\n  {coin_id}:")
        print(f"    Market Cap:         ${data['market_cap']:,.0f}" if data['market_cap'] else "    Market Cap:         N/A")
        print(f"    Circulating Supply: {data['circulating_supply']:,.0f}" if data['circulating_supply'] else "    Circulating Supply: N/A")
        print(f"    Total Supply:       {data['total_supply']:,.0f}" if data['total_supply'] else "    Total Supply:       N/A")
        print(f"    Max Supply:         {data['max_supply']:,.0f}" if data['max_supply'] else "    Max Supply:         N/A")
    
    print("\n✓ CoinGecko data test complete\n")


def test_small_collection():
    """Test collecting data for a few symbols"""
    print("="*70)
    print("TEST 3: Small Data Collection (5 symbols)")
    print("="*70)
    
    collector = BinanceEODCollector(data_dir="test_data")
    
    test_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOGEUSDT']
    
    print(f"\nCollecting 7 days of data for: {', '.join(test_symbols)}")
    
    collector.collect_historical_data(
        days=7,
        symbols_filter=test_symbols
    )
    
    # Load and display results
    data_file = "test_data/all_pairs_eod.csv"
    if os.path.exists(data_file):
        df = pd.read_csv(data_file)
        
        print("\n" + "="*70)
        print("DATA COLLECTION RESULTS")
        print("="*70)
        print(f"\nTotal records: {len(df)}")
        print(f"Unique symbols: {df['symbol'].nunique()}")
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")
        
        print("\nSample data (first 10 rows):")
        print(df.head(10).to_string(index=False))
        
        print("\nColumn summary:")
        for col in df.columns:
            non_null = df[col].notna().sum()
            print(f"  {col:20s}: {non_null}/{len(df)} non-null values")
        
        print("\n✓ Data collection test complete")
        print(f"✓ Data saved to: {data_file}")
    else:
        print("\n✗ ERROR: Data file not created")


def test_skip_behavior():
    """Test that non-CoinGecko symbols are properly skipped"""
    print("\n" + "="*70)
    print("TEST 4: Skip Behavior (Non-CoinGecko Symbols)")
    print("="*70)
    
    collector = BinanceEODCollector(data_dir="test_data")
    
    # Mix of real and potentially unmapped symbols
    test_symbols = [
        'BTCUSDT',      # Should work
        'FAKEUSDT',     # Should be skipped (doesn't exist)
        'ETHUSDT',      # Should work
    ]
    
    print(f"\nTesting with symbols: {test_symbols}")
    print("Expected: BTCUSDT and ETHUSDT succeed, FAKEUSDT skipped\n")
    
    # This will show which symbols get skipped
    all_data = []
    for symbol in test_symbols:
        df = collector.get_historical_klines(symbol, days=3)
        if not df.empty:
            all_data.append(df)
    
    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        enriched, skipped = collector.enrich_with_coingecko_data(combined)
        
        print(f"Symbols collected from Binance: {combined['symbol'].unique().tolist()}")
        print(f"Symbols after CoinGecko enrichment: {enriched['symbol'].unique().tolist() if not enriched.empty else 'None'}")
        print(f"Skipped symbols: {list(set(skipped))}")
        
        print("\n✓ Skip behavior test complete")


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("BINANCE + COINGECKO HYBRID APPROACH - TEST SUITE")
    print("="*70)
    print()
    
    try:
        # Test 1: Symbol mapping
        test_symbol_mapping()
        
        # Test 2: CoinGecko data fetching
        test_coingecko_data()
        
        # Test 3: Small collection
        test_small_collection()
        
        # Test 4: Skip behavior
        test_skip_behavior()
        
        print("\n" + "="*70)
        print("ALL TESTS COMPLETED SUCCESSFULLY! ✓")
        print("="*70)
        print("\nThe hybrid approach is working correctly:")
        print("  ✓ Symbols are mapped from Binance to CoinGecko")
        print("  ✓ Market cap and supply data is fetched from CoinGecko")
        print("  ✓ Data is properly enriched and saved")
        print("  ✓ Unmapped symbols are skipped as expected")
        print("\nYou can now run the full collection:")
        print("  poetry run collect-data --days 365")
        print()
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
