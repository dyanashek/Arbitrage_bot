import sqlite3
from telebot import types
import itertools

import config

# кнопки стартового меню - статичные
def start_menu():
    keyboard = types.InlineKeyboardMarkup()
    p2p = types.InlineKeyboardButton('P2P', callback_data = f'p2p')
    spot = types.InlineKeyboardButton('Спот', callback_data = f'spot')
    settings = types.InlineKeyboardButton('Настройки', callback_data = f'settings')
    alarm_settings = types.InlineKeyboardButton('Настройки уведомлений', callback_data = f'alarmsettings')
    keyboard.add(p2p)
    keyboard.add(spot)
    keyboard.add(settings)
    keyboard.add(alarm_settings)
    return keyboard

# кнопки меню для p2p - генерируемые
def p2p_exchange(exchanges):
    keyboard = types.InlineKeyboardMarkup()
    for exchange in exchanges:
        button = types.InlineKeyboardButton(f'{exchange.capitalize()}', callback_data = f'p2p_{exchange}')
        keyboard.add(button)
    back = types.InlineKeyboardButton('Назад', callback_data = f'back_main')
    keyboard.add(back)
    return keyboard

# кнопки монет, доступных для p2p на бирже - генерируемые
def p2p_coins(exchange):
    keyboard = types.InlineKeyboardMarkup()

    database = sqlite3.connect("arbitrage.db")
    cursor = database.cursor()
    coins = cursor.execute(f"SELECT coins FROM p2p_coins WHERE name='{exchange}'").fetchall()[0][0].split(', ')

    coins_buttons = list()

    #добавляем кнопки по 3 в ряд
    for i, coin in enumerate(coins):
        coins_buttons.append(types.InlineKeyboardButton(f'{coin}', callback_data = f'p2p_{exchange}_{coin}'))
        if i % 3 == 2 or i == len(coins) - 1:
            if len(coins_buttons) == 1:
                keyboard.add(coins_buttons[0])
            elif len(coins_buttons) == 2:
                keyboard.add(coins_buttons[0], coins_buttons[1])
            else:
                keyboard.add(coins_buttons[0], coins_buttons[1], coins_buttons[2])
            coins_buttons = list()

    back = types.InlineKeyboardButton('Назад', callback_data = f'back_p2pexchange')
    keyboard.add(back)

    return keyboard

# кнопки выбора способа покупки на р2р - генерируемые
def p2p_method(exchange, coin):
    keyboard = types.InlineKeyboardMarkup()
    taker = types.InlineKeyboardButton('Купить', callback_data = f'p2p_{exchange}_{coin}_taker')
    maker = types.InlineKeyboardButton('Продать', callback_data = f'p2p_{exchange}_{coin}_maker')
    back = types.InlineKeyboardButton('Назад', callback_data = f'back_p2pexchange_{exchange}')
    keyboard.add(taker, maker)
    keyboard.add(back)
    return keyboard

# кнопки добавления банка в фильтр:
def p2p_banks(banks, settings):
    exchange = settings[0]
    coin = settings[1]
    method = settings[2]
    banks_in_settings = settings[3]

    keyboard = types.InlineKeyboardMarkup()
    banks_keys = set(banks.keys())
    banks_buttons = banks_keys - banks_in_settings

    for bank in banks_buttons:
        button = types.InlineKeyboardButton(f'{banks[bank]}', callback_data = f'p2p_{exchange}_{coin}_{method}_{bank}')
        keyboard.add(button)

    if banks_in_settings == set():
        keyboard.add(types.InlineKeyboardButton(f'Добавить все', callback_data = f'p2p_{exchange}_{coin}_{method}_addall'))
    else:
        keyboard.add(types.InlineKeyboardButton(f'Выполнить поиск', callback_data = 'p2p_search'))

    keyboard.add(types.InlineKeyboardButton(f'Назад', callback_data = f'back_{exchange}_{coin}_method'))
    return keyboard

# кнопки под сообщением с информацией о р2р ордерах - статичные
def p2p_refresh():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(f'Обновить', callback_data = 'p2p_refresh'))
    keyboard.add(types.InlineKeyboardButton(f'P2P', callback_data = 'p2p_new'))
    return keyboard

# закрепленные кнопки - статичные
def reply_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard = True)
    keyboard.add(types.KeyboardButton('P2P'), types.KeyboardButton('Спот'))
    keyboard.add(types.KeyboardButton('Настройки'))
    keyboard.add(types.KeyboardButton('Настройки уведомлений'))
    return keyboard

# кнопки меню для spot - генерируемые
def spot_exchange(exchanges):
    keyboard = types.InlineKeyboardMarkup()
    for exchange in exchanges:
        button = types.InlineKeyboardButton(f'{exchange.capitalize()}', callback_data = f'spot_{exchange}')
        keyboard.add(button)
    back = types.InlineKeyboardButton('Назад', callback_data = f'back_main')
    keyboard.add(back)
    return keyboard

# кнопки пар на споте на бирже - генерируемые
def spot_pairs(exchange):
    keyboard = types.InlineKeyboardMarkup()

    pair_buttons = []

    #добавляем кнопки по 3 в ряд
    for i, pair in enumerate(config.pairs[exchange]):
        pair_buttons.append(types.InlineKeyboardButton(f'{pair}', callback_data = f'spot_{exchange}_{pair}'))
        if i % 2 == 1 or i == len(config.pairs[exchange]) - 1:
            if len(pair_buttons) == 1:
                keyboard.add(pair_buttons[0])
            else:
                keyboard.add(pair_buttons[0], pair_buttons[1])

            pair_buttons = list()

    back = types.InlineKeyboardButton('Назад', callback_data = f'back_spotexchange')
    keyboard.add(back)

    return keyboard

# кнопки под сообщением с информацией о спотовой цене - статичные
def spot_refresh():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(f'Обновить', callback_data = 'spot_refresh'))
    keyboard.add(types.InlineKeyboardButton(f'Спот', callback_data = 'spot_new'))
    return keyboard

# кнопки под сообщением с конвертацией суммы - генерируемые
def spot_renew(trade):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(f'Обновить', callback_data = f'spot_refresh_{trade}'))
    keyboard.add(types.InlineKeyboardButton(f'Спот', callback_data = 'spot_new'))
    return keyboard

# кнопки добавления настроек в фильтр для поиска связок:
def bonds_settings_keyboard(bonds_settings):
    keyboard = types.InlineKeyboardMarkup()

    exchanges_buttons = []
    for exchange in ['BINANCE', 'HUOBI', 'BYBIT']:
        if exchange not in bonds_settings[0]:
            exchanges_buttons.append(exchange)

    added_exchanges = []
    for num, add_exchange in enumerate(exchanges_buttons):
        added_exchanges.append(types.InlineKeyboardButton(f'{add_exchange.capitalize()}', callback_data = f'settings_exchange_{add_exchange}'))
        if num % 2 == 1 or num == len(exchanges_buttons) - 1:
            if len(added_exchanges) == 1:
                keyboard.add(added_exchanges[0])
            else:
                keyboard.add(added_exchanges[0], added_exchanges[1])
            added_exchanges = list()

    banks_buttons = []
    for bank in ['TINKOFF', 'SBER', 'RAIF']:
        if bank not in bonds_settings[1]:
            banks_buttons.append(bank)

    added_banks = []
    for num, add_bank in enumerate(banks_buttons):
        added_banks.append(types.InlineKeyboardButton(f'{config.banks[add_bank]}', callback_data = f'settings_bank_{add_bank}'))
        if num % 2 == 1 or num == len(banks_buttons) - 1:
            if len(added_banks) == 1:
                keyboard.add(added_banks[0])
            else:
                keyboard.add(added_banks[0], added_banks[1])
            added_banks = list()
    
    methods_buttons = []
    for method in ['taker-taker', 'maker-maker', 'taker-maker', 'maker-taker']:
        if method not in bonds_settings[2]:
            methods_buttons.append(method)

    added_methods = []
    for num, add_method in enumerate(methods_buttons):
        added_methods.append(types.InlineKeyboardButton(f'{add_method}', callback_data = f'settings_method_{add_method}'))
        if num % 2 == 1 or num == len(methods_buttons) - 1:
            if len(added_methods) == 1:
                keyboard.add(added_methods[0])
            else:
                keyboard.add(added_methods[0], added_methods[1])
            added_methods = list()

    coins_buttons = []
    if bonds_settings[0] != []:
        for exchange in bonds_settings[0]:
            for coin in config.coins[exchange]:
                if coin not in coins_buttons and coin not in bonds_settings[6]:
                    coins_buttons.append(coin)

    added_buttons = list()
    #добавляем кнопки по 3 в ряд (монеты)
    for i, coin in enumerate(coins_buttons):
        added_buttons.append(types.InlineKeyboardButton(f'{coin}', callback_data = f'settings_coin_{coin}'))
        if i % 3 == 2 or i == len(coins_buttons) - 1:
            if len(added_buttons) == 1:
                keyboard.add(added_buttons[0])
            elif len(added_buttons) == 2:
                keyboard.add(added_buttons[0], added_buttons[1])
            else:
                keyboard.add(added_buttons[0], added_buttons[1], added_buttons[2])
            added_buttons = list()
        
    if bonds_settings[0] != [] and bonds_settings[1] != [] and bonds_settings[2] != [] and bonds_settings[3] != '':
        keyboard.add(types.InlineKeyboardButton(f'Подтвердить', callback_data = f'settings_accept'))
    
    if bonds_settings[0] == []:
        keyboard.add(types.InlineKeyboardButton(f'Добавить все биржи', callback_data = f'settings_addall_exchanges'))
    
    if bonds_settings[1] == []:
        keyboard.add(types.InlineKeyboardButton(f'Добавить все банки', callback_data = f'settings_addall_banks'))
    
    if bonds_settings[2] == []:
        keyboard.add(types.InlineKeyboardButton(f'Добавить все способы', callback_data = f'settings_addall_methods'))
    
    keyboard.add(types.InlineKeyboardButton(f'Назад', callback_data = f'back_main'))

    return keyboard

# кнопки добавления настроек в фильтр уведомлений:
def bonds_alarmsettings_keyboard(bonds_settings):
    keyboard = types.InlineKeyboardMarkup()

    exchanges_buttons = []
    for exchange in ['BINANCE', 'HUOBI', 'BYBIT']:
        if exchange not in bonds_settings[0]:
            exchanges_buttons.append(exchange)

    added_exchanges = []
    for num, add_exchange in enumerate(exchanges_buttons):
        added_exchanges.append(types.InlineKeyboardButton(f'{add_exchange.capitalize()}', callback_data = f'alarmsettings_exchange_{add_exchange}'))
        if num % 2 == 1 or num == len(exchanges_buttons) - 1:
            if len(added_exchanges) == 1:
                keyboard.add(added_exchanges[0])
            else:
                keyboard.add(added_exchanges[0], added_exchanges[1])
            added_exchanges = list()

    banks_buttons = []
    for bank in ['TINKOFF', 'SBER', 'RAIF']:
        if bank not in bonds_settings[1]:
            banks_buttons.append(bank)

    added_banks = []
    for num, add_bank in enumerate(banks_buttons):
        added_banks.append(types.InlineKeyboardButton(f'{config.banks[add_bank]}', callback_data = f'alarmsettings_bank_{add_bank}'))
        if num % 2 == 1 or num == len(banks_buttons) - 1:
            if len(added_banks) == 1:
                keyboard.add(added_banks[0])
            else:
                keyboard.add(added_banks[0], added_banks[1])
            added_banks = list()
    
    methods_buttons = []
    for method in ['taker-taker', 'maker-maker', 'taker-maker', 'maker-taker']:
        if method not in bonds_settings[2]:
            methods_buttons.append(method)

    added_methods = []
    for num, add_method in enumerate(methods_buttons):
        added_methods.append(types.InlineKeyboardButton(f'{add_method}', callback_data = f'alarmsettings_method_{add_method}'))
        if num % 2 == 1 or num == len(methods_buttons) - 1:
            if len(added_methods) == 1:
                keyboard.add(added_methods[0])
            else:
                keyboard.add(added_methods[0], added_methods[1])
            added_methods = list()

    coins_buttons = []
    if bonds_settings[0] != []:
        for exchange in bonds_settings[0]:
            for coin in config.coins[exchange]:
                if coin not in coins_buttons and coin not in bonds_settings[6]:
                    coins_buttons.append(coin)

    added_buttons = list()
    #добавляем кнопки по 3 в ряд (монеты)
    for i, coin in enumerate(coins_buttons):
        added_buttons.append(types.InlineKeyboardButton(f'{coin}', callback_data = f'alarmsettings_coin_{coin}'))
        if i % 3 == 2 or i == len(coins_buttons) - 1:
            if len(added_buttons) == 1:
                keyboard.add(added_buttons[0])
            elif len(added_buttons) == 2:
                keyboard.add(added_buttons[0], added_buttons[1])
            else:
                keyboard.add(added_buttons[0], added_buttons[1], added_buttons[2])
            added_buttons = list()
        
    if bonds_settings[0] != [] and bonds_settings[1] != [] and bonds_settings[2] != [] and bonds_settings[3] != '':
        keyboard.add(types.InlineKeyboardButton(f'Подтвердить', callback_data = f'alarmsettings_accept'))
    
    if bonds_settings[0] == []:
        keyboard.add(types.InlineKeyboardButton(f'Добавить все биржи', callback_data = f'alarmsettings_addall_exchanges'))
    
    if bonds_settings[1] == []:
        keyboard.add(types.InlineKeyboardButton(f'Добавить все банки', callback_data = f'alarmsettings_addall_banks'))
    
    if bonds_settings[2] == []:
        keyboard.add(types.InlineKeyboardButton(f'Добавить все способы', callback_data = f'alarmsettings_addall_methods'))
    
    keyboard.add(types.InlineKeyboardButton(f'Назад', callback_data = f'back_main'))

    return keyboard

def taker_alarm(bonds_settings):
    keyboard = types.InlineKeyboardMarkup()

    counter = 0
    for alarm in config.alarms:
        if alarm == bonds_settings:
            counter = 1
            break
    
    if counter == 1:
        keyboard.add(types.InlineKeyboardButton(f'Остановить', callback_data = f'stop'))
    else:
        keyboard.add(types.InlineKeyboardButton(f'Запустить', callback_data = f'restart'))
        keyboard.add(types.InlineKeyboardButton(f'Отменить', callback_data = f'delete'))
    return keyboard