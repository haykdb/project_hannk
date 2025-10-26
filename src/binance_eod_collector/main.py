"""
Main entry point for Binance EOD Data Collector
"""

import argparse
import json
import os
import sys
from pathlib import Path
from binance_eod_collector import BinanceEODCollector


def load_config():
    """Load configuration from config.json if it exists"""
    config_path = Path("../../config.json")
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}


def main():
    """Main function for historical data collection"""
    parser = argparse.ArgumentParser(
        description="Collect historical EOD data from Binance Spot market"
    )
    parser.add_argument(
        '--days',
        type=int,
        default=365,
        help='Number of days of historical data to collect (default: 365)'
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        default='data',
        help='Directory to store data files (default: data)'
    )
    parser.add_argument(
        '--max-symbols',
        type=int,
        default=None,
        help='Maximum number of symbols to collect (for testing)'
    )
    parser.add_argument(
        '--symbols',
        type=str,
        nargs='+',
        help='Specific symbols to collect (e.g., BTCUSDT ETHUSDT)'
    )
    parser.add_argument(
        '--api-key',
        type=str,
        default=None,
        help='Binance API key (optional for public data)'
    )
    parser.add_argument(
        '--api-secret',
        type=str,
        default=None,
        help='Binance API secret (optional for public data)'
    )
    
    args = parser.parse_args()
    
    # Load config
    config = load_config()
    
    # Override config with command line args
    data_dir = args.data_dir or config.get('data_directory', 'data')
    api_key = args.api_key or config.get('api_key')
    api_secret = args.api_secret or config.get('api_secret')
    
    # Initialize collector
    collector = BinanceEODCollector(
        data_dir=data_dir,
        api_key=api_key,
        api_secret=api_secret
    )
    
    # Check if data already exists
    data_file = os.path.join(data_dir, "all_pairs_eod.csv")
    
    if not os.path.exists(data_file):
        print("No existing data found. Starting historical data collection...")
        collector.collect_historical_data(
            days=args.days,
            max_symbols=args.max_symbols,
            symbols_filter=args.symbols
        )
    else:
        print("Existing data found.")
        response = input("Do you want to:\n1. Collect fresh historical data (overwrites)\n2. Update with latest data\nChoice (1/2): ")
        
        if response == '1':
            collector.collect_historical_data(
                days=args.days,
                max_symbols=args.max_symbols,
                symbols_filter=args.symbols
            )
        elif response == '2':
            collector.collect_daily_update(symbols_filter=args.symbols)
        else:
            print("Invalid choice. Exiting.")
            sys.exit(1)
    
    # Print summary
    print("\n" + "="*60)
    print("DATA COLLECTION SUMMARY")
    print("="*60)
    stats = collector.get_summary_stats()
    print(json.dumps(stats, indent=2, default=str))


def update():
    """Update function for daily data collection"""
    parser = argparse.ArgumentParser(
        description="Update with today's EOD data from Binance Spot market"
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        default='data',
        help='Directory containing data files (default: data)'
    )
    parser.add_argument(
        '--symbols',
        type=str,
        nargs='+',
        help='Specific symbols to update (e.g., BTCUSDT ETHUSDT)'
    )
    parser.add_argument(
        '--api-key',
        type=str,
        default=None,
        help='Binance API key (optional for public data)'
    )
    parser.add_argument(
        '--api-secret',
        type=str,
        default=None,
        help='Binance API secret (optional for public data)'
    )
    
    args = parser.parse_args()
    
    # Load config
    config = load_config()
    
    # Override config with command line args
    data_dir = args.data_dir or config.get('data_directory', 'data')
    api_key = args.api_key or config.get('api_key')
    api_secret = args.api_secret or config.get('api_secret')
    
    # Initialize collector
    collector = BinanceEODCollector(
        data_dir=data_dir,
        api_key=api_key,
        api_secret=api_secret
    )
    
    # Perform daily update
    collector.collect_daily_update(symbols_filter=args.symbols)
    
    # Print summary
    print("\n" + "="*60)
    print("UPDATE SUMMARY")
    print("="*60)
    stats = collector.get_summary_stats()
    print(json.dumps(stats, indent=2, default=str))


if __name__ == "__main__":
    main()
