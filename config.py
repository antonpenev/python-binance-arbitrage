#!/usr/bin/env python
import configparser
import sys

# CONFIGS
CONFIG_FILE = 'config.ini'
if len(sys.argv) > 1:
    CONFIG_FILE = sys.argv[1]

PARSER = configparser.ConfigParser()
PARSER.read(CONFIG_FILE)

_CONFIG = {
    'markets': PARSER.get('all', 'markets').split(' '),
    'order_value': PARSER.getfloat('all', 'order_value'),
    'min_spread': PARSER.getfloat('all', 'min_spread'),
    'api_key': PARSER.get('all', 'api_key'),
    'api_secret': PARSER.get('all', 'api_secret'),
    'binance_max_precision': '.8f',
    'test_mode': PARSER.get('all', 'test_mode'),
    'main_wallet': PARSER.get('all', 'main_wallet')
}


def get(key):
    return _CONFIG.get(key)


def is_test():
    try:
        test_mode = PARSER.getboolean('all', 'test_mode')
    except configparser.NoOptionError:
        print('expection')
        test_mode = False

    return test_mode


def is_debug():
    try:
        debug_mode = PARSER.getboolean('all', 'debug')
    except configparser.NoOptionError:
        debug_mode = False

    return debug_mode

