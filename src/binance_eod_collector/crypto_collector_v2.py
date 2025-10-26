"""
Crypto Market Data Collector - Version 2
Uses Binance for trading pairs discovery and CoinGecko for historical data

Features:
- Fetches 365 days of historical data (Price, Volume, Market Cap)
- Daily updates
- Automatic symbol mapping between Binance and CoinGecko
"""

import requests
import pandas as pd
import time
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CryptoDataCollector:
    def __init__(self, output_dir='data'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.binance_base_url = 'https://api.binance.com/api/v3'
        self.coingecko_base_url = 'https://api.coingecko.com/api/v3'
        
        # Rate limiting
        self.coingecko_calls = []
        self.max_calls_per_minute = 30  # CoinGecko free tier limit
        
        # Cache file for symbol mappings
        self.mapping_file = self.output_dir / 'symbol_mapping.json'
        self.symbol_mapping = self.load_symbol_mapping()
        
    def load_symbol_mapping(self):
        """Load cached symbol mapping if exists"""
        if self.mapping_file.exists():
            with open(self.mapping_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_symbol_mapping(self):
        """Save symbol mapping to cache"""
        with open(self.mapping_file, 'w') as f:
            json.dump(self.symbol_mapping, f, indent=2)
    
    def rate_limit_coingecko(self):
        """Ensure we don't exceed CoinGecko rate limits (30 calls/min)"""
        now = time.time()
        # Remove calls older than 60 seconds
        self.coingecko_calls = [t for t in self.coingecko_calls if now - t < 60]
        
        if len(self.coingecko_calls) >= self.max_calls_per_minute:
            sleep_time = 60 - (now - self.coingecko_calls[0]) + 1
            logger.info(f"Rate limit reached. Sleeping for {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)
            self.coingecko_calls = []
        
        self.coingecko_calls.append(now)
    
    def get_binance_spot_pairs(self):
        """Get all USDT trading pairs from Binance"""
        logger.info("Fetching Binance Spot pairs...")
        
        try:
            response = requests.get(f'{self.binance_base_url}/exchangeInfo', timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Filter for active USDT pairs
            usdt_pairs = []
            for symbol_info in data['symbols']:
                if (symbol_info['status'] == 'TRADING' and 
                    symbol_info['quoteAsset'] == 'USDT'):
                    usdt_pairs.append({
                        'symbol': symbol_info['symbol'],
                        'base_asset': symbol_info['baseAsset']
                    })
            
            logger.info(f"Found {len(usdt_pairs)} active USDT trading pairs")
            return usdt_pairs
            
        except Exception as e:
            logger.error(f"Error fetching Binance pairs: {e}")
            return []
    
    def get_coingecko_coins_list(self):
        """Get list of all coins from CoinGecko for mapping"""
        logger.info("Fetching CoinGecko coins list...")
        self.rate_limit_coingecko()
        
        try:
            response = requests.get(
                f'{self.coingecko_base_url}/coins/list',
                timeout=10
            )
            response.raise_for_status()
            coins = response.json()
            
            # Create mapping: symbol -> id
            symbol_to_id = {}
            for coin in coins:
                symbol = coin['symbol'].upper()
                coin_id = coin['id']
                
                # Store first match, but prefer exact matches
                if symbol not in symbol_to_id:
                    symbol_to_id[symbol] = coin_id
                # Prefer matches where symbol matches name
                elif coin['name'].lower() == symbol.lower():
                    symbol_to_id[symbol] = coin_id
            
            logger.info(f"Loaded {len(symbol_to_id)} coin mappings from CoinGecko")
            return symbol_to_id
            
        except Exception as e:
            logger.error(f"Error fetching CoinGecko coins list: {e}")
            return {}
    
    def map_binance_to_coingecko(self, base_asset, symbol_to_id):
        """Map Binance base asset to CoinGecko ID"""
        # Check cache first
        if base_asset in self.symbol_mapping:
            return self.symbol_mapping[base_asset]
        
        # Try direct mapping
        if base_asset in symbol_to_id:
            coingecko_id = symbol_to_id[base_asset]
            self.symbol_mapping[base_asset] = coingecko_id
            return coingecko_id
        
        # Handle special cases
        special_mappings = {
            'BNB': 'binancecoin',
            'WBTC': 'wrapped-bitcoin',
            'WETH': 'weth',
            'SHIB': 'shiba-inu',
            'DOGE': 'dogecoin',
            'MATIC': 'matic-network',
        }
        
        if base_asset in special_mappings:
            coingecko_id = special_mappings[base_asset]
            self.symbol_mapping[base_asset] = coingecko_id
            return coingecko_id
        
        return None
    
    def get_historical_data(self, coingecko_id, days=365):
        """
        Fetch historical price, volume, and market cap from CoinGecko
        
        Args:
            coingecko_id: CoinGecko coin ID (e.g., 'bitcoin')
            days: Number of days of history (max 365 for free tier)
        
        Returns:
            DataFrame with columns: timestamp, date, price, volume, market_cap
        """
        self.rate_limit_coingecko()
        
        try:
            response = requests.get(
                f'{self.coingecko_base_url}/coins/{coingecko_id}/market_chart',
                params={
                    'vs_currency': 'usd',
                    'days': days,
                    'interval': 'daily'
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract data
            prices = data.get('prices', [])
            market_caps = data.get('market_caps', [])
            volumes = data.get('total_volumes', [])
            
            if not prices or not market_caps or not volumes:
                logger.warning(f"No data returned for {coingecko_id}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df_list = []
            for price_data, mcap_data, vol_data in zip(prices, market_caps, volumes):
                timestamp = price_data[0]
                df_list.append({
                    'timestamp': timestamp,
                    'date': datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d'),
                    'price': price_data[1],
                    'market_cap': mcap_data[1],
                    'volume': vol_data[1]
                })
            
            df = pd.DataFrame(df_list)
            logger.info(f"Fetched {len(df)} days of data for {coingecko_id}")
            return df
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning(f"Rate limited by CoinGecko. Waiting 60 seconds...")
                time.sleep(60)
                return self.get_historical_data(coingecko_id, days)
            else:
                logger.error(f"HTTP error fetching data for {coingecko_id}: {e}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error fetching data for {coingecko_id}: {e}")
            return pd.DataFrame()
    
    def collect_historical_data(self, days=365):
        """
        Collect historical data for all Binance USDT pairs
        
        Args:
            days: Number of days of history (max 365 for free tier)
        """
        logger.info(f"Starting historical data collection for {days} days...")
        
        # Get Binance pairs
        binance_pairs = self.get_binance_spot_pairs()
        if not binance_pairs:
            logger.error("No Binance pairs found. Exiting.")
            return

        # Get CoinGecko mapping
        symbol_to_id = self.get_coingecko_coins_list()
        
        # Collect data for each pair
        all_data = []
        successful_pairs = 0
        failed_pairs = []
        
        for i, pair_info in enumerate(binance_pairs, 1):
            symbol = pair_info['symbol']
            base_asset = pair_info['base_asset']
            
            logger.info(f"Processing {i}/{len(binance_pairs)}: {symbol} ({base_asset})")
            
            # Map to CoinGecko ID
            coingecko_id = self.map_binance_to_coingecko(base_asset, symbol_to_id)
            
            if not coingecko_id:
                logger.warning(f"Could not map {base_asset} to CoinGecko ID. Skipping {symbol}.")
                failed_pairs.append(symbol)
                continue
            
            # Fetch historical data
            df = self.get_historical_data(coingecko_id, days)
            
            if df.empty:
                logger.warning(f"No data retrieved for {symbol}. Skipping.")
                failed_pairs.append(symbol)
                continue
            
            # Add pair information
            df['symbol'] = symbol
            df['base_asset'] = base_asset
            df['coingecko_id'] = coingecko_id
            
            all_data.append(df)
            successful_pairs += 1
            
            # Save progress every 50 pairs
            if successful_pairs % 50 == 0:
                self.save_data(all_data, f'checkpoint_{successful_pairs}')
                logger.info(f"Checkpoint saved: {successful_pairs} pairs processed")
        
        # Save symbol mapping
        self.save_symbol_mapping()
        
        # Save final data
        if all_data:
            self.save_data(all_data, 'historical')
            logger.info(f"Historical data collection complete!")
            logger.info(f"Successful: {successful_pairs}/{len(binance_pairs)} pairs")
            if failed_pairs:
                logger.info(f"Failed pairs: {', '.join(failed_pairs[:10])}{'...' if len(failed_pairs) > 10 else ''}")
        else:
            logger.error("No data collected!")
    
    def collect_daily_update(self):
        """
        Update data with the latest day's data for all pairs
        """
        logger.info("Starting daily data update...")
        
        # Load existing data
        data_file = self.output_dir / 'crypto_data.csv'
        if not data_file.exists():
            logger.error("No existing data file found. Run historical collection first.")
            return
        
        existing_df = pd.read_csv(data_file)
        logger.info(f"Loaded existing data: {len(existing_df)} rows")
        
        # Get unique pairs
        pairs = existing_df[['symbol', 'base_asset', 'coingecko_id']].drop_duplicates()
        
        # Collect latest data for each pair
        new_data = []
        successful_updates = 0
        
        for i, row in pairs.iterrows():
            symbol = row['symbol']
            base_asset = row['base_asset']
            coingecko_id = row['coingecko_id']
            
            logger.info(f"Updating {i+1}/{len(pairs)}: {symbol}")
            
            # Fetch last 2 days (to ensure we get today's data)
            df = self.get_historical_data(coingecko_id, days=2)
            
            if df.empty:
                logger.warning(f"No data retrieved for {symbol}")
                continue
            
            # Get only the latest day
            df = df.sort_values('date').tail(1)
            
            # Add pair information
            df['symbol'] = symbol
            df['base_asset'] = base_asset
            df['coingecko_id'] = coingecko_id
            
            new_data.append(df)
            successful_updates += 1
        
        if new_data:
            # Combine new data
            new_df = pd.concat(new_data, ignore_index=True)
            
            # Remove duplicates (in case data already exists)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['date', 'symbol'], keep='last')
            combined_df = combined_df.sort_values(['symbol', 'date'])
            
            # Save
            output_file = self.output_dir / 'crypto_data.csv'
            combined_df.to_csv(output_file, index=False)
            
            logger.info(f"Daily update complete!")
            logger.info(f"Updated: {successful_updates}/{len(pairs)} pairs")
            logger.info(f"Total rows: {len(combined_df)}")
            logger.info(f"New rows added: {len(combined_df) - len(existing_df)}")
        else:
            logger.error("No new data collected!")
    
    def save_data(self, data_list, prefix=''):
        """Save collected data to CSV"""
        if not data_list:
            logger.warning("No data to save")
            return
        
        # Combine all dataframes
        df = pd.concat(data_list, ignore_index=True)
        
        # Sort by symbol and date
        df = df.sort_values(['symbol', 'date'])
        
        # Reorder columns
        column_order = ['date', 'symbol', 'base_asset', 'coingecko_id', 
                       'price', 'volume', 'market_cap', 'timestamp']
        df = df[column_order]
        
        # Save to CSV
        filename = f"{prefix}_crypto_data.csv" if prefix else "crypto_data.csv"
        output_file = self.output_dir / filename
        df.to_csv(output_file, index=False)
        
        logger.info(f"Data saved to {output_file}")
        logger.info(f"Total rows: {len(df)}")
        logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
        logger.info(f"Unique pairs: {df['symbol'].nunique()}")


def main():
    """Main entry point"""
    import sys
    
    collector = CryptoDataCollector(output_dir='data')
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'historical':
            # Collect 365 days of historical data
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 365
            collector.collect_historical_data(days=days)
        
        elif command == 'update':
            # Daily update
            collector.collect_daily_update()
        
        else:
            print("Usage:")
            print("  python crypto_collector_v2.py historical [days]  # Collect historical data (default: 365 days)")
            print("  python crypto_collector_v2.py update             # Daily update")
    else:
        print("Usage:")
        print("  python crypto_collector_v2.py historical [days]  # Collect historical data (default: 365 days)")
        print("  python crypto_collector_v2.py update             # Daily update")


if __name__ == '__main__':
    main()
