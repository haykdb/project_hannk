# Binance EOD Data Collector

A Python package for collecting End-of-Day (EOD) cryptocurrency market data from **Binance Spot market** for all trading pairs.

## Features

✅ **All Binance Spot Pairs** - Automatically discovers and downloads data for all active trading pairs  
✅ **Historical Data** - Download up to 365+ days of historical data  
✅ **Daily Updates** - Efficiently update with latest EOD data  
✅ **No API Keys Required** - Uses public Binance market data endpoints  
✅ **Rate Limit Handling** - Automatic rate limiting to respect Binance API limits  
✅ **Market Data** - Collects: Open, High, Low, Close, Volume, Quote Volume  
✅ **Poetry Management** - Modern Python dependency management with Poetry  

## Installation

### Using Poetry (Recommended)

```bash
# Clone or download the project
cd binance-eod-collector

# Install dependencies
poetry install

# Activate the virtual environment
poetry shell
```

### Manual Installation

```bash
pip install python-binance pandas numpy requests python-dateutil
```

## Project Structure

```
binance-eod-collector/
├── pyproject.toml          # Poetry configuration
├── config.json             # Optional configuration file
├── README.md              # This file
├── src/
│   └── binance_eod_collector/
│       ├── __init__.py
│       ├── collector.py   # Main collector class
│       └── main.py        # CLI entry point
├── data/                  # Output directory (created automatically)
│   └── all_pairs_eod.csv # Collected data
└── examples/              # Example scripts (optional)
```

## Usage

### Quick Start

```bash
# Using Poetry scripts (recommended)
poetry run collect-data

# Or activate shell and run directly
poetry shell
python -m binance_eod_collector.main
```

### Initial Historical Data Collection

Collect historical data for ALL Binance Spot pairs:

```bash
poetry run collect-data --days 365
```

Collect data for specific pairs only:

```bash
poetry run collect-data --symbols BTCUSDT ETHUSDT BNBUSDT --days 365
```

Test with limited number of pairs:

```bash
poetry run collect-data --max-symbols 10 --days 30
```

### Daily Updates

After initial collection, update with latest data:

```bash
poetry run update-data
```

Update specific pairs:

```bash
poetry run update-data --symbols BTCUSDT ETHUSDT
```

### Command Line Options

**collect-data options:**
- `--days`: Number of days of historical data (default: 365)
- `--data-dir`: Output directory (default: 'data')
- `--max-symbols`: Limit number of symbols (for testing)
- `--symbols`: Space-separated list of specific symbols
- `--api-key`: Binance API key (optional)
- `--api-secret`: Binance API secret (optional)

**update-data options:**
- `--data-dir`: Data directory (default: 'data')
- `--symbols`: Space-separated list of specific symbols
- `--api-key`: Binance API key (optional)
- `--api-secret`: Binance API secret (optional)

## Configuration

Edit `config.json` to set default values:

```json
{
  "data_directory": "data",
  "historical_days": 365,
  "api_key": null,
  "api_secret": null
}
```

**Note:** API keys are optional. Binance allows public market data access without authentication.

## Output Format

Data is saved to `data/all_pairs_eod.csv`:

```csv
date,symbol,open,high,low,close,volume,quote_volume,trades,market_cap_proxy
2024-01-01,BTCUSDT,42500.00,43000.00,42000.00,42800.00,1500.5,64200000.0,125000,64200000.0
2024-01-01,ETHUSDT,2250.00,2280.00,2240.00,2270.00,8500.2,19280454.0,98000,19280454.0
```

**Columns:**
- `date`: Trading date
- `symbol`: Trading pair (e.g., BTCUSDT)
- `open`: Opening price
- `high`: Highest price
- `low`: Lowest price
- `close`: Closing price
- `volume`: Base asset volume
- `quote_volume`: Quote asset volume (in USDT, BTC, etc.)
- `trades`: Number of trades
- `market_cap_proxy`: Close price × Volume (liquidity proxy)

**Important Note on Market Cap:**  
True market cap requires circulating supply data, which isn't available through Binance API. The `market_cap_proxy` field provides a liquidity measure based on trading activity.

## Using in Your ML Trading Model

### Load and Process Data

```python
import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('data/all_pairs_eod.csv')
df['date'] = pd.to_datetime(df['date'])

# Filter for USDT pairs (most common base)
usdt_pairs = df[df['symbol'].str.endswith('USDT')]

# Pivot to get price matrix
price_matrix = usdt_pairs.pivot(index='date', columns='symbol', values='close')

# Calculate returns
returns = price_matrix.pct_change()

# Calculate rolling volatility
volatility = returns.rolling(window=30).std()

# Your ML model here...
```

### Example: Generate Trading Weights

```python
from binance_eod_collector import BinanceEODCollector

# Initialize collector
collector = BinanceEODCollector(data_dir="data")

# Get summary stats
stats = collector.get_summary_stats()
print(stats)

# Load data for analysis
df = pd.read_csv('data/all_pairs_eod.csv')

# Filter for liquid pairs (high volume)
liquid_pairs = df.groupby('symbol')['quote_volume'].mean()
top_pairs = liquid_pairs.nlargest(50).index.tolist()

# Your weight generation model...
```

## Automated Daily Updates

### Using Cron (Linux/Mac)

Add to crontab (`crontab -e`):

```bash
# Run daily at 00:30 UTC (after Binance daily snapshot)
30 0 * * * cd /path/to/binance-eod-collector && /path/to/poetry run update-data >> data/collector.log 2>&1
```

### Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create new task
3. Set trigger: Daily at 00:30
4. Set action: 
   ```
   Program: C:\path\to\poetry.exe
   Arguments: run update-data
   Start in: C:\path\to\binance-eod-collector
   ```

### Using Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . /app

# Install poetry
RUN pip install poetry

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev

# Run daily updates
CMD ["poetry", "run", "update-data"]
```

Build and run:

```bash
docker build -t binance-collector .
docker run -v $(pwd)/data:/app/data binance-collector
```

## Rate Limits

Binance API has weight limits of 1200 requests per minute. This collector:

- Uses 0.5 second delays between requests
- Stays well within rate limits
- Can collect ~120 symbols per minute
- Full collection of 2000+ pairs takes ~20-30 minutes

## API Information

This collector uses Binance's public REST API endpoints:
- `/api/v3/exchangeInfo` - Get all trading pairs
- `/api/v3/klines` - Get historical OHLCV data
- `/api/v3/ticker/24hr` - Get 24hr ticker statistics

No authentication is required for public market data endpoints.

## Troubleshooting

### Connection Issues

```bash
# Test Binance connectivity
python -c "from binance.client import Client; print(Client().get_server_time())"
```

### Rate Limit Errors

If you encounter rate limit errors:
1. Increase sleep time in `collector.py` (change from 0.5 to 1.0)
2. Use `--max-symbols` to process in batches
3. Wait a few minutes before retrying

### Missing Data

Some trading pairs may have limited history:
- Newly listed pairs have less historical data
- Delisted pairs won't appear in current data
- Check Binance listings for pair availability

## Development

### Running Tests

```bash
poetry install --with dev
poetry run pytest
```

### Code Formatting

```bash
poetry run black src/
poetry run ruff check src/
```

## Data Update Strategy

**Recommended approach:**

1. **Initial Setup**: Collect 365 days of historical data for all pairs
   ```bash
   poetry run collect-data --days 365
   ```

2. **Daily Updates**: Run automated updates at 00:30 UTC daily
   ```bash
   poetry run update-data
   ```

3. **Periodic Full Refresh**: Every 3-6 months, collect fresh historical data to ensure data quality

## For ML Model Development

This collector provides clean, normalized data ideal for:
- Long/short portfolio optimization
- Mean reversion strategies  
- Momentum-based models
- Pairs trading
- Market microstructure analysis
- Risk modeling

The data format makes it easy to:
- Calculate returns across all pairs
- Build correlation matrices
- Compute technical indicators
- Generate feature matrices for ML

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## License

MIT License - Free for commercial and non-commercial use

## Support

For issues:
- Check Binance API status: https://binance.com/en/support
- Review API documentation: https://binance-docs.github.io/apidocs/spot/en/
- Check rate limits and restrictions

## Acknowledgments

Built with:
- [python-binance](https://github.com/sammchardy/python-binance) - Excellent Binance API wrapper
- [pandas](https://pandas.pydata.org/) - Data manipulation
- [poetry](https://python-poetry.org/) - Dependency management

---

**Happy Trading! 📈**
