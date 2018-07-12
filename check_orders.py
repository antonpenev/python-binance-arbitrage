from binance.enums import SIDE_BUY, SIDE_SELL
import binance_client
import config
import order

import time
import sys

client = binance_client.get_client()
markets = config.get('markets')
[market1, market2, market3] = markets
symbols = binance_client.get_symbols(market1, market2, market3)

orders =[ 32239119, 66512069, 22092391]

for symbol in symbols:
    for trade in client.get_my_trades(symbol=symbol, limit=100):
        if trade['orderId'] in orders:
            print(symbol + 'trades', trade)
