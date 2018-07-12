Crypto arbitrage bot.
----------------------------

For now basic idea is to do trinagular crypto arbitrage betweeen Binance markets.

```
Monitor:

BTC/USDT Market
ETH/USDT Market
ETH/BTC Market

Objective-> Accumulate USDT

call BTC/ETH price and multiply with BTC/USDT
compare to ETH/USDT price; If spread> 0.5%
Buy BTC with USDT (0.05% fee)
Buy ETH with BTC on BTC/ETH market (0.05% fee)
sell ETH on ETH/USDT (0.05% fee)
```

Requirements:
* `cp config.ini.sample config.ini` and replace your binance API keys and markets/currency.
* Load the corresponding markets in Binance with funds.
* `pip install python-binance` or `pip install -r requirements.txt`


Run:
* `python main.py` will run with the default _config.ini_
* `python main.py custom_config.ini` will override the config.ini with external.


Wallet balancer (because precisions and realtime logic in binance disrupt logic):
* `python wallet_balancer.py` or `python wallet_balancer.py custom_config.ini`
