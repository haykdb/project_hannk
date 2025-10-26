# Hybrid Data Collection Approach

## Overview

This collector uses a **hybrid approach** combining two data sources:

### 1. Binance API (Primary Data Source)
**Purpose**: OHLCV trading data  
**Provides**:
- Open, High, Low, Close prices
- Trading volume (base asset)
- Quote volume (USDT, BTC, etc.)
- Number of trades
- Historical and current data for ALL Binance Spot pairs

**Why Binance?**
- Most accurate trading data directly from the exchange
- Real-time updates
- Complete historical data
- No API key required for public market data

### 2. CoinGecko API (Market Cap Data Source)
**Purpose**: Market capitalization and supply metrics  
**Provides**:
- Market Cap (USD)
- Circulating Supply
- Total Supply
- Max Supply

**Why CoinGecko?**
- Comprehensive cryptocurrency database (13,000+ coins)
- Calculates accurate market cap using circulating supply
- Free tier: 10,000 calls/month
- No API key required

## How It Works

### Symbol Mapping Process

1. **Fetch Binance Pairs**: Get all active Spot trading pairs (e.g., BTCUSDT, ETHBTC)

2. **Extract Base Asset**: Parse the trading pair to get base symbol
   - `BTCUSDT` → `BTC`
   - `ETHBTC` → `ETH`
   - `BNBBUSD` → `BNB`

3. **Map to CoinGecko**: Match base symbol to CoinGecko ID
   - `BTC` → `bitcoin`
   - `ETH` → `ethereum`
   - `BNB` → `binancecoin`

4. **Fetch Market Data**: Get market cap and supply from CoinGecko

5. **Enrich Data**: Combine Binance OHLCV with CoinGecko market metrics

6. **Skip Unmapped Pairs**: If a pair cannot be matched to CoinGecko, it's excluded

### Example Flow

```
Input: BTCUSDT (Binance)
  ↓
Extract: BTC
  ↓
Map: BTC → bitcoin (CoinGecko ID)
  ↓
Fetch: Market cap, circulating supply from CoinGecko
  ↓
Combine: Binance OHLCV + CoinGecko market data
  ↓
Output: Complete record with all metrics
```

## Data Output Format

### Complete Record Example

```csv
date,symbol,open,high,low,close,volume,quote_volume,trades,market_cap,circulating_supply,total_supply,max_supply
2024-01-01,BTCUSDT,42500.00,43000.00,42000.00,42800.00,1500.5,64200000.0,125000,832500000000,19845000,19845000,21000000
```

### Column Descriptions

**From Binance:**
- `date`: Trading date (YYYY-MM-DD)
- `symbol`: Trading pair (e.g., BTCUSDT)
- `open`: Opening price
- `high`: Highest price
- `low`: Lowest price
- `close`: Closing price
- `volume`: Base asset volume
- `quote_volume`: Quote asset volume
- `trades`: Number of trades

**From CoinGecko:**
- `market_cap`: Market capitalization in USD (= price × circulating_supply)
- `circulating_supply`: Coins in circulation
- `total_supply`: Total minted supply
- `max_supply`: Maximum possible supply (null if unlimited)

## Symbol Filtering

### Pairs Included
✅ All Binance Spot pairs that exist on CoinGecko  
✅ Major pairs: BTCUSDT, ETHUSDT, BNBUSDT, etc.  
✅ Altcoin pairs with CoinGecko listings  

### Pairs Excluded (Automatically Skipped)
❌ Pairs not listed on CoinGecko  
❌ Very new listings without CoinGecko data  
❌ Leveraged tokens (BTCUP, BTCDOWN, etc.)  
❌ Some regional or niche pairs  

### Expected Coverage
Typically **80-90%** of Binance Spot pairs are matched:
- ~2,500 total Binance Spot pairs
- ~2,000-2,250 pairs matched to CoinGecko
- ~250-500 pairs skipped

The collector logs all skipped pairs for transparency.

## Rate Limits

### Binance API
- **Limit**: 1,200 requests/minute (weight-based)
- **Our usage**: 0.5s delay between requests
- **Impact**: ~2 requests/second = safe margin

### CoinGecko API (Free Tier)
- **Limit**: 30 calls/minute, 10,000 calls/month
- **Our usage**: 2s delay between batch requests
- **Optimization**: Batch processing (up to 250 coins per request)
- **Impact**: Efficient for daily updates

## Advantages of Hybrid Approach

### 1. **Data Quality**
- Binance: Most accurate exchange data
- CoinGecko: Verified market cap calculations

### 2. **Comprehensive Coverage**
- Binance: All trading pairs on the exchange
- CoinGecko: 13,000+ cryptocurrency projects

### 3. **Cost Efficiency**
- Both APIs offer generous free tiers
- No paid subscriptions required
- Suitable for individual researchers and small teams

### 4. **ML-Ready Data**
- Complete feature set for trading models
- Price, volume, market cap, supply metrics
- Daily granularity for time-series analysis

## Common Use Cases

### Portfolio Optimization
```python
# Use market cap for position sizing
weights = market_cap / market_cap.sum()
```

### Market Cap Weighted Index
```python
# Create custom crypto index
index_value = (prices * market_cap_weights).sum()
```

### Liquidity Filtering
```python
# Filter for liquid, large-cap coins
liquid_pairs = df[df['market_cap'] > 1_000_000_000]
```

### Supply Analysis
```python
# Calculate inflation rate
inflation = (total_supply - circulating_supply) / circulating_supply
```

## Troubleshooting

### "Symbol not found on CoinGecko"
**Cause**: New listing or delisted coin  
**Solution**: Normal behavior, pair is automatically skipped

### "CoinGecko rate limit exceeded"
**Cause**: Too many requests  
**Solution**: 
- Increase sleep time (change from 2s to 5s)
- Reduce batch size
- Wait for rate limit reset (1 minute)

### "Market cap is None/NaN"
**Cause**: CoinGecko doesn't have supply data  
**Solution**: Pair is filtered out automatically

## Future Enhancements

Possible improvements (not currently implemented):
- Add backup data source (CoinMarketCap, CoinPaprika)
- Cache CoinGecko data to reduce API calls
- Support for custom symbol mappings
- Historical market cap data (requires paid CoinGecko plan)

---

**Result**: Clean, ML-ready dataset combining the best of both platforms! 🎯
