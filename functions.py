import sqlite3
import requests
import pprint

import config

headers = {
    'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'origin' : 'https://www.bybit.com'
}

class Deal:
    def __init__(self, nick, price, max, min, orders, rate, banks): 
        self.nick = nick
        self.price = price
        self.max = max
        self.min = min
        self.orders = orders
        self.rate = rate
        self.banks = banks


class Pair:
    def __init__(self, exchange, price, coin_a, coin_b, pair): 
        self.exchange = exchange
        self.price = price
        self.coin_a = coin_a
        self.coin_b = coin_b
        self.pair = pair


class Coin:
    def __init__(self, exchange, coin, price, side, nick, orders, rate, banks): 
        self.exchange = exchange
        self.coin = coin
        self.price = price        
        self.side = side
        self.nick = nick
        self.orders = orders
        self.rate = rate
        self.banks = banks


class OneExOneCoin:
    def __init__(self, exchange, coin, profit, side_a, side_b, buy, sell): 
        self.exchange = exchange
        self.coin = coin
        self.profit = profit  

        if side_a == 'BUY':
            method_a = 'taker'
        elif side_a == 'SELL':
            method_a = 'maker'
        
        if side_b == 'BUY':
            method_b = 'maker'
        elif side_b == 'SELL':
            method_b = 'taker'

        self.method = f'{method_a}-{method_b}'
        self.buy = buy
        self.sell = sell


class TwoExOneCoin:
    def __init__(self, exchange_a, exchange_b, profit, side_a, side_b, buy, sell, coin='USDT'): 
        self.exchange_a = exchange_a
        self.exchange_b = exchange_b
        self.coin = coin
        self.profit = profit

        if side_a == 'BUY':
            method_a = 'taker'
        elif side_a == 'SELL':
            method_a = 'maker'
        
        if side_b == 'BUY':
            method_b = 'maker'
        elif side_b == 'SELL':
            method_b = 'taker'

        self.method = f'{method_a}-{method_b}'
        self.buy = buy
        self.sell = sell


class OneExTwoCoin:
    def __init__(self, exchange, profit, pair, side_a, side_b, price, buy, sell): 
        self.exchange = exchange
        self.pair = pair
        self.profit = profit
        
        if side_a == 'BUY':
            method_a = 'taker'
        elif side_a == 'SELL':
            method_a = 'maker'
        
        if side_b == 'BUY':
            method_b = 'maker'
        elif side_b == 'SELL':
            method_b = 'taker'

        self.method = f'{method_a}-{method_b}'
        self.price = price
        self.buy = buy
        self.sell = sell


class TwoExTwoCoin:
    def __init__(self, exchange_a, exchange_b, profit, pair, side_a, side_b, price, buy, sell, pair_exchange): 
        self.exchange_a = exchange_a
        self.exchange_b = exchange_b
        self.pair = pair
        self.profit = profit
        
        if side_a == 'BUY':
            method_a = 'taker'
        elif side_a == 'SELL':
            method_a = 'maker'
        
        if side_b == 'BUY':
            method_b = 'maker'
        elif side_b == 'SELL':
            method_b = 'taker'

        self.method = f'{method_a}-{method_b}'
        self.price = price
        self.buy = buy
        self.sell = sell
        self.pair_exchange = pair_exchange


def p2p_settings_text(p2p_settings):
    banks_text = ''
    for bank in p2p_settings[3]:
        banks_text += f'{config.banks[bank]}, '
    banks_text = banks_text.rstrip(', ')

    amount = 'не задана'
    if p2p_settings[4] != 0:
        amount = '{:,}'.format(p2p_settings[4]).replace(',', ' ')
    
    orders_count = 'не задано'
    if p2p_settings[5] != 0:
        orders_count = '{:,}'.format(p2p_settings[5]).replace(',', ' ')
    
    orders_rate = 'не задан'
    if p2p_settings[6] != 0:
        orders_rate = p2p_settings[6]

    if p2p_settings[2] == 'taker':
        method = 'купить'
    else:
        method = 'продать'

    reply_text = f'''
                    \nТекущие настройки для р2р:\
                    \nБиржа: *{p2p_settings[0].capitalize()}*\
                    \nМонета: *{p2p_settings[1]}*\
                    \nСпособ: *{method}*\
                    \nБанк(и): *{banks_text}*\
                    \nСумма: *{amount}*\
                    \nКол-во ордеров: *{orders_count}*\
                    \nПроцент выполнения: *{orders_rate}*\
                    \n\
                    \nДля изменения настроек воспользуйтесь командами:\
                    \n*/a <значение>*\
                    \n*/o <значение>*\
                    \n*/r <значение>*\
    '''
    return reply_text


def p2p_search(p2p_settings):
    exchange = p2p_settings[0]
    coin = p2p_settings[1]

    method = p2p_settings[2]
    if method == 'taker':
        side = 'BUY'
    elif method == 'maker':
        side = 'SELL'

    banks = p2p_settings[3]

    amount = p2p_settings[4]
    if amount == 0:
        amount = ''

    orders = p2p_settings[5]
    rate = p2p_settings[6]
    currency = config.currency_data[exchange]

    database = sqlite3.connect("arbitrage.db")
    cursor = database.cursor()

    coin = cursor.execute(f"SELECT system FROM coins WHERE name='{exchange}' and coin='{coin}'").fetchall()[0][0]
    side = cursor.execute(f"SELECT system FROM side WHERE name='{exchange}' and side='{side}'").fetchall()[0][0]
    banks_request = []
    for bank in banks:
        bank = cursor.execute(f"SELECT system FROM banks WHERE name='{exchange}' and bank='{bank}'").fetchall()[0][0]
        banks_request.append(bank)
    
    if exchange == 'BINANCE':
        result = p2p_binance_search(coin, banks_request, side, currency, amount, orders, rate)
    elif exchange == 'HUOBI':
        result = p2p_huobi_search(coin, banks_request, side, currency, amount, orders, rate)
    elif exchange == 'BYBIT':
        result = p2p_bybit_search(coin, banks_request, side, currency, amount, orders, rate)
    
    if result != 'Ошибка соединения':
        reply_text = p2p_settings_text(p2p_settings).replace('\n*/r <значение>*', '')\
            .replace('\n*/o <значение>*', '').replace('\n*/a <значение>*', '')\
                .replace('\nДля изменения настроек воспользуйтесь командами:', '')
        if result != []:
            for num, deal in enumerate(result):
                min = '{:,}'.format(deal.min).replace(',', ' ')
                max = '{:,}'.format(deal.max).replace(',', ' ')
                price = '{:,}'.format(deal.price).replace(',', ' ')
                orders = '{:,}'.format(deal.orders).replace(',', ' ')
                rate = round(deal.rate, 2)
                add_text = f'''\n{num + 1}. *{deal.nick}*:\
                            \nЦена: *{price} RUB*\
                            \nЛимиты: *{min} - {max}*\
                            \nКол-во ордеров: *{orders} ({rate}%)*\
                            \nCпособы оплаты: *{deal.banks}*\
                            \n\
                '''
                reply_text += add_text
            reply_text = reply_text.rstrip('\n')
        else:
            reply_text += 'Не найдено ордеров с заданными параметрами.'

        return reply_text

    else:
        return 'Ошибка соединения'


def p2p_binance_search(coin, banks, side, currency, amount=0, orders=0, rate=0):

    data_binance = {
        "asset": coin,
        "countries": [],
        "fiat": currency,
        "page": 1,
        "proMerchantAds": False,
        "publisherType": None,
        "rows": 20,
        "tradeType": side,
        "transAmount": amount,
        "payTypes" : banks
    }
    try:
        deals = requests.post(url=config.url_binance, json=data_binance, headers=headers).json().get('data')
    except:
        return 'Ошибка соединения'
    
    if deals is None:
        return 'Ошибка соединения'
    
    final_deals = []
    for deal in deals:
        order_count = int(deal.get('advertiser').get('monthOrderCount'))
        finish_rate = float(deal.get('advertiser').get('monthFinishRate')) * 100
        if order_count >= orders and finish_rate >= rate:
            nick = deal.get('advertiser').get('nickName')
            min = int(float(deal.get('adv').get('minSingleTransAmount')))
            max = int(float(deal.get('adv').get('maxSingleTransAmount')))
            price = float(deal.get('adv').get('price'))

            final_banks = []
            adv_banks = deal.get('adv').get('tradeMethods')
            for bank in adv_banks:
                final_banks.append(bank.get('tradeMethodName'))
            final_banks = (', ').join(final_banks)

            adv = Deal(nick, price, max, min, order_count, finish_rate, final_banks)
            final_deals.append(adv)

        if len(final_deals) == 3:
            break

    return final_deals


def p2p_huobi_search(coin, banks, side, currency, amount=0, orders=0, rate=0):

    params_huobi = {
        'coinId': coin,
        'currency': currency,
        'tradeType': side,
        'currPage': 1,
        'payMethod': banks,
        'acceptOrder': 0,
        'blockType' : 'general',
        'online': 1,
        'range': 0,
        'amount' : amount,
        'isThumbsUp': False,
        'isMerchant': False,
        'isTraded': False,
        'onlyTradable': True,
        'isFollowed' : False
    }

    try:
        deals = requests.get(url=config.url_huobi, params=params_huobi, headers=headers).json().get('data')
    except:
        return 'Ошибка соединения'
    
    if deals is None:
        return 'Ошибка соединения'
    
    final_deals = []
    for deal in deals:
        order_count = int(deal.get('tradeMonthTimes'))
        finish_rate = float(deal.get('orderCompleteRate'))
        if order_count >= orders and finish_rate >= rate:
            nick = deal.get('userName')
            min = int(float(deal.get('minTradeLimit')))
            max = int(float(deal.get('maxTradeLimit')))
            price = float(deal.get('price'))

            final_banks = []
            adv_banks = deal.get('payMethods')
            for bank in adv_banks:
                final_banks.append(bank.get('name'))
            final_banks = (', ').join(final_banks)

            adv = Deal(nick, price, max, min, order_count, finish_rate, final_banks)
            final_deals.append(adv)
        
        if len(final_deals) == 3:
            break

    return final_deals


def p2p_bybit_search(coin, banks, side, currency, amount=0, orders=0, rate=0):
    
    data_bybit = {
        'tokenId': coin, 
        'currencyId': currency, 
        'payment': banks,
        'amount' : amount,
        'side' : side,
    }

    try:
        deals = requests.post(url=config.url_bybit, data=data_bybit, headers=headers).json().get('result').get('items')
    except:
        return 'Ошибка соединения'
    
    if deals is None:
        return 'Ошибка соединения'
    
    final_deals = []
    for deal in deals:
        order_count = int(deal.get('recentOrderNum'))
        finish_rate = float(deal.get('recentExecuteRate'))
        if order_count >= orders and finish_rate >= rate:
            nick = deal.get('nickName')
            min = int(float(deal.get('minAmount')))
            max = int(float(deal.get('maxAmount')))
            price = float(deal.get('price'))

            final_banks = []
            adv_banks = deal.get('payments')

            database = sqlite3.connect("arbitrage.db")
            cursor = database.cursor()

            for bank in adv_banks:
                try:
                    bank_name = cursor.execute(f"SELECT bank FROM banks WHERE name='BYBIT' and system='{bank}'").fetchall()[0][0]
                    final_banks.append(config.banks[bank_name])
                except:
                    pass
            final_banks = (', ').join(final_banks)

            adv = Deal(nick, price, max, min, order_count, finish_rate, final_banks)
            final_deals.append(adv)
        
        if len(final_deals) == 3:
            break

    return final_deals


def spot_search(exchange, pair):
    pair = pair.replace('/', '')

    price = 'a'
    if exchange == 'BINANCE':
        url = f'{config.url_binance_spot}{pair}'
        try:
            price = float(requests.get(url).json().get('price'))
        except:
            pass
    elif exchange == 'HUOBI':
        pair_lower = pair.lower()
        url = f'{config.url_huobi_spot}{pair_lower}'
        try:
            price = float(requests.get(url).json().get('tick').get('ask')[0])
        except:
            pass
    elif exchange == 'BYBIT':
        url = f'{config.url_bybit_spot}{pair}'
        try:    
            price = float(requests.get(url).json().get('result')[0].get('ask_price'))
        except:
            pass

    if price == 'a':
        return 'Ошибка соединения', None
    else:
        reply_text = f'''
                            \nКурс на пару *{pair}* ({exchange.capitalize()}):\
                            \n*{'{:,}'.format(price).replace(',', ' ')}*\
                            \n\
                            \nВоспользуйтесь командой:\
                            \n/t <значение>
                '''
        return price, reply_text


def spot_price(spot_settings, trade):
    pairs_currency = spot_settings[1].split('/')
    currency_a = pairs_currency[0]
    currency_b = pairs_currency[1]

    exchange = spot_settings[0]
    price = spot_settings[2]

    amount = price * trade * 0.999

    if currency_a != 'BTC':
        trade = round(trade, 2)
    if currency_b != 'BTC':
        amount = round(amount, 2)

    reply_text = f'''
                \nНа бирже *{exchange.capitalize()}*:\
                \n{'{:,}'.format(trade).replace(',', ' ')} {currency_a} = {'{:,}'.format(amount).replace(',', ' ')} {currency_b}
    '''
    return reply_text


def settings_text(bonds_settings):
    exchanges = ''
    for exchange in bonds_settings[0]:
        exchanges += f'{exchange.capitalize()}, '
    exchanges = exchanges.rstrip(', ')
    if bonds_settings[0] == []:
        exchanges = 'не выбраны'

    banks = ''
    for bank in bonds_settings[1]:
        banks += f'{config.banks[bank]}, '
    banks = banks.rstrip(', ')
    if bonds_settings[1] == []:
        banks = 'не выбраны'

    methods = ''
    for method in bonds_settings[2]:
        methods += f'{method}, '
    methods = methods.rstrip(', ')
    if bonds_settings[2] == []:
        methods = 'не выбраны'

    amount = 'не задана'
    if bonds_settings[3] != '':
        amount = '{:,}'.format(bonds_settings[3]).replace(',', ' ')
    
    orders_count = 'не задано'
    if bonds_settings[4] != '':
        orders_count = '{:,}'.format(bonds_settings[4]).replace(',', ' ')
    
    orders_rate = 'не задан'
    if bonds_settings[5] != '':
        orders_rate = bonds_settings[5]

    coins = 'не заданы'
    if bonds_settings[6] != []:
        coins = (', ').join(bonds_settings[6])

    reply_text = f'''
                    \nТекущие настройки поиска связок:\
                    \nБиржи: *{exchanges}*\
                    \nСпособы: *{methods}*\
                    \nБанки: *{banks}*\
                    \nСумма: *{amount}*\
                    \nКол-во ордеров: *{orders_count}*\
                    \nПроцент выполнения: *{orders_rate}*\
                    \nМонеты: *{coins}*\
                    \n\
                    \nДля изменения настроек воспользуйтесь командами:\
                    \n*/sa <значение>*\
                    \n*/so <значение>*\
                    \n*/sr <значение>*\
    '''
    return reply_text


def settings_alarm_text(bonds_settings):
    exchanges = ''
    for exchange in bonds_settings[0]:
        exchanges += f'{exchange.capitalize()}, '
    exchanges = exchanges.rstrip(', ')
    if bonds_settings[0] == []:
        exchanges = 'не выбраны'

    banks = ''
    for bank in bonds_settings[1]:
        banks += f'{config.banks[bank]}, '
    banks = banks.rstrip(', ')
    if bonds_settings[1] == []:
        banks = 'не выбраны'

    methods = ''
    for method in bonds_settings[2]:
        methods += f'{method}, '
    methods = methods.rstrip(', ')
    if bonds_settings[2] == []:
        methods = 'не выбраны'

    amount = 'не задана'
    if bonds_settings[3] != '':
        amount = '{:,}'.format(bonds_settings[3]).replace(',', ' ')
    
    orders_count = 'не задано'
    if bonds_settings[4] != '':
        orders_count = '{:,}'.format(bonds_settings[4]).replace(',', ' ')
    
    orders_rate = 'не задан'
    if bonds_settings[5] != '':
        orders_rate = bonds_settings[5]
    
    coins = 'не заданы'
    if bonds_settings[6] != []:
        coins = (', ').join(bonds_settings[6])

    reply_text = f'''
                    \nТекущие настройки поиска связок (уведомления):\
                    \nБиржи: *{exchanges}*\
                    \nСпособы: *{methods}*\
                    \nБанки: *{banks}*\
                    \nСумма: *{amount}*\
                    \nКол-во ордеров: *{orders_count}*\
                    \nПроцент выполнения: *{orders_rate}*\
                    \nМонеты: *{coins}*\
                    \n\
                    \nДля изменения настроек воспользуйтесь командами:\
                    \n*/aa <значение>*\
                    \n*/ao <значение>*\
                    \n*/ar <значение>*\
    '''
    return reply_text


def bonds_text(profit_bonds):
    replies = []
    reply_text = ''
    counter = 0
    bonds_num = len(profit_bonds)
    for num, bond in enumerate(profit_bonds):
        counter += 1
        if isinstance(bond, OneExOneCoin):
            reply_text += f'''
                    \n*{num + 1}. {bond.exchange}, {bond.coin}, {bond.method}:*\
                    \nBUY *{bond.coin}*: *{bond.buy.nick} - {'{:,}'.format(bond.buy.price).replace(',', ' ')}*, {bond.buy.banks}, ({'{:,}'.format(bond.buy.orders).replace(',', ' ')}, {'{:,}'.format(bond.buy.rate).replace(',', ' ')}%)\
                    \nSELL *{bond.coin}*: *{bond.sell.nick} - {'{:,}'.format(bond.sell.price).replace(',', ' ')}*, {bond.sell.banks}, ({'{:,}'.format(bond.sell.orders).replace(',', ' ')}, {'{:,}'.format(bond.sell.rate).replace(',', ' ')}%)\
                    \nПрофит: *{round(bond.profit,3)}%*'''

        elif isinstance(bond, OneExTwoCoin):
            if bond.pair not in config.pairs_spot[bond.exchange]:
                coins = bond.pair.split('/')
                coin_a = coins[0]
                coin_b = coins[1]
                pair = f'{coin_b}/{coin_a}'
                price = 1 / bond.price

            else:
                pair = bond.pair
                price = bond.price

            reply_text += f'''
                    \n*{num + 1}. {bond.exchange}, {pair} ({'{:,}'.format(price).replace(',', ' ')}), {bond.method}:*\
                    \nBUY *{bond.buy.coin}*: *{bond.buy.nick} - {'{:,}'.format(bond.buy.price).replace(',', ' ')}*, {bond.buy.banks}, ({'{:,}'.format(bond.buy.orders).replace(',', ' ')}, {'{:,}'.format(bond.buy.rate).replace(',', ' ')}%)\
                    \nSELL *{bond.sell.coin}*: *{bond.sell.nick} - {'{:,}'.format(bond.sell.price).replace(',', ' ')}*, {bond.sell.banks}, ({'{:,}'.format(bond.sell.orders).replace(',', ' ')}, {'{:,}'.format(bond.sell.rate).replace(',', ' ')}%)\
                    \nПрофит: *{round(bond.profit,3)}%*'''

        elif isinstance(bond, TwoExOneCoin):
            reply_text += f'''
                    \n*{num + 1}. {bond.exchange_a} -> {bond.exchange_b}, {bond.coin}, {bond.method}:*\
                    \nBUY *{bond.coin}*: *{bond.buy.nick} - {'{:,}'.format(bond.buy.price).replace(',', ' ')}*, {bond.buy.banks}, ({'{:,}'.format(bond.buy.orders).replace(',', ' ')}, {'{:,}'.format(bond.buy.rate).replace(',', ' ')}%)\
                    \nSELL *{bond.coin}*: *{bond.sell.nick} - {'{:,}'.format(bond.sell.price).replace(',', ' ')}*, {bond.sell.banks}, ({'{:,}'.format(bond.sell.orders).replace(',', ' ')}, {'{:,}'.format(bond.sell.rate).replace(',', ' ')}%)\
                    \nПрофит: *{round(bond.profit,3)}%*'''

        elif isinstance(bond, TwoExTwoCoin):
            if bond.pair not in config.pairs_spot[bond.pair_exchange]:
                coins = bond.pair.split('/')
                coin_a = coins[0]
                coin_b = coins[1]
                pair = f'{coin_b}/{coin_a}'
                price = 1 / bond.price

            else:
                pair = bond.pair
                price = bond.price

            reply_text += f'''
                    \n*{num + 1}. {bond.exchange_a} -> {bond.exchange_b}, {pair} ({'{:,}'.format(price).replace(',', ' ')}), {bond.method}:*\
                    \nBUY *{bond.buy.coin}*: *{bond.buy.nick} - {'{:,}'.format(bond.buy.price).replace(',', ' ')}*, {bond.buy.banks}, ({'{:,}'.format(bond.buy.orders).replace(',', ' ')}, {'{:,}'.format(bond.buy.rate).replace(',', ' ')}%)\
                    \nSELL *{bond.sell.coin}*: *{bond.sell.nick} - {'{:,}'.format(bond.sell.price).replace(',', ' ')}*, {bond.sell.banks}, ({'{:,}'.format(bond.sell.orders).replace(',', ' ')}, {'{:,}'.format(bond.sell.rate).replace(',', ' ')}%)\
                    \nПрофит: *{round(bond.profit,3)}%*'''

        if counter == 10 or num == bonds_num - 1:
            reply_text = reply_text.rstrip('\n')
            replies.append(reply_text)
            reply_text = ''
            counter = 0

    return replies


def current_settings(bonds_settings):
    exchanges = ''
    for exchange in bonds_settings[0]:
        exchanges += f'{exchange.capitalize()}, '
    exchanges = exchanges.rstrip(', ')
    if bonds_settings[0] == []:
        exchanges = 'не выбраны'

    banks = ''
    for bank in bonds_settings[1]:
        banks += f'{config.banks[bank]}, '
    banks = banks.rstrip(', ')
    if bonds_settings[1] == []:
        banks = 'не выбраны'

    methods = ''
    for method in bonds_settings[2]:
        methods += f'{method}, '
    methods = methods.rstrip(', ')
    if bonds_settings[2] == []:
        methods = 'не выбраны'

    amount = 'не задана'
    if bonds_settings[3] != '':
        amount = '{:,}'.format(bonds_settings[3]).replace(',', ' ')
    
    orders_count = 'не задано'
    if bonds_settings[4] != '':
        orders_count = '{:,}'.format(bonds_settings[4]).replace(',', ' ')
    
    orders_rate = 'не задан'
    if bonds_settings[5] != '':
        orders_rate = bonds_settings[5]
    
    coins = 'не заданы'
    if bonds_settings[6] != []:
        coins = (', ').join(bonds_settings[6])

    reply_text = f'''
                    \nЗаданы следующие настройки поиска связок:\
                    \nБиржи: *{exchanges}*\
                    \nСпособы: *{methods}*\
                    \nБанки: *{banks}*\
                    \nСумма: *{amount}*\
                    \nКол-во ордеров: *{orders_count}*\
                    \nПроцент выполнения: *{orders_rate}*\
                    \nМонеты: *{coins}*
    '''
    return reply_text


def current_alarm_settings(bonds_settings):
    exchanges = ''
    for exchange in bonds_settings[0]:
        exchanges += f'{exchange.capitalize()}, '
    exchanges = exchanges.rstrip(', ')
    if bonds_settings[0] == []:
        exchanges = 'не выбраны'

    banks = ''
    for bank in bonds_settings[1]:
        banks += f'{config.banks[bank]}, '
    banks = banks.rstrip(', ')
    if bonds_settings[1] == []:
        banks = 'не выбраны'

    methods = ''
    for method in bonds_settings[2]:
        methods += f'{method}, '
    methods = methods.rstrip(', ')
    if bonds_settings[2] == []:
        methods = 'не выбраны'

    amount = 'не задана'
    if bonds_settings[3] != '':
        amount = '{:,}'.format(bonds_settings[3]).replace(',', ' ')
    
    orders_count = 'не задано'
    if bonds_settings[4] != '':
        orders_count = '{:,}'.format(bonds_settings[4]).replace(',', ' ')
    
    orders_rate = 'не задан'
    if bonds_settings[5] != '':
        orders_rate = bonds_settings[5]
    
    coins = 'не заданы'
    if bonds_settings[6] != []:
        coins = (', ').join(bonds_settings[6])

    reply_text = f'''
                    \nЗаданы следующие настройки поиска связок (с уведомлениями):\
                    \nБиржи: *{exchanges}*\
                    \nСпособы: *{methods}*\
                    \nБанки: *{banks}*\
                    \nСумма: *{amount}*\
                    \nКол-во ордеров: *{orders_count}*\
                    \nПроцент выполнения: *{orders_rate}*\
                    \nМонеты: *{coins}*
    '''
    return reply_text


def all_alarms(alarms):
    replies = []
    reply_text = ''
    counter = 0
    alarms_num = len(alarms)
    for num, alarm in enumerate(alarms):
        exchanges = ''
        for exchange in alarm[0]:
            exchanges += f'{exchange.capitalize()}, '
        exchanges = exchanges.rstrip(', ')
        if alarm[0] == []:
            exchanges = 'не выбраны'

        banks = ''
        for bank in alarm[1]:
            banks += f'{config.banks[bank]}, '
        banks = banks.rstrip(', ')
        if alarm[1] == []:
            banks = 'не выбраны'

        methods = ''
        for method in alarm[2]:
            methods += f'{method}, '
        methods = methods.rstrip(', ')
        if alarm[2] == []:
            methods = 'не выбраны'

        amount = 'не задана'
        if alarm[3] != '':
            amount = '{:,}'.format(alarm[3]).replace(',', ' ')
        
        orders_count = 'не задано'
        if alarm[4] != '':
            orders_count = '{:,}'.format(alarm[4]).replace(',', ' ')
        
        orders_rate = 'не задан'
        if alarm[5] != '':
            orders_rate = alarm[5]
        
        coins = 'не заданы'
        if alarm[6] != []:
            coins = (', ').join(alarm[6])
        
        reply_text += f'''
                    \n{num + 1}. Настройки для уведомлений:\
                    \nБиржи: *{exchanges}*\
                    \nСпособы: *{methods}*\
                    \nБанки: *{banks}*\
                    \nСумма: *{amount}*\
                    \nКол-во ордеров: *{orders_count}*\
                    \nПроцент выполнения: *{orders_rate}*\
                    \nМонеты: *{coins}*'''

        if counter == 5 or num == alarms_num - 1:
            reply_text = reply_text.rstrip('\n')
            replies.append(reply_text)
            reply_text = ''
            counter = 0

    return replies


def bonds_alarm_text(profit_bonds, bonds_settings):
    exchanges = ''
    for exchange in bonds_settings[0]:
        exchanges += f'{exchange.capitalize()}, '
    exchanges = exchanges.rstrip(', ')
    if bonds_settings[0] == []:
        exchanges = 'не выбраны'

    banks = ''
    for bank in bonds_settings[1]:
        banks += f'{config.banks[bank]}, '
    banks = banks.rstrip(', ')
    if bonds_settings[1] == []:
        banks = 'не выбраны'

    methods = ''
    for method in bonds_settings[2]:
        methods += f'{method}, '
    methods = methods.rstrip(', ')
    if bonds_settings[2] == []:
        methods = 'не выбраны'

    amount = 'не задана'
    if bonds_settings[3] != '':
        amount = '{:,}'.format(bonds_settings[3]).replace(',', ' ')
    
    orders_count = 'не задано'
    if bonds_settings[4] != '':
        orders_count = '{:,}'.format(bonds_settings[4]).replace(',', ' ')
    
    orders_rate = 'не задан'
    if bonds_settings[5] != '':
        orders_rate = bonds_settings[5]
    
    coins = 'не заданы'
    if bonds_settings[6] != []:
        coins = (', ').join(bonds_settings[6])

    reply_text = f'''
                    \nСработало уведомление для следующих настроек:\
                    \nБиржи: *{exchanges}*\
                    \nСпособы: *{methods}*\
                    \nБанки: *{banks}*\
                    \nСумма: *{amount}*\
                    \nКол-во ордеров: *{orders_count}*\
                    \nПроцент выполнения: *{orders_rate}*\
                    \nМонеты: *{coins}*'''
    
    replies = []
    counter = 0
    bonds_num = len(profit_bonds)
    for num, bond in enumerate(profit_bonds):
        counter += 1
        if isinstance(bond, OneExOneCoin):
            reply_text += f'''
                    \n*{num + 1}. {bond.exchange}, {bond.coin}, {bond.method}:*\
                    \nBUY *{bond.coin}*: *{bond.buy.nick} - {'{:,}'.format(bond.buy.price).replace(',', ' ')}*, {bond.buy.banks}, ({'{:,}'.format(bond.buy.orders).replace(',', ' ')}, {'{:,}'.format(bond.buy.rate).replace(',', ' ')}%)\
                    \nSELL *{bond.coin}*: *{bond.sell.nick} - {'{:,}'.format(bond.sell.price).replace(',', ' ')}*, {bond.sell.banks}, ({'{:,}'.format(bond.sell.orders).replace(',', ' ')}, {'{:,}'.format(bond.sell.rate).replace(',', ' ')}%)\
                    \nПрофит: *{round(bond.profit,3)}%*'''

        elif isinstance(bond, OneExTwoCoin):
            if bond.pair not in config.pairs_spot[bond.exchange]:
                coins = bond.pair.split('/')
                coin_a = coins[0]
                coin_b = coins[1]
                pair = f'{coin_b}/{coin_a}'
                price = 1 / bond.price

            else:
                pair = bond.pair
                price = bond.price

            reply_text += f'''
                    \n*{num + 1}. {bond.exchange}, {pair} ({'{:,}'.format(price).replace(',', ' ')}), {bond.method}:*\
                    \nBUY *{bond.buy.coin}*: *{bond.buy.nick} - {'{:,}'.format(bond.buy.price).replace(',', ' ')}*, {bond.buy.banks}, ({'{:,}'.format(bond.buy.orders).replace(',', ' ')}, {'{:,}'.format(bond.buy.rate).replace(',', ' ')}%)\
                    \nSELL *{bond.sell.coin}*: *{bond.sell.nick} - {'{:,}'.format(bond.sell.price).replace(',', ' ')}*, {bond.sell.banks}, ({'{:,}'.format(bond.sell.orders).replace(',', ' ')}, {'{:,}'.format(bond.sell.rate).replace(',', ' ')}%)\
                    \nПрофит: *{round(bond.profit,3)}%*'''

        elif isinstance(bond, TwoExOneCoin):
            reply_text += f'''
                    \n*{num + 1}. {bond.exchange_a} -> {bond.exchange_b}, {bond.coin}, {bond.method}:*\
                    \nBUY *{bond.coin}*: *{bond.buy.nick} - {'{:,}'.format(bond.buy.price).replace(',', ' ')}*, {bond.buy.banks}, ({'{:,}'.format(bond.buy.orders).replace(',', ' ')}, {'{:,}'.format(bond.buy.rate).replace(',', ' ')}%)\
                    \nSELL *{bond.coin}*: *{bond.sell.nick} - {'{:,}'.format(bond.sell.price).replace(',', ' ')}*, {bond.sell.banks}, ({'{:,}'.format(bond.sell.orders).replace(',', ' ')}, {'{:,}'.format(bond.sell.rate).replace(',', ' ')}%)\
                    \nПрофит: *{round(bond.profit,3)}%*'''

        elif isinstance(bond, TwoExTwoCoin):
            if bond.pair not in config.pairs_spot[bond.pair_exchange]:
                coins = bond.pair.split('/')
                coin_a = coins[0]
                coin_b = coins[1]
                pair = f'{coin_b}/{coin_a}'
                price = 1 / bond.price

            else:
                pair = bond.pair
                price = bond.price

            reply_text += f'''
                    \n*{num + 1}. {bond.exchange_a} -> {bond.exchange_b}, {pair} ({'{:,}'.format(price).replace(',', ' ')}), {bond.method}:*\
                    \nBUY *{bond.buy.coin}*: *{bond.buy.nick} - {'{:,}'.format(bond.buy.price).replace(',', ' ')}*, {bond.buy.banks}, ({'{:,}'.format(bond.buy.orders).replace(',', ' ')}, {'{:,}'.format(bond.buy.rate).replace(',', ' ')}%)\
                    \nSELL *{bond.sell.coin}*: *{bond.sell.nick} - {'{:,}'.format(bond.sell.price).replace(',', ' ')}*, {bond.sell.banks}, ({'{:,}'.format(bond.sell.orders).replace(',', ' ')}, {'{:,}'.format(bond.sell.rate).replace(',', ' ')}%)\
                    \nПрофит: *{round(bond.profit,3)}%*'''

        if counter == 10 or num == bonds_num - 1:
            reply_text = reply_text.rstrip('\n')
            replies.append(reply_text)
            reply_text = ''
            counter = 0

    return replies
