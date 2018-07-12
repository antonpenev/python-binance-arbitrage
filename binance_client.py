import config
from binance.client import Client as BinanceClient


def get_client():
    """ Return a new instance with Binance API connection """
    return BinanceClient(
        config.get('api_key'),
        config.get('api_secret'))


def concat_symbol(currency1, currency2):
    """
    With two currencies, returns the correct symbol market
    E.g. USDT, BTC -> BTCUSDT or BTC,ETH -> ETHBTC
    """

    if currency1 == 'USDT':
        symbol = currency2 + currency1
    elif currency2 == 'USDT' or currency2 == 'BTC':
        symbol = currency1 + currency2
    elif currency1 == 'BTC':
        symbol = currency2 + currency1
    elif currency1 == 'ETH':
        symbol = currency2 + currency1
    else:
        symbol = currency1 + currency2

    return symbol


def get_symbols(currency, market1, market2):
    return [
        concat_symbol(currency, market1),
        concat_symbol(currency, market2),
        concat_symbol(market1, market2),
    ]


def get_exchange_info(connection, symbols):
    """ Fetches general information for markets """

    return dict((s, connection.get_symbol_info(s)) for s in symbols)


def get_filter_lot_size(filters):
    """ Return the LOT_SIZE for given Binance exchange filters """

    lot_size = None
    for lotfilter in filters:
        if lotfilter.get('filterType') == 'LOT_SIZE':
            lot_size = float(lotfilter['stepSize'])
            break

    return lot_size
