#!/usr/bin/env python
"""
CRYPTO ARBITRAGE BOT
"""
from datetime import datetime
import time
import sys
from requests.exceptions import RequestException

from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET
from binance.exceptions import BinanceAPIException, BinanceOrderException

import binance_client
import binance_sockets
import config
import tickers
import log

# CONFIGS
BINANCE_MAX_PRECISION = config.get('binance_max_precision')
MARKETS = config.get('markets')
ORDER_VALUE = config.get('order_value')
MIN_SPREAD = config.get('min_spread')
TEST_MODE = config.is_test()
DEBUG_MODE = config.is_debug()

# CONSTS
LIST_LIMIT = 5
FEE = 0.05

# Tracking variables
start_time = datetime.now()
arbitrages_count = 0
reverse_arbitrages_count = 0
check_count = 0

# General exchange info
exchanges = []

SYMBOLS = [
    binance_client.concat_symbol(MARKETS[0], MARKETS[1]),
    binance_client.concat_symbol(MARKETS[1], MARKETS[2]),
    binance_client.concat_symbol(MARKETS[2], MARKETS[0]),
]

# END CONFIGS

print(SYMBOLS)
BINANCE_CLIENT = binance_client.get_client()


def format_order(order):
    """ Reduce/Formats the bloat from Binance API order book"""
    return {
        'price': float(order[0]),
        'quantity': float(order[1])
    }


def determine_buy_sell(base_currency, pair, value):
    """
    When your arbitrage currency is market currency (USDT, ETH, BTC)
    the bid/asks operations are inverted
    """

    symbol = pair['symbol']
    bids = pair['bids']
    asks = pair['asks']
    base_asset = pair['base_asset']

    log.debug('{} bids: {} asks {}'.format(symbol, bids, asks))

    order_type = ORDER_TYPE_MARKET

    if base_asset == base_currency:
        side_type = SIDE_SELL
        amount = value * bids
    else:
        side_type = SIDE_BUY
        amount = value / asks

    if side_type == SIDE_BUY:
        depth_quantity = pair['asks_qty']
        price = asks
    else:
        depth_quantity = pair['bids_qty']
        price = bids

    return {
        'type': side_type,
        'amount': amount,
        'price': price,
        'depth_quantity': depth_quantity,
        'symbol': symbol,
        'order_type': order_type,
        'lot_size': pair['lot_size'],
        'base_asset': pair['base_asset']
    }


def get_depth(depth, exchange):
    """
    For currency pair symbol
    get order book and return the best prices for bids/asks
    """

    symbol = depth['symbol']
    filters = exchange['filters']

    return {
        'symbol': symbol,
        'bids': float(depth['bids']['price']),
        'bids_qty': float(depth['bids']['quantity']),
        'asks': float(depth['asks']['price']),
        'asks_qty': float(depth['asks']['quantity']),
        'base_asset': exchanges[symbol]['baseAsset'],
        'lot_size': binance_client.get_filter_lot_size(filters)
    }


def calculate(pairs, balance, markets):
    """ By given order books - determine if there is arbitrage opportunity """

    step1 = determine_buy_sell(markets[0], pairs[0], balance)
    firstBuy = step1['amount']

    step2 = determine_buy_sell(markets[1], pairs[1], firstBuy)
    secondBuy = step2['amount']

    step3 = determine_buy_sell(markets[2], pairs[2], secondBuy)
    thirdBuy = step3['amount']

    profit = thirdBuy - balance
    spread = (profit / balance * 100) - 3 * FEE

    has_arbitrage = spread >= MIN_SPREAD

    if has_arbitrage:
        first = '{} {} {} -> {}'.format(
            pairs[0]['symbol'],
            step1['type'],
            balance,
            firstBuy)
        second = '{} {} {} -> {}'.format(
            pairs[1]['symbol'],
            step2['type'],
            firstBuy,
            secondBuy)
        third = '{} {} {} -> {}'.format(
            pairs[2]['symbol'],
            step3['type'],
            secondBuy,
            thirdBuy)
        print('{}, {}, {}'.format(first, second, third))

        print('Profit: {} ({})\n'.format(
          format(spread, BINANCE_MAX_PRECISION),
          format(profit, BINANCE_MAX_PRECISION)
        ))
    else:
        log.debug('No profit ({})\n'.format(spread))

    return {
        'step1': step1,
        'step2': step2,
        'step3': step3,
        'profit': profit,
        'has_arbitrage': has_arbitrage,
        'markets': markets
    }


def start_arbitrage_deal(arbitrage, test_mode=True):
    """ Initiate arbitrage deals """

    [step1, step2, step3, __, __, markets] = arbitrage.values()

    # Corrections depending on the base or quote currency
    if step1['symbol'].endswith(markets[1]):
        step1['amount'] = ORDER_VALUE

    if step2['symbol'].endswith(markets[2]):
        step2['amount'] = ORDER_VALUE / step1['price']

    # if step3['symbol'].startswith(markets[0]):
    step3['amount'] = ORDER_VALUE  # step3['amount'] / step3['price']

    step1['quantity'] = do_amount_precision(step1['amount'], step1['lot_size'])
    step2['quantity'] = do_amount_precision(step2['amount'], step2['lot_size'])
    step3['quantity'] = do_amount_precision(step3['amount'], step3['lot_size'])

    [step1, step2, step3] = correct_lot_size(step1, step2, step3)

    no_qty_1 = float(step1['quantity']) > step1['depth_quantity']
    no_qty_2 = float(step2['quantity']) > step2['depth_quantity']
    no_qty_3 = float(step3['quantity']) > step3['depth_quantity']

    if no_qty_1 or no_qty_2 or no_qty_3:
        print('Skip arbitrage due not enough depth quantity. ')
        print('trade 1', step1)
        print('trade 2', step2)
        print('trade 3', step3)
        return

    start_arbitrage_time = datetime.now()
    print('Start: ' + start_arbitrage_time.strftime('%X'))

    make_order(BINANCE_CLIENT, step1, test_mode)
    make_order(BINANCE_CLIENT, step2, test_mode)
    make_order(BINANCE_CLIENT, step3, test_mode)

    print('Duration: {}'.format(datetime.now() - start_arbitrage_time))
    print('\n-------------------\n')


def correct_lot_size(step1, step2, step3):
    """ corrections if some of the pairs have lower LOT_SIZE (PRECISION) """

    max_lot = max(step1['lot_size'], step2['lot_size'])

    step1['quantity'] = do_amount_precision(step1['amount'], max_lot)
    step2['quantity'] = do_amount_precision(step1['amount'], max_lot)
    # step3['quantity'] = do_amount_precision(
    #     float(step2['quantity']) * float(step2['price']),
    #     step3['lot_size']
    # )

    return [step1, step2, step3]


def make_order(order_connection, step, test_mode=True):
    """ Makes order to given market """

    symbol = step['symbol']
    step_type = step['type']

    quantity = step['quantity']

    print('[Order] {} {} {} (price: {}, depth: {})'.format(
        step_type,
        symbol,
        quantity,
        step['price'],
        step['depth_quantity']))

    if not test_mode:
        try:
            make_market_order(
                order_connection,
                symbol=symbol,
                side_type=step_type,
                quantity=quantity)

        except BinanceAPIException as ex:
            ex.message += ' market=' + symbol
            log.binance_exception(ex)
            # No funds - no party
            # Or try rebalance in the future
            if ex.status_code is 400:
                log.arbitrages_count(
                    start_time,
                    arbitrages_count,
                    reverse_arbitrages_count,
                    check_count)
                sys.exit()
        except BinanceOrderException as ex:
            log.binance_exception(ex)
    else:
        # print('print make test call')
        order = order_connection.create_test_order(
            symbol=symbol,
            side=step_type,
            type=step['order_type'],
            quantity=quantity)

        print('test order ', order)


def do_amount_precision(amount, lot_size):
    step_size = float(format(amount % lot_size, BINANCE_MAX_PRECISION))

    amount = amount - step_size

    # round up
    # if step_size > 0:
    #     amount = amount + lot_size

    return format(amount, BINANCE_MAX_PRECISION)


def make_market_order(connection, symbol, side_type, quantity):
    """ Make Binance Buy/Sell Market order """

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


def try_arbitrage(depths, order_value, markets) -> bool:
    """ With given order books - calculate and if needed, start arbitrage """
    result = calculate(
        depths,
        order_value,
        markets
    )

    if result['has_arbitrage']:
        start_arbitrage_deal(result, TEST_MODE)
        return True

    return False


def receive_socket_depth(socket_depths):
    global reverse_arbitrages_count
    global arbitrages_count
    global check_count

    single_round_time = time.time()

    try:
        depths = [get_depth(s, exchanges[s['symbol']]) for s in socket_depths]

        check_count += 1

        if try_arbitrage(depths, ORDER_VALUE, MARKETS):
            arbitrages_count = arbitrages_count + 1
            return

        # try also the reverse arbitrage logic
        reverse_depths = [depths[1], depths[0], depths[2]]
        reverse_markets = [MARKETS[2], MARKETS[1], MARKETS[0]]

        reverse_order_value = ORDER_VALUE * depths[2]['asks']
        if try_arbitrage(reverse_depths, reverse_order_value, reverse_markets):
            reverse_arbitrages_count += 1

    except RequestException as ex:
        print('Request timeout. Skip... and try again')
        print(ex)
        time.sleep(10)

    log.debug('Check time: {}\n'.format(time.time() - single_round_time))


if __name__ == '__main__':
    exchanges = binance_client.get_exchange_info(BINANCE_CLIENT, SYMBOLS)

    binance_sockets.start_depths_socket(
        BINANCE_CLIENT,
        SYMBOLS,
        receive_socket_depth)

    try:
        # loop
        while True:
            time.sleep(5)
            continue
    except KeyboardInterrupt:
        binance_sockets.stop()

        log.arbitrages_count(
            start_time,
            arbitrages_count,
            reverse_arbitrages_count,
            check_count)

        sys.exit(0)
