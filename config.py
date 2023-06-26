import os
from dotenv import load_dotenv

load_dotenv()

TG_TOKEN = os.getenv('TG_TOKEN')

main_user = os.getenv('MAIN_USER')

# словарь банков
banks = {'TINKOFF' : 'Тинькофф',
         'SBER' : 'Сбербанк',
         'RAIF' : 'Райффайзенбанк'
         }

# словарь вылюты
currency_data = {
    'BINANCE' : 'RUB',
    'HUOBI' : 11,
    'BYBIT' : 'RUB'
}

#список пар для меню спот:
pairs = {
    'BINANCE' : ['BTC/USDT', 'USDT/RUB', 'BTC/RUB', 'BNB/USDT', 'BUSD/USDT'],
    'HUOBI' : ['BTC/USDT', 'USDT/RUB', 'BTC/RUB', 'BNB/USDT'],
    'BYBIT' : ['BTC/USDT', 'BNB/USDT', 'BUSD/USDT'],
    }

# список пар, доступных для торговли на споте:
pairs_spot = {
    'BINANCE' : ['USDT/RUB', 'BTC/USDT', 'BTC/BUSD', 'BTC/RUB', 'BUSD/USDT', 'BUSD/RUB', 'BNB/USDT', 'BNB/BTC', 'BNB/BUSD', 'BNB/ETH', 'BNB/RUB', 'ETH/USDT', 'ETH/BTC', 'ETH/BUSD', 'ETH/RUB', 'SHIB/USDT', 'SHIB/BUSD'],
    'HUOBI' : ['BTC/USDT', 'BTC/USDD', 'USDD/USDT', 'HT/USDT', 'HT/USDD', 'HT/ETH', 'TRX/USDT', 'TRX/BTC', 'TRX/USDD', 'TRX/ETH', 'ETH/USDT', 'ETH/BTC', 'ETH/USDD', 'EOS/USDT', 'EOS/BTC', 'EOS/USDD', 'EOS/HT', 'EOS/ETH', 'XRP/USDT', 'XRP/BTC', 'XRP/USDD', 'XRP/HT', 'LTC/USDT', 'LTC/BTC', 'LTC/HT'],
    'BYBIT' : ['BTC/USDT', 'ETH/USDT', 'USDC/USDT'],
}

# монеты, доступные для торговли на р2р:
coins = {
    'BINANCE' : ['USDT', 'BTC', 'BUSD', 'BNB', 'ETH', 'RUB', 'SHIB'],
    'HUOBI' : ['USDT', 'BTC', 'USDD', 'HT', 'TRX', 'ETH', 'EOS', 'XRP', 'LTC'],
    'BYBIT' : ['USDT', 'BTC', 'ETH', 'USDC'],
    }

# словарь связок taker - taker
taker = {}

bonds_all_params = ['BINANCE', 'HUOBI', 'BYBIT', 'TINKOFF', 'SBER', 'RAIF', 'taker-taker', 'maker-maker', 'taker-maker', 'maker-taker']
sides = ['BUY', 'SELL']

settings_flag = False
settings_alarm_flag = True

profit_bonds = []
alarms = []

url_binance = 'https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search'
url_huobi = 'https://otc-api.trygofast.com/v1/data/trade-market'
url_bybit = 'https://api2.bybit.com/fiat/otc/item/online'

url_binance_spot = 'https://api.binance.com/api/v3/ticker/price?symbol='
url_huobi_spot = 'https://api.huobi.pro/market/detail/merged?symbol='
url_bybit_spot = 'https://api.bybit.com/v2/public/tickers?symbol='