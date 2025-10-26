"""
Test script to verify the crypto collector works correctly
"""

from binance_eod_collector.crypto_collector_v2 import CryptoDataCollector
import sys

def test_collector():
    """Run basic tests"""
    print("=" * 60)
    print("Testing Crypto Data Collector")
    print("=" * 60)
    
    # Test initialization
    print("\n1. Initializing collector...")
    try:
        collector = CryptoDataCollector(output_dir='test_data')
        print("   ✓ Collector initialized")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    # Test Binance API
    print("\n2. Testing Binance API...")
    try:
        pairs = collector.get_binance_spot_pairs()
        print(f"   ✓ Fetched {len(pairs)} Binance USDT pairs")
        if pairs:
            print(f"   Example pairs: {[p['symbol'] for p in pairs[:3]]}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    # Test CoinGecko coins list
    print("\n3. Testing CoinGecko API - Coins List...")
    try:
        coins = collector.get_coingecko_coins_list()
        print(f"   ✓ Fetched {len(coins)} CoinGecko coin mappings")
        print(f"   Example mappings:")
        for symbol in ['BTC', 'ETH', 'BNB']:
            if symbol in coins:
                print(f"     {symbol} -> {coins[symbol]}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    # Test symbol mapping
    print("\n4. Testing symbol mapping...")
    try:
        btc_id = collector.map_binance_to_coingecko('BTC', coins)
        print(f"   ✓ Mapped BTC to: {btc_id}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    # Test historical data fetch
    print("\n5. Testing historical data fetch (7 days)...")
    try:
        df = collector.get_historical_data('bitcoin', days=7)
        if not df.empty:
            print(f"   ✓ Fetched {len(df)} days of data")
            print(f"   Columns: {list(df.columns)}")
            latest = df.iloc[-1]
            print(f"   Latest data:")
            print(f"     Date: {latest['date']}")
            print(f"     Price: ${latest['price']:,.2f}")
            print(f"     Market Cap: ${latest['market_cap']/1e9:,.2f}B")
            print(f"     Volume: ${latest['volume']/1e9:,.2f}B")
        else:
            print("   ✗ No data returned")
            return False
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    print("\nYou can now run:")
    print("  python crypto_collector_v2.py historical")
    print("=" * 60)
    return True

if __name__ == '__main__':
    success = test_collector()
    sys.exit(0 if success else 1)
