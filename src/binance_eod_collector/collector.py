"""
Binance EOD Data Collector

Collects End-of-Day Price, Volume, and Market Cap data for all Binance Spot pairs
"""

import logging
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BinanceEODCollector:
    """Collects EOD crypto market data from Binance Spot market"""
    
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
    
    def calculate_market_cap_proxy(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add market cap proxy based on quote volume
        
        Note: True market cap requires circulating supply data which isn't 
        available through Binance API. We use quote_volume as a proxy for liquidity.
        
        Args:
            df: DataFrame with price and volume data
            
        Returns:
            DataFrame with market_cap_proxy column added
        """
        # Market cap proxy = close price * volume
        # This gives us a sense of the market size/liquidity
        df['market_cap_proxy'] = df['close'] * df['volume']
        return df
    
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
        
        for i, symbol in enumerate(symbols, 1):
            logger.info(f"Processing {i}/{len(symbols)}: {symbol}")
            
            df = self.get_historical_klines(symbol, days=days)
            
            if not df.empty:
                df = self.calculate_market_cap_proxy(df)
                all_data.append(df)
            else:
                failed_symbols.append(symbol)
            
            # Rate limiting: Binance has weight limits
            # Most requests have weight 1-2, limit is 1200/min
            # Sleep 0.5s between requests to be safe
            time.sleep(0.5)
            
            # Save intermediate results every 100 symbols
            if i % 100 == 0 and all_data:
                logger.info(f"Saving intermediate results after {i} symbols...")
                combined_df = pd.concat(all_data, ignore_index=True)
                self.save_to_csv(combined_df)
                all_data = []
        
        # Save final batch
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            combined_df = combined_df.sort_values(['symbol', 'date'])
            self.save_to_csv(combined_df)
        
        logger.info(f"Historical data collection complete!")
        logger.info(f"Successfully collected: {len(symbols) - len(failed_symbols)} symbols")
        
        if failed_symbols:
            logger.warning(f"Failed symbols ({len(failed_symbols)}): {failed_symbols[:10]}...")
    
    def collect_daily_update(self, symbols_filter: Optional[List[str]] = None):
        """
        Collect today's data for all Binance Spot pairs (for daily updates)
        
        Args:
            symbols_filter: Optional list of specific symbols to update
        """
        logger.info("Starting daily update...")
        
        # Get symbols
        if symbols_filter:
            symbols = symbols_filter
        else:
            symbols = self.get_all_spot_symbols()
        
        # Get current day data
        df = self.get_current_day_ticker(symbols)
        
        if not df.empty:
            df = self.calculate_market_cap_proxy(df)
            self.save_to_csv(df, mode='a')
            logger.info(f"Daily update complete for {len(df)} symbols")
        else:
            logger.error("Daily update failed - no data retrieved")
    
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
