import copy
import config
import time
import sqlite3
import asyncio
import itertools
import telebot
import datetime
from aiohttp import ClientSession

from functions import bonds_text, bonds_alarm_text, OneExOneCoin, OneExTwoCoin, TwoExOneCoin, TwoExTwoCoin, Pair, Coin
from keyboards import taker_alarm

bot = telebot.TeleBot(config.TG_TOKEN)


async def start_bonds(bonds_settings):
    while True:
        if config.settings_flag is False:
            break

        pairs_spot = config.pairs_spot
        coins = config.coins
        amount = bonds_settings[3]

        tasks_pairs = []
        tasks_coins = []
        for exchange, pairs in pairs_spot.items():
            for pair in pairs:
                tasks_pairs.append(asyncio.create_task(get_pairs(exchange, pair, bonds_settings)))
        for exchange, coins in coins.items():
            for coin in coins:
                tasks_coins.append(asyncio.create_task(get_coins(exchange, coin, bonds_settings)))

        try:
            pairs_prices = await asyncio.gather(*tasks_pairs)
        except:
            pairs_prices = []
        
        try:
            coins_prices = await asyncio.gather(*tasks_coins)
        except:
            coins_prices = []

        while 0 in pairs_prices:
            pairs_prices.remove(0)

        try:
            pairs_prices = list(itertools.chain.from_iterable(pairs_prices))
            coins_prices = list(itertools.chain.from_iterable(coins_prices))
        except Exception as ex:
            print(ex)
            pairs_prices = []
            coins_prices = []

        while 0 in coins_prices:
            coins_prices.remove(0)

        if pairs_prices != [] or coins_prices != []:
            all_bonds = bonds(pairs_prices, coins_prices, amount)
            methods = bonds_settings[2]
            settings_coins = bonds_settings[6]
            profit_bonds = []
            
            for bond in all_bonds:
                if bond.method in methods:
                    if (bond.buy.coin in settings_coins) and (bond.sell.coin in settings_coins):
                        profit_bonds.append(bond)

            config.profit_bonds = copy.deepcopy(profit_bonds)
        
        if config.settings_flag is False:
            break
        
        time.sleep(15)


async def start_alarm_bonds(bonds_settings):
    config.alarms.append(bonds_settings)
    while True:
        if config.settings_alarm_flag is False:
            config.alarms.remove(bonds_settings)
            break

        counter = 0
        for alarm in config.alarms:
            if alarm == bonds_settings:
                counter = 1
                break

        if counter == 0:
            break

        pairs_spot = config.pairs_spot
        coins = config.coins
        amount = bonds_settings[3]

        tasks_pairs = []
        tasks_coins = []
        for exchange, pairs in pairs_spot.items():
            for pair in pairs:
                tasks_pairs.append(asyncio.create_task(get_pairs(exchange, pair, bonds_settings)))
        for exchange, coins in coins.items():
            for coin in coins:
                tasks_coins.append(asyncio.create_task(get_coins(exchange, coin, bonds_settings)))

        try:
            pairs_prices = await asyncio.gather(*tasks_pairs)
        except:
            pairs_prices = []
        
        try:
            coins_prices = await asyncio.gather(*tasks_coins)
        except:
            coins_prices = []

        while 0 in pairs_prices:
            pairs_prices.remove(0)

        try:
            pairs_prices = list(itertools.chain.from_iterable(pairs_prices))
            coins_prices = list(itertools.chain.from_iterable(coins_prices))
        except Exception as ex:
            print(ex)
            pairs_prices = []
            coins_prices = []

        while 0 in coins_prices:
            coins_prices.remove(0)

        if pairs_prices != [] or coins_prices != []:
            profit_bonds = bonds(pairs_prices, coins_prices, amount)

            if profit_bonds != []:

                methods = bonds_settings[2]
                settings_coins = bonds_settings[6]
                final_profit_bonds = []
                
                for bond in profit_bonds:
                    if bond.method in methods and bond.profit <= 2.5:
                        if (bond.buy.coin in settings_coins) and (bond.sell.coin in settings_coins):
                            final_profit_bonds.append(bond)

                if final_profit_bonds != []:
                    final_profit_bonds = sorted(final_profit_bonds, key=lambda x: x.profit)[::-1]
                    replies = bonds_alarm_text(final_profit_bonds, bonds_settings)

                    if methods != ['taker-taker']:
                        for reply in replies:
                            bot.send_message(config.main_user, text=reply, parse_mode='Markdown')

                        config.alarms.remove(bonds_settings)
                        break

                    else:
                        reply = replies[0]
                        message_id = ''

                        for id, settings in config.taker.items():
                            if settings == bonds_settings:
                                message_id = id
                                break
                            
                        refresh_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime('%d.%m.%y %H:%M:%S')
                        if message_id == '':
                            reply = f'Сработало *{refresh_time}*{reply}'
                            alarm_message = bot.send_message(config.main_user, text=reply, reply_markup=taker_alarm(bonds_settings), parse_mode='Markdown')
                            bot.pin_chat_message(config.main_user, alarm_message.message_id, True)
                            config.taker[alarm_message.message_id] = bonds_settings
                        else:
                            reply = f'Обновлено *{refresh_time}*{reply}'
                            bot.edit_message_text(chat_id=config.main_user, message_id=message_id, text=reply, parse_mode='Markdown')
                            bot.edit_message_reply_markup(chat_id=config.main_user, message_id=message_id, reply_markup=taker_alarm(bonds_settings))

        if config.settings_alarm_flag is False:
            config.alarms.remove(bonds_settings)
            break
        
        time.sleep(15)


async def get_pairs(exchange, pair, bonds_settings):
    coins = pair.split('/')
    coin_a = coins[0]
    coin_b = coins[1]

    settings_exchanges = bonds_settings[0]

    pair_symbol = pair.replace('/', '')

    if exchange == 'BINANCE' and exchange in settings_exchanges:
        url_binance_spot = f'{config.url_binance_spot}{pair_symbol}'
        try:
            async with ClientSession() as session:
                async with session.get(url=url_binance_spot, ssl=False) as response:
                    price_json = await response.json()
                    price = float(price_json.get('price'))
                    return Pair(exchange, price, coin_a, coin_b, pair), Pair(exchange, 1/price, coin_b, coin_a, f'{coin_b}/{coin_a}')
        except Exception as ex:
            pass

    elif exchange == 'HUOBI' and exchange in settings_exchanges:
        pair_symbol = pair_symbol.lower()
        url_huobi_spot = f'{config.url_huobi_spot}{pair_symbol}'
        try:
            async with ClientSession() as session:
                async with session.get(url=url_huobi_spot, ssl=False) as response:
                    price_json = await response.json()
                    price = float(price_json.get('tick').get('ask')[0])
                    return Pair(exchange, price, coin_a, coin_b, pair), Pair(exchange, 1/price, coin_b, coin_a, f'{coin_b}/{coin_a}')
        except:
            pass

    elif exchange == 'BYBIT' and exchange in settings_exchanges:
        url_bybit_spot = f'{config.url_bybit_spot}{pair_symbol}'
        try:
            async with ClientSession() as session:
                async with session.get(url=url_bybit_spot, ssl=False) as response:
                    price_json = await response.json()
                    price = float(price_json.get('result')[0].get('ask_price'))
                    return Pair(exchange, price, coin_a, coin_b, pair), Pair(exchange, 1/price, coin_b, coin_a, f'{coin_b}/{coin_a}')
        except:
            pass

    return 0


async def get_coins(exchange, coin, bonds_settings):
    headers = {
        'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
        'origin' : 'https://www.bybit.com'
    }
    database = sqlite3.connect("arbitrage.db")
    cursor = database.cursor()

    settings_exchanges = bonds_settings[0]
    settings_banks = bonds_settings[1]
    settings_methods = bonds_settings[2]
    settings_amount = bonds_settings[3]
    settings_orders = bonds_settings[4]
    settings_rate = bonds_settings[5]

    if settings_orders == '':
        settings_orders = 0
    
    if settings_rate == '':
        settings_rate = 0

    currency = config.currency_data[exchange]
    banks_request = []
    for bank in config.banks:
        if bank in settings_banks:
            bank = cursor.execute(f"SELECT system FROM banks WHERE name='{exchange}' and bank='{bank}'").fetchall()[0][0]
            banks_request.append(bank)

    coin_symbol = cursor.execute(f"SELECT system FROM coins WHERE name='{exchange}' and coin='{coin}'").fetchall()[0][0]
        
    buy_price = 0
    sell_price = 0
    if exchange == 'BINANCE' and exchange in settings_exchanges:

        for side in config.sides:
            side_symbol = cursor.execute(f"SELECT system FROM side WHERE name='{exchange}' and side='{side}'").fetchall()[0][0]

            data_binance = {
                "asset": coin_symbol,
                "countries": [],
                "fiat": currency,
                "page": 1,
                "proMerchantAds": False,
                "publisherType": None,
                "rows": 20,
                "tradeType": side_symbol,
                "transAmount": settings_amount,
                "payTypes" : banks_request
            }
            try:
                async with ClientSession() as session:
                    async with session.post(url=config.url_binance, json=data_binance, headers=headers, ssl=False) as response:
                        deals_json = await response.json()
                        deals = deals_json.get('data')
            except:
                deals = []

            if deals != [] and deals is not None:
                for deal in deals:
                    order_count = int(deal.get('advertiser').get('monthOrderCount'))
                    finish_rate = float(deal.get('advertiser').get('monthFinishRate')) * 100
                    if order_count >= settings_orders and finish_rate >= settings_rate:
                        price = float(deal.get('adv').get('price'))
                        nick = deal.get('advertiser').get('nickName')

                        final_banks = []
                        adv_banks = deal.get('adv').get('tradeMethods')
                        for bank in adv_banks:
                            final_banks.append(bank.get('tradeMethodName'))
                        final_banks = (', ').join(final_banks)

                        if side == 'BUY':
                            buy_price = Coin(exchange, coin, price, side, nick, order_count, finish_rate, final_banks)
                        elif side == 'SELL':
                            sell_price = Coin(exchange, coin, price, side, nick, order_count, finish_rate, final_banks)
                        break

    elif exchange == 'HUOBI' and exchange in settings_exchanges:
        for side in config.sides:
            side_symbol = cursor.execute(f"SELECT system FROM side WHERE name='{exchange}' and side='{side}'").fetchall()[0][0]
            params_huobi = {
                'coinId': coin_symbol,
                'currency': currency,
                'tradeType': side_symbol,
                'currPage': 1,
                'payMethod': banks_request,
                'acceptOrder': 0,
                'blockType' : 'general',
                'online': 1,
                'range': 0,
                'amount' : settings_amount,
            }
            try:
                async with ClientSession() as session:
                    async with session.get(url=config.url_huobi, params=params_huobi, headers=headers, ssl=False) as response:
                        deals_json = await response.json()
                        deals = deals_json.get('data')
            except Exception as ex:
                print(ex)
                deals = []
            
            if deals != [] and deals is not None:
                for deal in deals:
                    order_count = int(deal.get('tradeMonthTimes'))
                    finish_rate = float(deal.get('orderCompleteRate'))
                    if order_count >= settings_orders and finish_rate >= settings_rate:
                        nick = deal.get('userName')
                        price = float(deal.get('price'))

                        final_banks = []
                        adv_banks = deal.get('payMethods')
                        for bank in adv_banks:
                            final_banks.append(bank.get('name'))
                        final_banks = (', ').join(final_banks)

                        if side == 'BUY':
                            buy_price = Coin(exchange, coin, price, side, nick, order_count, finish_rate, final_banks)
                        elif side == 'SELL':
                            sell_price = Coin(exchange, coin, price, side, nick, order_count, finish_rate, final_banks)
                        break

    elif exchange == 'BYBIT' and exchange in settings_exchanges:
        for side in config.sides:
            side_symbol = cursor.execute(f"SELECT system FROM side WHERE name='{exchange}' and side='{side}'").fetchall()[0][0]
            data_bybit = {
                'tokenId': coin_symbol, 
                'currencyId': currency, 
                'payment': banks_request,
                'amount' : settings_amount,
                'side' : side_symbol,
            }
            try:
                async with ClientSession() as session:
                    async with session.post(url=config.url_bybit, data=data_bybit, headers=headers, ssl=False) as response:
                        deals_json = await response.json()
                        deals = deals_json.get('result').get('items')
            except:
                deals =[]
            
            if deals != [] and deals is not None:
                for deal in deals:
                    order_count = int(deal.get('recentOrderNum'))
                    finish_rate = float(deal.get('recentExecuteRate'))
                    if order_count >= settings_orders and finish_rate >= settings_rate:
                        price = float(deal.get('price'))
                        nick = deal.get('nickName')

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

                        if side == 'BUY':
                            buy_price = Coin(exchange, coin, price, side, nick, order_count, finish_rate, final_banks)
                        elif side == 'SELL':
                            sell_price = Coin(exchange, coin, price, side, nick, order_count, finish_rate, final_banks)
                        break

    return buy_price, sell_price


def bonds(pairs_prices, coins_prices, amount):
    profit_bonds = []
    one_coin_one_exchange = []
    for exchange, coins in config.coins.items():
        for coin in coins:
            prices = []
            for coin_price in coins_prices:
                if coin_price.coin == coin and coin_price.exchange == exchange:
                    prices.append(coin_price)

            prices = itertools.permutations(prices, 2)
            for price in prices:
                coeff_a = 1
                coeff_b = 1
                if exchange == 'BINANCE':
                    if price[0].side == 'SELL':
                        coeff_a = 0.999
                    if price[1].side == 'BUY':
                        coeff_b = 0.999
                profit = (1 / price[0].price * coeff_a * price[1].price * coeff_b - 1) / 1 * 100
                if profit >= 0.1:
                    one_coin_one_exchange.append(OneExOneCoin(exchange, coin, profit, price[0].side, price[1].side, price[0], price[1]))
                    profit_bonds.append(OneExOneCoin(exchange, coin, profit, price[0].side, price[1].side, price[0], price[1]))

    one_coin_two_exchange = []
    prices = []
    for coin_price in coins_prices:
        if coin_price.coin == 'USDT':
            prices.append(coin_price)
    
    prices = itertools.permutations(prices, 2)
    for price in prices:
        if price[0].exchange != price[1].exchange:
            coeff_a = 1
            coeff_b = 1
            if price[0].exchange == 'BINANCE' and price[0].side == 'SELL':
                coeff_a = 0.999
            if price[1].exchange == 'BINANCE' and price[1].side == 'BUY':
                coeff_b = 0.999

            database = sqlite3.connect("arbitrage.db")
            cursor = database.cursor()

            coms = cursor.execute(f"SELECT coms FROM coms WHERE send='{price[0].exchange}' and reciev='{price[1].exchange}'").fetchall()[0][0]

            profit = ((amount / price[0].price * coeff_a - coms) * price[1].price * coeff_b - amount) / amount * 100
            # profit = (1 / price[0].price * coeff_a * price[1].price * coeff_b - 1) / 1 * 100
            if profit >= 0.1:
                one_coin_two_exchange.append(TwoExOneCoin(price[0].exchange, price[1].exchange, profit, price[0].side, price[1].side, price[0], price[1]))
                profit_bonds.append(TwoExOneCoin(price[0].exchange, price[1].exchange, profit, price[0].side, price[1].side, price[0], price[1]))

    two_coin_one_exchange = []
    for exchange, coins in config.coins.items():
        for coin in coins:
            for coin_price in coins_prices:
                if coin_price.coin == coin and coin_price.exchange == exchange:
                    for pair_price in pairs_prices:
                        if pair_price.exchange == exchange and pair_price.coin_a == coin_price.coin:
                            for second_coin in coins_prices:
                                if second_coin.exchange == exchange and second_coin.coin == pair_price.coin_b:
                                    coeff_a = 1
                                    coeff_b = 1
                                    if coin_price.exchange == 'BINANCE' and coin_price.side == 'SELL':
                                        coeff_a = 0.999
                                    if second_coin.exchange == 'BINANCE' and second_coin.side == 'BUY':
                                        coeff_b = 0.999
                                    profit = (1 / coin_price.price * coeff_a * pair_price.price * 0.999 * second_coin.price * coeff_b - 1) / 1 * 100
                                    if profit >= 0.1:
                                        two_coin_one_exchange.append(OneExTwoCoin(exchange, profit, pair_price.pair, coin_price.side, second_coin.side, pair_price.price, coin_price, second_coin))
                                        profit_bonds.append(OneExTwoCoin(exchange, profit, pair_price.pair, coin_price.side, second_coin.side, pair_price.price, coin_price, second_coin))

    two_coin_two_exchange = []
    for exchange, coins in config.coins.items():
        for coin in coins:
            if coin == 'USDT':
                for coin_price in coins_prices:
                    if coin_price.coin == coin and coin_price.exchange == exchange:
                        for pair_price in pairs_prices:
                            if pair_price.coin_a == coin and pair_price.exchange != exchange:
                                for second_coin in coins_prices:
                                    if second_coin.coin == pair_price.coin_b and second_coin.exchange == pair_price.exchange:
                                        coeff_a = 1
                                        coeff_b = 1
                                        if coin_price.exchange == 'BINANCE' and coin_price.side == 'SELL':
                                            coeff_a = 0.999
                                        if second_coin.exchange == 'BINANCE' and second_coin.side == 'BUY':
                                            coeff_b = 0.999
                                        
                                        database = sqlite3.connect("arbitrage.db")
                                        cursor = database.cursor()

                                        coms = cursor.execute(f"SELECT coms FROM coms WHERE send='{coin_price.exchange}' and reciev='{second_coin.exchange}'").fetchall()[0][0]

                                        profit = ((amount / coin_price.price * coeff_a - coms) * pair_price.price * 0.999 * second_coin.price * coeff_b - amount) / amount * 100
                                        # profit = (1 / coin_price.price * coeff_a * pair_price.price * 0.999 * second_coin.price * coeff_b - 1) / 1 * 100
                                        if profit >= 0.1:
                                            two_coin_two_exchange.append(TwoExTwoCoin(coin_price.exchange, second_coin.exchange, profit, pair_price.pair, coin_price.side, second_coin.side, pair_price.price, coin_price, second_coin, pair_price.exchange))
                                            profit_bonds.append(TwoExTwoCoin(coin_price.exchange, second_coin.exchange, profit, pair_price.pair, coin_price.side, second_coin.side, pair_price.price, coin_price, second_coin, pair_price.exchange))

            elif coin != 'USDT':
                for coin_price in coins_prices:
                    if coin_price.coin == coin and coin_price.exchange == exchange:
                        for pair_price in pairs_prices:
                            if pair_price.coin_b == 'USDT' and pair_price.exchange == exchange and pair_price.coin_a == coin:
                                for second_coin in coins_prices:
                                    if second_coin.coin == 'USDT' and second_coin.exchange != pair_price.exchange:
                                        coeff_a = 1
                                        coeff_b = 1
                                        if coin_price.exchange == 'BINANCE' and coin_price.side == 'SELL':
                                            coeff_a = 0.999
                                        if second_coin.exchange == 'BINANCE' and second_coin.side == 'BUY':
                                            coeff_b = 0.999
                                        
                                        database = sqlite3.connect("arbitrage.db")
                                        cursor = database.cursor()

                                        coms = cursor.execute(f"SELECT coms FROM coms WHERE send='{coin_price.exchange}' and reciev='{second_coin.exchange}'").fetchall()[0][0]

                                        profit = ((amount / coin_price.price * coeff_a * pair_price.price * 0.999 - coms) * second_coin.price * coeff_b - amount) / amount * 100
                                        # profit = (1 / coin_price.price * coeff_a * pair_price.price * 0.999 * second_coin.price * coeff_b - 1) / 1 * 100
                                        if profit >= 0.1:
                                            two_coin_two_exchange.append(TwoExTwoCoin(coin_price.exchange, second_coin.exchange, profit, pair_price.pair, coin_price.side, second_coin.side, pair_price.price, coin_price, second_coin, pair_price.exchange))
                                            profit_bonds.append(TwoExTwoCoin(coin_price.exchange, second_coin.exchange, profit, pair_price.pair, coin_price.side, second_coin.side, pair_price.price, coin_price, second_coin, pair_price.exchange))

    return profit_bonds