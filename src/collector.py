"""
Binance EOD Data Collector

Collects End-of-Day Price, Volume, and Market Cap data for all Binance Spot pairs
Uses hybrid approach:
- Binance API for OHLCV data
- CoinGecko API for market cap and circulating supply
"""

import logging
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import pandas as pd
import requests
from binance.client import Client
from binance.exceptions import BinanceAPIException

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BinanceEODCollector:
    """Collects EOD crypto market data from Binance Spot market with CoinGecko market cap data"""
    
    COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
    
    def __init__(self, data_dir: str = "data", api_key: Optional[str] = None, 
                 api_secret: Optional[str] = None):
        """
        Initialize the Binance data collector
        
        Args:
            data_dir: Directory to store CSV files
            api_key: Binance API key (optional for public data)
            api_secret: Binance API secret (optional for public data)
        
        Note: API keys are not required for downloading market data
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize Binance client (no keys needed for public market data)
        self.client = Client(api_key, api_secret)
        
        # Cache for CoinGecko mappings
        self._coingecko_map = None
        self._coingecko_map_timestamp = None
        
    def get_all_spot_symbols(self) -> List[str]:
        """
        Get all active Binance SPOT trading pairs
        
        Returns:
            List of trading pair symbols (e.g., ['BTCUSDT', 'ETHUSDT', ...])
        """
        try:
            exchange_info = self.client.get_exchange_info()
            
            # Filter for SPOT trading pairs with TRADING status
            spot_symbols = [
                s['symbol'] 
                for s in exchange_info['symbols'] 
                if s['status'] == 'TRADING'
            ]
            
            logger.info(f"Found {len(spot_symbols)} active SPOT trading pairs")
            return spot_symbols
            
        except BinanceAPIException as e:
            logger.error(f"Error fetching trading pairs: {e}")
            return []
    
    def get_coingecko_coins_list(self) -> Dict[str, str]:
        """
        Get CoinGecko coins list and create symbol-to-id mapping
        Cache for 24 hours to avoid excessive API calls
        
        Returns:
            Dictionary mapping symbol (uppercase) to CoinGecko ID
            Example: {'BTC': 'bitcoin', 'ETH': 'ethereum'}
        """
        # Check cache validity (24 hours)
        if (self._coingecko_map is not None and 
            self._coingecko_map_timestamp is not None):
            age = datetime.now() - self._coingecko_map_timestamp
            if age.total_seconds() < 86400:  # 24 hours
                return self._coingecko_map
        
        try:
            url = f"{self.COINGECKO_BASE_URL}/coins/list"
            response = requests.get(url)
            response.raise_for_status()
            coins = response.json()
            
            # Create mapping: symbol -> id
            symbol_map = {}
            for coin in coins:
                symbol = coin['symbol'].upper()
                # If duplicate symbols exist, prefer the one with more common name
                if symbol not in symbol_map:
                    symbol_map[symbol] = coin['id']
            
            self._coingecko_map = symbol_map
            self._coingecko_map_timestamp = datetime.now()
            
            logger.info(f"Loaded {len(symbol_map)} CoinGecko coin mappings")
            return symbol_map
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching CoinGecko coins list: {e}")
            return {}
    
    def extract_base_symbol(self, binance_symbol: str) -> Optional[str]:
        """
        Extract base asset symbol from Binance trading pair
        
        Args:
            binance_symbol: Binance symbol like 'BTCUSDT', 'ETHBTC', 'BNBBUSD'
        
        Returns:
            Base symbol (e.g., 'BTC', 'ETH') or None if cannot parse
        """
        # Common quote assets on Binance
        quote_assets = ['USDT', 'BUSD', 'USDC', 'BTC', 'ETH', 'BNB', 'TRX', 
                       'XRP', 'TUSD', 'PAX', 'EUR', 'GBP', 'AUD', 'TRY']
        
        # Try to match quote asset from the end
        for quote in quote_assets:
            if binance_symbol.endswith(quote):
                base = binance_symbol[:-len(quote)]
                if base:  # Make sure we have a base symbol
                    return base
        
        # If no match, log warning
        logger.warning(f"Could not extract base symbol from {binance_symbol}")
        return None
    
    def map_binance_to_coingecko(self, binance_symbol: str) -> Optional[str]:
        """
        Map Binance symbol to CoinGecko ID
        
        Args:
            binance_symbol: Binance trading pair (e.g., 'BTCUSDT')
        
        Returns:
            CoinGecko ID (e.g., 'bitcoin') or None if not found
        """
        base_symbol = self.extract_base_symbol(binance_symbol)
        if not base_symbol:
            return None
        
        coingecko_map = self.get_coingecko_coins_list()
        return coingecko_map.get(base_symbol)
    
    def get_coingecko_market_data(self, coingecko_ids: List[str]) -> Dict[str, Dict]:
        """
        Fetch market cap and supply data from CoinGecko for multiple coins
        
        Args:
            coingecko_ids: List of CoinGecko IDs
        
        Returns:
            Dictionary mapping CoinGecko ID to market data
        """
        if not coingecko_ids:
            return {}
        
        market_data = {}
        
        # CoinGecko allows up to 250 IDs per request with free tier
        batch_size = 250
        
        for i in range(0, len(coingecko_ids), batch_size):
            batch = coingecko_ids[i:i + batch_size]
            
            try:
                url = f"{self.COINGECKO_BASE_URL}/coins/markets"
                params = {
                    'vs_currency': 'usd',
                    'ids': ','.join(batch),
                    'order': 'market_cap_desc',
                    'per_page': batch_size,
                    'page': 1,
                    'sparkline': False
                }
                
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                for coin in data:
                    market_data[coin['id']] = {
                        'market_cap': coin.get('market_cap'),
                        'circulating_supply': coin.get('circulating_supply'),
                        'total_supply': coin.get('total_supply'),
                        'max_supply': coin.get('max_supply')
                    }
                
                # Rate limiting for CoinGecko free tier: 30 calls/min
                time.sleep(2)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching CoinGecko market data for batch {i}: {e}")
                continue
        
        logger.info(f"Fetched market data for {len(market_data)} coins from CoinGecko")
        return market_data
    
    def get_historical_klines(self, symbol: str, days: int = 365) -> pd.DataFrame:
        """
        Fetch historical daily klines (OHLCV) data for a symbol
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            days: Number of days of historical data
            
        Returns:
            DataFrame with columns: date, open, high, low, close, volume, 
                                   quote_volume, trades, taker_buy_base, taker_buy_quote
        """
        try:
            # Calculate start time
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            # Get daily klines
            klines = self.client.get_historical_klines(
                symbol=symbol,
                interval=Client.KLINE_INTERVAL_1DAY,
                start_str=start_time.strftime('%Y-%m-%d'),
                end_str=end_time.strftime('%Y-%m-%d')
            )
            
            if not klines:
                logger.warning(f"No data returned for {symbol}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Convert timestamp to date
            df['date'] = pd.to_datetime(df['timestamp'], unit='ms').dt.date
            
            # Convert price and volume columns to float
            price_cols = ['open', 'high', 'low', 'close', 'volume', 'quote_volume']
            for col in price_cols:
                df[col] = df[col].astype(float)
            
            # Select and reorder columns
            df = df[['date', 'open', 'high', 'low', 'close', 'volume', 'quote_volume', 'trades']]
            df['symbol'] = symbol
            
            logger.info(f"Downloaded {len(df)} days of data for {symbol}")
            return df
            
        except BinanceAPIException as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_current_day_ticker(self, symbols: List[str]) -> pd.DataFrame:
        """
        Get current 24hr ticker data for all symbols (more efficient for daily updates)
        
        Args:
            symbols: List of trading pair symbols
            
        Returns:
            DataFrame with current day data
        """
        try:
            # Get 24hr ticker for all symbols at once
            tickers = self.client.get_ticker()
            
            # Filter for requested symbols
            symbol_set = set(symbols)
            filtered_tickers = [t for t in tickers if t['symbol'] in symbol_set]
            
            if not filtered_tickers:
                logger.warning("No ticker data returned")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(filtered_tickers)
            
            # Add date and convert types
            df['date'] = datetime.now().date()
            
            # Select relevant columns and rename
            df = df[['date', 'symbol', 'openPrice', 'highPrice', 'lowPrice', 
                    'lastPrice', 'volume', 'quoteVolume', 'count']]
            
            df.columns = ['date', 'symbol', 'open', 'high', 'low', 
                         'close', 'volume', 'quote_volume', 'trades']
            
            # Convert to float
            price_cols = ['open', 'high', 'low', 'close', 'volume', 'quote_volume']
            for col in price_cols:
                df[col] = df[col].astype(float)
            
            logger.info(f"Downloaded current data for {len(df)} symbols")
            return df
            
        except BinanceAPIException as e:
            logger.error(f"Error fetching current ticker data: {e}")
            return pd.DataFrame()
    
    def enrich_with_coingecko_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        Enrich Binance data with CoinGecko market cap and supply data
        
        Args:
            df: DataFrame with Binance OHLCV data
        
        Returns:
            Tuple of (enriched DataFrame, list of skipped symbols)
        """
        if df.empty:
            return df, []
        
        # Get unique symbols
        symbols = df['symbol'].unique()
        
        # Map Binance symbols to CoinGecko IDs
        symbol_to_coingecko = {}
        skipped_symbols = []
        
        for symbol in symbols:
            cg_id = self.map_binance_to_coingecko(symbol)
            if cg_id:
                symbol_to_coingecko[symbol] = cg_id
            else:
                skipped_symbols.append(symbol)
        
        if not symbol_to_coingecko:
            logger.warning("No symbols could be mapped to CoinGecko")
            return pd.DataFrame(), list(symbols)
        
        logger.info(f"Mapped {len(symbol_to_coingecko)} symbols to CoinGecko")
        logger.info(f"Skipped {len(skipped_symbols)} symbols (not found on CoinGecko)")
        
        # Fetch CoinGecko market data
        coingecko_ids = list(symbol_to_coingecko.values())
        market_data = self.get_coingecko_market_data(coingecko_ids)
        
        # Enrich DataFrame
        df['market_cap'] = None
        df['circulating_supply'] = None
        df['total_supply'] = None
        df['max_supply'] = None
        
        for idx, row in df.iterrows():
            symbol = row['symbol']
            if symbol in symbol_to_coingecko:
                cg_id = symbol_to_coingecko[symbol]
                if cg_id in market_data:
                    df.at[idx, 'market_cap'] = market_data[cg_id]['market_cap']
                    df.at[idx, 'circulating_supply'] = market_data[cg_id]['circulating_supply']
                    df.at[idx, 'total_supply'] = market_data[cg_id]['total_supply']
                    df.at[idx, 'max_supply'] = market_data[cg_id]['max_supply']
        
        # Filter out rows where we couldn't get CoinGecko data
        df_filtered = df[df['market_cap'].notna()].copy()
        
        additional_skipped = set(df[df['market_cap'].isna()]['symbol'].unique())
        skipped_symbols.extend(additional_skipped)
        
        logger.info(f"Successfully enriched {len(df_filtered)} records with CoinGecko data")
        
        return df_filtered, skipped_symbols
    
    def save_to_csv(self, df: pd.DataFrame, filename: str = "all_pairs_eod.csv", 
                    mode: str = 'w'):
        """
        Save data to CSV file
        
        Args:
            df: DataFrame to save
            filename: Output filename
            mode: Write mode ('w' for overwrite, 'a' for append)
        """
        if df.empty:
            logger.warning("Empty DataFrame, nothing to save")
            return
        
        filepath = os.path.join(self.data_dir, filename)
        
        if mode == 'a' and os.path.exists(filepath):
            # Append and remove duplicates
            existing_df = pd.read_csv(filepath)
            existing_df['date'] = pd.to_datetime(existing_df['date']).dt.date
            
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['date', 'symbol'], keep='last')
            combined_df = combined_df.sort_values(['symbol', 'date'])
            combined_df.to_csv(filepath, index=False)
            logger.info(f"Appended data to {filepath}")
        else:
            df.to_csv(filepath, index=False)
            logger.info(f"Saved data to {filepath}")
    
    def collect_historical_data(self, days: int = 365, max_symbols: Optional[int] = None,
                               symbols_filter: Optional[List[str]] = None):
        """
        Collect historical data for all or filtered Binance Spot pairs
        Enriches with CoinGecko market cap and supply data
        
        Args:
            days: Number of days of historical data
            max_symbols: Maximum number of symbols to collect (for testing)
            symbols_filter: List of specific symbols to collect (e.g., ['BTCUSDT', 'ETHUSDT'])
        """
        logger.info("Starting historical data collection...")
        
        # Get all spot symbols
        if symbols_filter:
            symbols = symbols_filter
            logger.info(f"Using provided symbol filter: {len(symbols)} symbols")
        else:
            symbols = self.get_all_spot_symbols()
            
            if max_symbols:
                symbols = symbols[:max_symbols]
                logger.info(f"Limited to first {max_symbols} symbols for testing")
        
        all_data = []
        failed_symbols = []
        skipped_symbols_coingecko = []
        
        for i, symbol in enumerate(symbols, 1):
            logger.info(f"Processing {i}/{len(symbols)}: {symbol}")
            
            df = self.get_historical_klines(symbol, days=days)
            
            if not df.empty:
                all_data.append(df)
            else:
                failed_symbols.append(symbol)
            
            # Rate limiting: Binance has weight limits
            # Most requests have weight 1-2, limit is 1200/min
            # Sleep 0.5s between requests to be safe
            time.sleep(0.5)
            
            # Save and enrich intermediate results every 50 symbols
            if i % 50 == 0 and all_data:
                logger.info(f"Processing intermediate batch and enriching with CoinGecko data...")
                combined_df = pd.concat(all_data, ignore_index=True)
                
                # Enrich with CoinGecko data
                enriched_df, skipped = self.enrich_with_coingecko_data(combined_df)
                skipped_symbols_coingecko.extend(skipped)
                
                if not enriched_df.empty:
                    self.save_to_csv(enriched_df, mode='a')
                
                all_data = []  # Clear batch
        
        # Process final batch
        if all_data:
            logger.info("Processing final batch and enriching with CoinGecko data...")
            combined_df = pd.concat(all_data, ignore_index=True)
            
            # Enrich with CoinGecko data
            enriched_df, skipped = self.enrich_with_coingecko_data(combined_df)
            skipped_symbols_coingecko.extend(skipped)
            
            if not enriched_df.empty:
                enriched_df = enriched_df.sort_values(['symbol', 'date'])
                self.save_to_csv(enriched_df, mode='a')
        
        logger.info(f"Historical data collection complete!")
        logger.info(f"Successfully collected from Binance: {len(symbols) - len(failed_symbols)} symbols")
        logger.info(f"Failed to fetch from Binance: {len(failed_symbols)} symbols")
        logger.info(f"Skipped (not on CoinGecko): {len(set(skipped_symbols_coingecko))} symbols")
        
        if failed_symbols:
            logger.warning(f"Failed Binance symbols: {failed_symbols[:10]}...")
        if skipped_symbols_coingecko:
            logger.warning(f"Skipped CoinGecko symbols: {list(set(skipped_symbols_coingecko))[:10]}...")
    
    def collect_daily_update(self, symbols_filter: Optional[List[str]] = None):
        """
        Collect today's data for all Binance Spot pairs (for daily updates)
        Enriches with CoinGecko market cap and supply data
        
        Args:
            symbols_filter: Optional list of specific symbols to update
        """
        logger.info("Starting daily update...")
        
        # Get symbols
        if symbols_filter:
            symbols = symbols_filter
        else:
            symbols = self.get_all_spot_symbols()
        
        # Get current day data from Binance
        df = self.get_current_day_ticker(symbols)
        
        if not df.empty:
            # Enrich with CoinGecko data
            enriched_df, skipped = self.enrich_with_coingecko_data(df)
            
            if not enriched_df.empty:
                self.save_to_csv(enriched_df, mode='a')
                logger.info(f"Daily update complete for {len(enriched_df)} symbols")
                if skipped:
                    logger.info(f"Skipped {len(set(skipped))} symbols (not on CoinGecko)")
            else:
                logger.error("No symbols could be enriched with CoinGecko data")
        else:
            logger.error("Daily update failed - no data retrieved from Binance")
    
    def get_summary_stats(self) -> Dict:
        """
        Get summary statistics of collected data
        
        Returns:
            Dictionary with summary statistics
        """
        filepath = os.path.join(self.data_dir, "all_pairs_eod.csv")
        
        if not os.path.exists(filepath):
            return {"error": "No data file found"}
        
        df = pd.read_csv(filepath)
        df['date'] = pd.to_datetime(df['date'])
        
        stats = {
            "total_records": len(df),
            "unique_symbols": df['symbol'].nunique(),
            "date_range": {
                "start": df['date'].min().strftime('%Y-%m-%d'),
                "end": df['date'].max().strftime('%Y-%m-%d')
            },
            "top_10_symbols_by_volume": df.groupby('symbol')['volume'].sum()
                                          .sort_values(ascending=False).head(10).to_dict(),
            "data_completeness": {
                "symbols_with_data": df.groupby('symbol').size().describe().to_dict()
            }
        }
        
        return stats
