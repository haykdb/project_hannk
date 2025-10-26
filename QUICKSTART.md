# Quick Start Guide

Get up and running with the Crypto Data Collector in 5 minutes!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Collect Historical Data (One-Time Setup)

```bash
python crypto_collector_v2.py historical
```

⏱️ **This will take 2-3 hours** to collect 365 days of data for ~200-300 trading pairs.

The script will:
- ✅ Fetch all USDT pairs from Binance
- ✅ Map symbols to CoinGecko coin IDs
- ✅ Download 365 days of price, volume, and market cap data
- ✅ Save to `data/crypto_data.csv`
- ✅ Create checkpoints every 50 pairs

**You can safely stop and restart** - symbol mappings are cached!

## Step 3: Run Daily Updates

### Option A: Manual Update
```bash
python crypto_collector_v2.py update
```

### Option B: Automated Scheduler
```bash
# Runs continuously, updates at 1:00 AM daily
python run_daily_scheduler.py
```

To test immediately:
```bash
python run_daily_scheduler.py --now
```

### Option C: Cron Job (Linux/Mac)
```bash
# Edit crontab
crontab -e

# Add this line (updates at 1:00 AM daily)
0 1 * * * cd /path/to/project && python3 crypto_collector_v2.py update
```

## Step 4: Analyze Your Data

```bash
python example_analysis.py
```

This will:
- 📊 Show top 10 coins by market cap
- 📈 Calculate 30-day returns for BTC, ETH, BNB
- 📉 Generate price history charts
- 📊 Display statistics

## Understanding Your Data

Your data file `data/crypto_data.csv` contains:

```csv
date,symbol,base_asset,coingecko_id,price,volume,market_cap,timestamp
2024-01-01,BTCUSDT,BTC,bitcoin,42500.50,28500000000,832500000000,1704067200000
```

**Quick Python Example:**
```python
import pandas as pd

# Load data
df = pd.read_csv('data/crypto_data.csv')
df['date'] = pd.to_datetime(df['date'])

# Get Bitcoin prices
btc = df[df['base_asset'] == 'BTC']

# Get latest prices
latest = df[df['date'] == df['date'].max()]

# Calculate returns
btc_returns = btc.set_index('date')['price'].pct_change()
```

## Common Commands

```bash
# Collect 365 days of historical data
python crypto_collector_v2.py historical

# Collect only 90 days
python crypto_collector_v2.py historical 90

# Daily update
python crypto_collector_v2.py update

# Run scheduler (updates at 1:00 AM daily)
python run_daily_scheduler.py

# Test scheduler immediately
python run_daily_scheduler.py --now

# Analyze data
python example_analysis.py
```

## Troubleshooting

**"No data file found"**
→ Run historical collection first: `python crypto_collector_v2.py historical`

**"Rate limited by CoinGecko"**
→ Script will automatically wait and retry. This is normal.

**Script is slow**
→ CoinGecko free tier allows 30 calls/minute. Full collection takes 2-3 hours.

**Some pairs are missing**
→ Not all tokens are on CoinGecko. Check logs for failed mappings.

## Next Steps

1. ✅ Set up daily automation (cron or scheduler)
2. ✅ Build your ML models with the data
3. ✅ Customize analysis scripts
4. ✅ Consider upgrading to CoinGecko paid tier if you need:
   - More than 365 days of history
   - Faster collection (higher rate limits)
   - More API calls per month

## File Structure After Setup

```
your-project/
├── crypto_collector_v2.py      # Main collector
├── run_daily_scheduler.py      # Automation script
├── example_analysis.py         # Analysis examples
├── requirements.txt            # Dependencies
├── README.md                   # Full documentation
├── QUICKSTART.md              # This file
├── data/
│   ├── crypto_data.csv        # Your data! 🎉
│   ├── symbol_mapping.json    # Cached mappings
│   └── checkpoint_*.csv       # Progress saves
└── logs/
    └── scheduler.log          # Scheduler logs
```

## Support

- 📖 Full docs: See [README.md](README.md)
- 🔧 CoinGecko API: https://docs.coingecko.com/
- 🔧 Binance API: https://binance-docs.github.io/apidocs/spot/en/

Happy trading! 🚀
