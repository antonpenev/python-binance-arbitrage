from datetime import datetime

import sys
from binance.websockets import BinanceSocketManager

_socket_client = None
_socket_key = None
_socket_depths = {}
_symbols = []

DEPTH_SYMBOL_SUFFIX = '@depth5'

def stop():
    _socket_client.stop_socket(_socket_key)


def on_receive_depths(msg):
    """
    Receives single Binance socket event.
    If the event tops up to all numbers of symbols, to start format events
    """

    global _socket_depths

    if not msg['stream'].endswith(DEPTH_SYMBOL_SUFFIX):
        print('skip socket message')
        return

    symbol = msg['stream'][:-len(DEPTH_SYMBOL_SUFFIX)]
    _socket_depths[symbol] = {'symbol': symbol, 'data': msg['data']}

    if len(_socket_depths.keys()) == len(_symbols):
        result = format_depths(_socket_depths.values(), _symbols)
        _socket_depths = {}
        return result


def format_depths(socket_depths, symbols):
    """
    Parses the order books,
    gets the worst price and the total amount of all orders
    """

    result = []
    for depth in socket_depths:
        data = depth['data']
        symbol = depth['symbol'].upper()

        bids_quantity = sum([float(amount) for _, amount, _ in data['bids']])
        bids_price = float(data['bids'][-1][0])

        asks_quantity = sum([float(amount) for _, amount, _ in data['asks']])
        asks_price = float(data['asks'][-1][0])

        result.append({
            'symbol': symbol,
            'bids': {
                'price': bids_price,
                'quantity': bids_quantity
            },
            'asks': {
                'price': asks_price,
                'quantity': asks_quantity
            }
        })

    return sorted(result, key=lambda depth: symbols.index(depth['symbol']))


def start_depths_socket(client, symbols, callback):
    """
    Initiates the binance socket connect.
    Binds socket received messages to the external callback
    """

    global _symbols
    global _socket_client
    global _socket_key

    _symbols = symbols

    _socket_client = BinanceSocketManager(client)

    symbols_websockets = [(s + DEPTH_SYMBOL_SUFFIX).lower() for s in _symbols]

    # internal... ugly.. but wraps the external callback in this scope
    def socket_cb(msg):
        depths = on_receive_depths(msg)
        if depths:
            callback(depths)

    _socket_key = _socket_client.start_multiplex_socket(
        symbols_websockets,
        socket_cb)

    _socket_client.start()


if __name__ == '__main__':
    import time
    import config
    import binance_client

    symbols = binance_client.get_symbols(*config.get('markets'))

    _socket_depths = []

    def dummy_callback(depths):
        print('dummy callback', depths)

    start_depths_socket(binance_client.get_client(), symbols, dummy_callback)

    while True:
        time.sleep(5)
        continue
