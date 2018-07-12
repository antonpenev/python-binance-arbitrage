import binance_client
import config


def get_orderbook_tickers(client, symbols):
    """ For given symbols return order book tickers """

    result = client.get_orderbook_tickers()
    allowed_tickers = [t for t in result if t['symbol'] in symbols]
    tickers_dict = dict((t['symbol'], t) for t in allowed_tickers)

    return [tickers_dict[symbol] for symbol in symbols]


if __name__ == '__main__':
    markets = config.get('markets')
    client = binance_client.get_client()
    symbols = binance_client.get_symbols(*markets)

    get_orderbook_tickers(client, symbols)

