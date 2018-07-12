"""
Script to be runned in cli mode side-by-side with main.py.
Purpose is to handle wallet balances while the other script is making trades.

Each balance from the config pairs should be higher than the const BALANCE_MULTIPLIER
Script presumes one of the wallets as a piggy bank e.g. with more money.
This wallet will be used to cache the other accounts.
"""

from binance.enums import SIDE_BUY, SIDE_SELL
from requests.exceptions import RequestException
import binance_client
import config
import order
import log

import time
import sys

client = binance_client.get_client()

markets = config.get('markets')
[market1, market2, market3] = markets

order_value = config.get('order_value')

# used for measure the value between different balances
RELATIVE_CURRENCY = config.get('main_wallet')
BALANCE_MULTIPLIER = 1.1


def get_balances(tickers):
    market1_balance = float(client.get_asset_balance(asset=market1)['free'])
    market2_balance = float(client.get_asset_balance(asset=market2)['free'])
    market3_balance = float(client.get_asset_balance(asset=market3)['free'])

    result = {
        market1: {
            'value': market1_balance,
            'relative_value': get_relative_price(market1_balance, market1, tickers)
        },
        market2: {
            'value': market2_balance,
            'relative_value': get_relative_price(market2_balance, market2, tickers)
        },
        market3: {
            'value': market3_balance,
            'relative_value': get_relative_price(market3_balance, market3, tickers)
        },
    }

    # BNB will be used for low fee trades
    if not result.get('BNB'):
        bnb_balance = float(client.get_asset_balance(asset='BNB')['free'])
        result['BNB'] = {
            'value': bnb_balance,
            'relative_value': get_relative_price(bnb_balance, 'BNB', tickers)
        }

    return result


def get_relative_price(value, currency, tickers):
    if currency == RELATIVE_CURRENCY:
        # after all 1 ETH is... 1 ETH
        return value

    for ticker in tickers:
        symbol = ticker['symbol']

        if symbol in [currency + RELATIVE_CURRENCY, RELATIVE_CURRENCY + currency]:
            price = float(ticker['price'])

            if symbol[-3:] == RELATIVE_CURRENCY:
                return value * price

            return value / price


def get_normal_price(value, exchange, tickers):
    symbol = exchange['symbol']
    ticker = next(t for t in tickers if t['symbol'] == symbol)

    price = float(ticker['price'])
    if exchange['baseAsset'] == RELATIVE_CURRENCY:
        return price * value

    return price / value


def get_tickers(symbols):
    return [t for t in client.get_all_tickers() if t['symbol'] in symbols]


def print_balance(value, currency, relative_value):
    log.debug('{}{} = {}{}'.format(
        value,
        currency,
        relative_value,
        RELATIVE_CURRENCY))


def rebalance_account(currency, relative_value, normal_value, exchange):

    if currency == RELATIVE_CURRENCY:
        print('No enough money in base account. Just quit...')
        sys.exit()

    if currency == exchange['baseAsset']:
        step_type = SIDE_BUY
        amount = normal_value
    else:
        step_type = SIDE_SELL
        amount = relative_value

    step = {
        'amount': amount,
        'symbol': exchange['symbol'],
        'type': step_type
    }

    lot_size = binance_client.get_filter_lot_size(exchange['filters'])
    options = {
        'lot_size': lot_size
    }

    print('before order.make', step, options)
    order.make(client, step, options)


def find_exchange_by_currency(currency, exchanges):
    try:
        return exchanges[currency + RELATIVE_CURRENCY]
    except KeyError:
        return exchanges[RELATIVE_CURRENCY + currency]


def check_balances(relative_order_value, balances, exchanges):
    multiplied_relative = relative_order_value * BALANCE_MULTIPLIER

    markets_bnb = markets[:]
    markets_bnb.append('BNB')

    for currency in markets_bnb:
        if currency == RELATIVE_CURRENCY:
            continue

        balance = balances[currency]
        print_balance(balance['value'], currency, balance['relative_value'])

        exchange = find_exchange_by_currency(currency, exchanges)

        if currency == 'BNB':
            multiplied_relative = 0.05 * multiplied_relative

        if balance['relative_value'] >= multiplied_relative:
            continue

        diff_value = multiplied_relative - balance['relative_value']

        normal_diff_value = get_normal_price(diff_value, exchange, tickers)

        # BNB rates are very low - let's just make one bigger transaction
        if currency == 'BNB':
            normal_diff_value = 1

        print('{} needs to be toped up with {}'.format(
            currency,
            normal_diff_value))

        rebalance_account(
            currency,
            diff_value,
            normal_diff_value,
            exchange)


if __name__ == '__main__':
    print('wallet balancer should be reworked to empty the wallet into the main')
    exit()

    symbols = binance_client.get_symbols(market1, market2, market3)
    symbols.append('BNB' + RELATIVE_CURRENCY)
    exchanges = binance_client.get_exchange_info(client, symbols)

    while True:
        try:
            tickers = get_tickers(symbols)
            balances = get_balances(tickers)

            relative_order_value = get_relative_price(order_value, market1, tickers)
            print_balance(order_value, market1, relative_order_value)

            check_balances(relative_order_value, balances, exchanges)

        except RequestException:
            print('Request timeout. Skip... and try again')

        time.sleep(6)
