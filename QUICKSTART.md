# Quick Start Guide

Get up and running with Binance EOD Data Collector in 5 minutes!

## Prerequisites

- Python 3.9 or higher
- Poetry (Python dependency manager)

### Install Poetry

**Linux/Mac/WSL:**
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**Windows (PowerShell):**
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

Or visit: https://python-poetry.org/docs/#installation

## Setup (2 minutes)

```bash
# Navigate to project directory
cd binance-eod-collector

# Run setup script
chmod +x setup.sh
./setup.sh

# Or manually:
poetry install
```

## Test Run (1 minute)

Test with a small sample of 10 symbols:

```bash
poetry run collect-data --max-symbols 10 --days 30
```

This will:
- Download data for 10 Binance Spot pairs
- Fetch last 30 days of historical data
- Save to `data/all_pairs_eod.csv`

## Full Collection (20-30 minutes)

Collect ALL Binance Spot pairs:

```bash
poetry run collect-data --days 365
```

This downloads data for 2000+ trading pairs (takes 20-30 minutes due to rate limiting).

## Daily Updates (30 seconds)

After initial collection, update daily:

```bash
poetry run update-data
```

## View Results

```bash
# Check collected data
head -20 data/all_pairs_eod.csv

# Run example analysis
poetry run python examples/ml_preprocessing_example.py
```

## Common Use Cases

### Collect USDT pairs only

```bash
# First, collect all pairs
poetry run collect-data --days 365

# Then filter in your code:
import pandas as pd
df = pd.read_csv('data/all_pairs_eod.csv')
usdt_pairs = df[df['symbol'].str.endswith('USDT')]
```

### Collect specific pairs

```bash
poetry run collect-data --symbols BTCUSDT ETHUSDT BNBUSDT ADAUSDT --days 365
```

### Update specific pairs

```bash
poetry run update-data --symbols BTCUSDT ETHUSDT
```

## Automate Daily Updates

### Linux/Mac (Cron)

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 00:30 UTC)
30 0 * * * cd /path/to/binance-eod-collector && poetry run update-data >> data/collector.log 2>&1
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 00:30
4. Action: Start a program
   - Program: `C:\Users\YourName\AppData\Roaming\Python\Scripts\poetry.exe`
   - Arguments: `run update-data`
   - Start in: `C:\path\to\binance-eod-collector`

## Data Format

Output file: `data/all_pairs_eod.csv`

| Column | Description |
|--------|-------------|
| date | Trading date (YYYY-MM-DD) |
| symbol | Trading pair (e.g., BTCUSDT) |
| open | Opening price |
| high | Highest price |
| low | Lowest price |
| close | Closing price |
| volume | Base asset volume |
| quote_volume | Quote asset volume |
| trades | Number of trades |
| market_cap_proxy | Price × Volume (liquidity measure) |

## Using in Your ML Model

```python
import pandas as pd

# Load data
df = pd.read_csv('data/all_pairs_eod.csv')
df['date'] = pd.to_datetime(df['date'])

# Filter USDT pairs
usdt = df[df['symbol'].str.endswith('USDT')]

# Create price matrix
prices = usdt.pivot(index='date', columns='symbol', values='close')

# Calculate returns
returns = prices.pct_change()

# Your ML model here...
# features = create_features(returns)
# weights = model.predict(features)
```

## Troubleshooting

**Can't connect to Binance:**
```bash
# Test connectivity
poetry run python -c "from binance.client import Client; print(Client().get_server_time())"
```

**Rate limit errors:**
- Wait a few minutes
- Increase sleep time in `src/binance_eod_collector/collector.py` (line with `time.sleep(0.5)`)

**No data collected:**
- Check internet connection
- Verify Binance is accessible in your region
- Some symbols may have limited history

## Next Steps

1. ✅ Collect data
2. 📊 Explore with `examples/ml_preprocessing_example.py`
3. 🤖 Build your ML trading model
4. 📈 Backtest your strategy
5. 🚀 Deploy for live trading

## Need Help?

- Check full documentation: [README.md](README.md)
- Binance API docs: https://binance-docs.github.io/apidocs/spot/en/
- Python-binance: https://python-binance.readthedocs.io/

---

**Happy Trading! 🎯**
