# Crypto Market Data Collector v2

A Python-based collector that gathers historical cryptocurrency data using **Binance** for trading pair discovery and **CoinGecko** for price, volume, and market cap data.

## Features

✅ **365 Days Historical Data** - Price, Volume, and Market Cap from CoinGecko  
✅ **All Binance Spot Pairs** - Automatically discovers USDT trading pairs  
✅ **Daily Updates** - Efficiently update with latest EOD data  
✅ **Free API** - Uses CoinGecko's free tier (30 calls/min, 10k/month)  
✅ **Rate Limiting** - Automatic rate limiting to respect API limits  
✅ **Symbol Mapping** - Smart mapping between Binance and CoinGecko symbols  
✅ **Progress Checkpoints** - Saves progress every 50 pairs  

## Data Sources

1. **Binance API** → Discovery of all active USDT trading pairs
2. **CoinGecko API** → Historical Price, Volume, and Market Cap data

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install requests pandas
```

### 2. Create Data Directory

```bash
mkdir data
```

## Usage

### Collect 365 Days of Historical Data

This is the **first step** - run this once to build your historical dataset:

```bash
python crypto_collector_v2.py historical
```

To specify a different number of days (max 365 for free tier):
```bash
python crypto_collector_v2.py historical 180
```

**Expected Runtime:** 
- ~200-300 pairs typically available
- ~30 API calls per minute (CoinGecko limit)
- Total time: ~2-3 hours for full collection

**What happens:**
1. Fetches all USDT trading pairs from Binance
2. Maps each base asset to CoinGecko coin ID
3. Fetches 365 days of historical data for each coin
4. Saves progress every 50 pairs (checkpoints)
5. Outputs to `data/crypto_data.csv`

### Daily Data Update

Run this **daily** to keep your dataset current:

```bash
python crypto_collector_v2.py update
```

**What happens:**
1. Loads existing `data/crypto_data.csv`
2. Fetches the latest day's data for all pairs
3. Appends new data (removing duplicates)
4. Updates the same CSV file

**Recommended:** Set up a cron job or scheduled task to run this automatically.

## Automation

### Linux/Mac - Cron Job

Add to your crontab (`crontab -e`):

```bash
# Run daily at 1:00 AM
0 1 * * * cd /path/to/project && /usr/bin/python3 crypto_collector_v2.py update >> logs/update.log 2>&1
```

### Windows - Task Scheduler

Create a batch file `daily_update.bat`:

```batch
@echo off
cd C:\path\to\project
python crypto_collector_v2.py update >> logs\update.log 2>&1
```

Then create a scheduled task to run this batch file daily.

### Python Script for Daily Automation

Create `run_daily_update.py`:

```python
import schedule
import time
from crypto_collector_v2 import CryptoDataCollector

def daily_update():
    collector = CryptoDataCollector(output_dir='data')
    collector.collect_daily_update()

# Schedule daily update at 1:00 AM
schedule.every().day.at("01:00").do(daily_update)

print("Scheduler started. Daily updates will run at 1:00 AM.")
while True:
    schedule.run_pending()
    time.sleep(60)
```

Install schedule package:
```bash
pip install schedule
```

Run the scheduler:
```bash
python run_daily_update.py
```

## Output Format

Data is saved to `data/crypto_data.csv`:

```csv
date,symbol,base_asset,coingecko_id,price,volume,market_cap,timestamp
2024-01-01,BTCUSDT,BTC,bitcoin,42500.50,28500000000,832500000000,1704067200000
2024-01-01,ETHUSDT,ETH,ethereum,2250.75,15200000000,270000000000,1704067200000
```

**Columns:**
- `date`: Trading date (YYYY-MM-DD)
- `symbol`: Binance trading pair (e.g., BTCUSDT)
- `base_asset`: Base cryptocurrency (e.g., BTC)
- `coingecko_id`: CoinGecko coin ID (e.g., bitcoin)
- `price`: USD price from CoinGecko
- `volume`: 24h trading volume in USD
- `market_cap`: Market capitalization in USD
- `timestamp`: Unix timestamp in milliseconds

## CoinGecko API Limitations

**Free Tier Limits:**
- 30 API calls per minute
- 10,000 API calls per month
- Historical data limited to 365 days

**The script automatically handles:**
- Rate limiting (waits when limit reached)
- HTTP 429 responses (waits 60 seconds and retries)
- Checkpointing (saves progress to avoid re-fetching)

**Monthly Usage Estimation:**
- Initial collection: ~200-300 API calls
- Daily updates: ~200-300 API calls per day
- Monthly total: ~6,000-9,000 calls (within free tier)

## Symbol Mapping

The script creates a cache file `data/symbol_mapping.json` that maps Binance symbols to CoinGecko IDs:

```json
{
  "BTC": "bitcoin",
  "ETH": "ethereum",
  "BNB": "binancecoin",
  "DOGE": "dogecoin"
}
```

This cache is automatically saved and reused to avoid redundant API calls.

## Handling Failures

**If a pair fails to map:**
- The script logs a warning and skips it
- Failed pairs are listed at the end
- You can manually add mappings to `symbol_mapping.json`

**If data collection is interrupted:**
- Checkpoint files are saved every 50 pairs: `checkpoint_50_crypto_data.csv`, `checkpoint_100_crypto_data.csv`, etc.
- Restart the script and it will resume from the beginning (using cached mappings)

**If you hit rate limits:**
- The script automatically waits and retries
- For persistent issues, consider upgrading to CoinGecko paid tier

## Advanced Usage

### Custom Date Range

To get only recent data:
```bash
python crypto_collector_v2.py historical 90  # Last 90 days
```

### Using as a Python Module

```python
from crypto_collector_v2 import CryptoDataCollector

# Initialize collector
collector = CryptoDataCollector(output_dir='my_data')

# Collect 180 days of data
collector.collect_historical_data(days=180)

# Daily update
collector.collect_daily_update()
```

### Loading Data

```python
import pandas as pd

# Load data
df = pd.read_csv('data/crypto_data.csv')

# Convert date to datetime
df['date'] = pd.to_datetime(df['date'])

# Filter for specific coin
btc_data = df[df['base_asset'] == 'BTC']

# Get latest prices
latest = df[df['date'] == df['date'].max()]
```

## Troubleshooting

**Issue: "No Binance pairs found"**
- Check internet connection
- Binance API might be temporarily down
- Try again in a few minutes

**Issue: "Rate limited by CoinGecko"**
- Script will automatically wait 60 seconds
- If persistent, you may have hit monthly limit
- Consider upgrading to paid tier or waiting until next month

**Issue: "Could not map [symbol] to CoinGecko ID"**
- Some newer or less common tokens may not be on CoinGecko
- Manually add mapping to `data/symbol_mapping.json`
- Or ignore - data will be collected for available coins

**Issue: "No existing data file found"**
- Run historical collection first: `python crypto_collector_v2.py historical`
- Cannot run `update` without existing data

## Project Structure

```
.
├── crypto_collector_v2.py    # Main collector script
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── data/                      # Output directory
│   ├── crypto_data.csv        # Main data file
│   ├── symbol_mapping.json    # Symbol mapping cache
│   └── checkpoint_*.csv       # Progress checkpoints
└── logs/                      # Log files (if using automation)
```

## Data Quality

**Pros:**
- ✅ Official CoinGecko data (trusted by millions)
- ✅ Includes market cap (not available from Binance)
- ✅ Aggregated across 1000+ exchanges
- ✅ Free for 365 days of history

**Cons:**
- ⚠️ Daily granularity only (no intraday data)
- ⚠️ Limited to 365 days for free tier
- ⚠️ Some obscure tokens may not be available
- ⚠️ Rate limits can slow initial collection

## Upgrading to Paid Tier

If you need more data, consider [CoinGecko's paid plans](https://www.coingecko.com/en/api/pricing):

- **Analyst Plan ($129/mo)**: 500 calls/min, 500k/month, all historical data
- **Lite Plan ($429/mo)**: 500 calls/min, 5M/month, priority support
- **Pro Plan ($899/mo)**: 1000 calls/min, 30M/month

Benefits:
- No 365-day limit
- Higher rate limits (faster collection)
- More historical data
- Priority support

## License

MIT License - Use freely for personal or commercial projects.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review CoinGecko API docs: https://docs.coingecko.com/
3. Review Binance API docs: https://binance-docs.github.io/apidocs/spot/en/

## Changelog

**v2.0** (Current)
- Switched from Binance OHLCV to CoinGecko historical data
- Added market cap data
- Simplified architecture (single data source)
- Improved rate limiting
- Added symbol mapping cache
- Added progress checkpoints

**v1.0** (Previous)
- Binance OHLCV + CoinGecko current market cap
- Required complex daily merging
- No historical market cap
