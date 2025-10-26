"""
Daily Update Scheduler for Crypto Data Collector

This script runs continuously and executes daily updates at a specified time.
"""

import schedule
import time
import logging
from datetime import datetime
from binance_eod_collector.crypto_collector_v2 import CryptoDataCollector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def daily_update():
    """Run daily data update"""
    logger.info("=" * 60)
    logger.info(f"Starting scheduled daily update: {datetime.now()}")
    logger.info("=" * 60)
    
    try:
        collector = CryptoDataCollector(output_dir='data')
        collector.collect_daily_update()
        logger.info("Daily update completed successfully!")
    except Exception as e:
        logger.error(f"Daily update failed: {e}", exc_info=True)
    
    logger.info("=" * 60)


def main():
    """Main scheduler loop"""
    # Create logs directory if it doesn't exist
    import os
    os.makedirs('logs', exist_ok=True)
    
    # Schedule daily update at 1:00 AM
    update_time = "01:00"
    schedule.every().day.at(update_time).do(daily_update)
    
    logger.info("=" * 60)
    logger.info("Crypto Data Collector - Daily Scheduler Started")
    logger.info("=" * 60)
    logger.info(f"Daily updates scheduled at: {update_time}")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)
    
    # Run once immediately if requested
    import sys
    if '--now' in sys.argv:
        logger.info("Running update immediately (--now flag detected)")
        daily_update()
    
    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")


if __name__ == '__main__':
    main()
