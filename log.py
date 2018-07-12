""" Simple helper logging to stdout functions """

from datetime import datetime
import config


def binance_exception(e):
    """ Pretty print a Binance api exception """

    print("Binance exception", e)
    print('Code {}: {} '.format(e.status_code, e.message))


def debug(message):
    """ Only logs message if its debug mode """

    if config.is_debug():
        print(message)


def arbitrages_count(start_time, count, reverse_count, all_count):
    """ Print counters of arbitrages. Typically on quit statistics """

    print('\n----------\nTotal run time: {}'.format(
        datetime.now() - start_time))
    print('Arbitrages: {}, Reversed: {}, Total: {}'.format(
        count,
        reverse_count,
        all_count))
