# Crypto Data Collector v2 - Project Summary

## 🎯 What This Does

A complete solution for collecting historical cryptocurrency market data using:
- **Binance API** for discovering trading pairs
- **CoinGecko API** for 365 days of historical price, volume, and market cap data
- Automatic daily updates to keep your dataset current

## 📦 What You're Getting

### Core Scripts

1. **crypto_collector_v2.py** - Main data collector
   - Fetches all USDT trading pairs from Binance
   - Maps symbols to CoinGecko IDs
   - Downloads 365 days of historical data
   - Handles daily updates
   - Includes rate limiting, error handling, checkpointing

2. **run_daily_scheduler.py** - Automated daily updates
   - Runs continuously
   - Updates data at 1:00 AM daily
   - Logs all activity
   - Can run immediately with `--now` flag

3. **example_analysis.py** - Data analysis examples
   - Load and analyze collected data
   - Calculate returns
   - Generate charts
   - Show statistics

4. **test_collector.py** - Test script
   - Verify APIs are working
   - Test all functionality
   - Quick validation

### Documentation

1. **README.md** - Complete documentation
   - Detailed setup instructions
   - API limitations and best practices
   - Troubleshooting guide
   - Advanced usage examples

2. **QUICKSTART.md** - 5-minute quick start
   - Fast setup guide
   - Common commands
   - Essential information

3. **requirements.txt** - Python dependencies
   - All required packages
   - Version specifications

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Collect historical data (first time only)
python crypto_collector_v2.py historical

# 3. Set up daily updates
python run_daily_scheduler.py
```

## 📊 Output Data Format

**File:** `data/crypto_data.csv`

```csv
date,symbol,base_asset,coingecko_id,price,volume,market_cap,timestamp
2024-01-01,BTCUSDT,BTC,bitcoin,42500.50,28500000000,832500000000,1704067200000
2024-01-01,ETHUSDT,ETH,ethereum,2250.75,15200000000,270000000000,1704067200000
```

### Columns Explained

- **date**: Trading date (YYYY-MM-DD)
- **symbol**: Binance trading pair (e.g., BTCUSDT)
- **base_asset**: Base cryptocurrency (e.g., BTC)
- **coingecko_id**: CoinGecko coin ID (e.g., bitcoin)
- **price**: USD price
- **volume**: 24h trading volume in USD
- **market_cap**: Market capitalization in USD
- **timestamp**: Unix timestamp in milliseconds

## ✨ Key Features

✅ **Free Historical Data** - 365 days of price, volume, market cap  
✅ **All Major Coins** - 200-300+ USDT trading pairs  
✅ **Automatic Updates** - Daily data refresh  
✅ **Rate Limit Handling** - Respects CoinGecko's 30 calls/min limit  
✅ **Progress Checkpoints** - Resume interrupted downloads  
✅ **Symbol Mapping Cache** - Avoids redundant API calls  
✅ **Error Recovery** - Robust error handling and retries  
✅ **Ready for ML** - Clean CSV format for model training  

## 🎓 Usage Examples

### Collect Historical Data
```bash
# Get 365 days (maximum for free tier)
python crypto_collector_v2.py historical

# Get only 90 days
python crypto_collector_v2.py historical 90
```

### Daily Updates
```bash
# Manual update
python crypto_collector_v2.py update

# Automated scheduler (runs at 1:00 AM daily)
python run_daily_scheduler.py

# Test immediately
python run_daily_scheduler.py --now
```

### Load and Analyze Data
```python
import pandas as pd

# Load data
df = pd.read_csv('data/crypto_data.csv')
df['date'] = pd.to_datetime(df['date'])

# Get Bitcoin data
btc = df[df['base_asset'] == 'BTC']

# Calculate 30-day return
btc_30d = btc.tail(31)
return_pct = (btc_30d.iloc[-1]['price'] / btc_30d.iloc[0]['price'] - 1) * 100
print(f"BTC 30-day return: {return_pct:.2f}%")
```

## ⏱️ Expected Timeline

### Initial Collection
- **Pairs:** ~200-300 USDT trading pairs
- **API Calls:** ~200-300 (1 per coin)
- **Rate Limit:** 30 calls/minute
- **Duration:** 2-3 hours

### Daily Updates  
- **API Calls:** ~200-300 (1 per coin)
- **Duration:** ~10-15 minutes

### Monthly Usage
- Initial: ~200-300 calls
- Daily: ~200-300 calls × 30 days = 6,000-9,000 calls
- **Total:** ~6,200-9,300 calls (within 10k free tier limit)

## 🔧 Technical Details

### CoinGecko API Free Tier
- **Rate Limit:** 30 calls per minute
- **Monthly Cap:** 10,000 calls
- **Historical Data:** Maximum 365 days
- **No API Key Required:** Uses public endpoints

### Data Sources Comparison

| Feature | Binance API | CoinGecko API |
|---------|------------|---------------|
| Purpose | Trading pairs discovery | Historical market data |
| Cost | Free | Free (with limits) |
| Data Depth | Real-time only | 365 days historical |
| Market Cap | ❌ No | ✅ Yes |
| Rate Limits | 1200/min | 30/min |
| Used For | Finding what to track | Getting the actual data |

## 📁 Project Structure

```
crypto-data-collector/
├── crypto_collector_v2.py      # Main collector
├── run_daily_scheduler.py      # Automation script  
├── example_analysis.py         # Analysis examples
├── test_collector.py          # Test script
├── requirements.txt           # Dependencies
├── README.md                  # Full documentation
├── QUICKSTART.md              # Quick start guide
├── data/                      # Output directory
│   ├── crypto_data.csv        # Main data file
│   ├── symbol_mapping.json    # Cached mappings
│   └── checkpoint_*.csv       # Progress saves
└── logs/                      # Log files
    └── scheduler.log
```

## 🔄 Workflow

```
1. DISCOVERY (Binance)
   Get all USDT trading pairs
   ↓
2. MAPPING (CoinGecko)
   Map Binance symbols to CoinGecko IDs
   ↓
3. HISTORICAL COLLECTION (CoinGecko)
   Fetch 365 days of data for each coin
   ↓
4. DAILY UPDATES (CoinGecko)
   Add latest day's data each day
```

## 💡 Use Cases

### Trading & Investment
- Backtest trading strategies
- Analyze market trends
- Track portfolio performance
- Identify correlations

### Machine Learning
- Train prediction models
- Feature engineering
- Time series analysis
- Market classification

### Research & Analysis
- Market cap evolution
- Volume analysis
- Price discovery
- Comparative studies

## ⚠️ Limitations

### CoinGecko Free Tier
- ❌ Limited to 365 days of historical data
- ❌ Daily granularity only (no intraday)
- ❌ 30 API calls per minute rate limit
- ❌ Some newer/obscure tokens may not be available

### Solutions
- ✅ For more history: Upgrade to paid tier ($129/mo for unlimited history)
- ✅ For intraday data: Use Binance klines or other sources
- ✅ For more tokens: Use additional data sources
- ✅ For higher limits: CoinGecko paid plans available

## 🆙 Upgrade Paths

If you need more than the free tier offers:

### CoinGecko Paid Plans
- **Analyst ($129/mo):** Unlimited history, 500 calls/min
- **Lite ($429/mo):** 5M calls/month, priority support
- **Pro ($899/mo):** 30M calls/month, dedicated support

### Alternative Approaches
1. **Multiple Free Accounts:** Rotate between accounts (against ToS)
2. **Complementary Sources:** Combine CoinGecko with CoinCap, CoinLore
3. **Exchange APIs:** Use Binance/Coinbase for specific pairs
4. **Commercial APIs:** CoinMarketCap, Kaiko, CryptoCompare

## 📚 Additional Resources

- **CoinGecko API Docs:** https://docs.coingecko.com/
- **Binance API Docs:** https://binance-docs.github.io/apidocs/spot/en/
- **Pandas Guide:** https://pandas.pydata.org/docs/
- **Python Schedule:** https://schedule.readthedocs.io/

## 🤝 Support

### Common Issues
1. **Rate limits** - Script handles automatically
2. **Missing symbols** - Some tokens not on CoinGecko
3. **Network errors** - Script retries automatically

### Getting Help
- Check README.md for detailed troubleshooting
- Review logs in `logs/` directory
- Test with `test_collector.py`

## 🎉 Next Steps

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Run test: `python test_collector.py`
3. ✅ Collect data: `python crypto_collector_v2.py historical`
4. ✅ Set up automation: `python run_daily_scheduler.py`
5. ✅ Start building your ML models!

---

**Version:** 2.0  
**Last Updated:** October 2025  
**License:** MIT  

Happy trading! 🚀📈
