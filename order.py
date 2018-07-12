"""
Functions to make binance api orders
"""
from binance.enums import SIDE_BUY
from binance.exceptions import BinanceAPIException

import config


def make(connection, step, options):
    """ Makes order to given market """

    print('in make', step, options)
    symbol = step['symbol']
    precision = config.get('binance_max_precision')

    lot_size = options.get('lot_size')
    if not lot_size:
        raise 'No lot_size given'

    amount = float(format(step['amount'], precision))
    step_size = amount % lot_size

    amount = amount - step_size

    # round up
    if step_size > 0:
        amount = amount + lot_size

    quantity = format(amount, precision)

    make_market_order(
        connection,
        symbol=symbol,
        side_type=step['type'],
        quantity=quantity)


def make_market_order(connection, symbol, side_type, quantity):
    """ Make Binance Buy/Sell Market order """

    # print('in make_market_order. STOP HERE ', symbol, side_type, quantity)
    # return ''

    if side_type == SIDE_BUY:
        order = connection.order_market_buy(
            symbol=symbol,
            quantity=quantity)
    else:
        order = connection.order_market_sell(
            symbol=symbol,
            quantity=quantity)

    print('market order', type, order)

    return order
