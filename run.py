import sys
from binance_eod_collector.crypto_collector_v2 import main

sys.argv[1:] = "historical 365".split(" ")
main()
