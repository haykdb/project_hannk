"""
Binance EOD Data Collector

A Python package for collecting End-of-Day (EOD) cryptocurrency market data
from Binance Spot market for all trading pairs.
"""

__version__ = "0.1.0"
__author__ = "Your Name"

from .collector import BinanceEODCollector

__all__ = ["BinanceEODCollector"]
