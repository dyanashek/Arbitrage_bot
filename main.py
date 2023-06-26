import telebot
import sqlite3
import asyncio
import threading
from aiohttp import ClientSession

import config
from bonds import start_bonds, start_alarm_bonds
from functions import p2p_settings_text, p2p_search, spot_search, spot_price, settings_text, settings_alarm_text,\
                      bonds_text, current_settings, current_alarm_settings, all_alarms
from keyboards import start_menu, p2p_exchange, p2p_coins, p2p_method, p2p_banks, p2p_refresh, reply_menu,\
                      spot_exchange, spot_pairs, spot_refresh, spot_renew,\
                      bonds_settings_keyboard, bonds_alarmsettings_keyboard, taker_alarm


bot = telebot.TeleBot(config.TG_TOKEN)
bot.unpin_all_chat_messages(config.main_user)
# генерируем список бирж:
exchanges = []

database = sqlite3.connect("arbitrage.db")
cursor = database.cursor()

result = cursor.execute(f"SELECT name FROM p2p_coins").fetchall()
for exchange in result:
    exchanges.append(exchange[0])

# словарь банков
banks = config.banks

# настройки для вывода вариантов на p2p
p2p_settings = []
# настройки для вывода вариантов на споте
spot_settings = []
# настройки для отслеживания связок:
bonds_settings = [[], [], [], '', '', '', []] # биржи, банки, типы связок, сумма, кол-во ордеров, процент выполнения, монеты
# настройки для отслеживания связок с уведомлениями:
bonds_alarm_settings = [[], [], [], '', '', '', []] # биржи, банки, типы связок, сумма, кол-во ордеров, процент выполненияь монеты


def wrapper_bonds():
    asyncio.run(start_bonds(bonds_settings))


def wrapper_alarm_bonds():
    global bonds_alarm_settings
    asyncio.run(start_alarm_bonds(bonds_alarm_settings))

    bonds_alarm_settings = [[], [], [], '', '', '', []]


def wrapper_restart(restart_settings):
    asyncio.run(start_alarm_bonds(restart_settings))


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Выберите интересующий вас раздел:', reply_markup=start_menu())


@bot.callback_query_handler(func = lambda call: True)
def callback_query(call):

    message_id = call.message.id
    chat_id = call.message.chat.id
    call_data = call.data.split('_')
    len_data = len(call_data)
    action = call_data[0]

    if len_data == 1:
    # кнопки основного меню
        if call.data == 'p2p':
            p2p_settings.clear()
            bot.edit_message_text(chat_id = chat_id, message_id = message_id, text='Выберите биржу (p2p):')
            bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup = p2p_exchange(exchanges))

        elif call.data == 'spot':
            spot_settings.clear()
            bot.edit_message_text(chat_id = chat_id, message_id = message_id, text='Выберите биржу (spot):')
            bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup = spot_exchange(exchanges))

        elif call.data == 'settings':
            global bonds_settings
            bonds_settings = [[], [], [], '', '', '', []]

            config.settings_flag = False
            config.profit_bonds = []

            reply_text = settings_text(bonds_settings)
            bot.edit_message_text(chat_id = chat_id, message_id = message_id, text=reply_text, parse_mode='Markdown')
            bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup = bonds_settings_keyboard(bonds_settings))
            pass

        elif call.data == 'alarmsettings':
            global bonds_alarm_settings
            bonds_alarm_settings = [[], [], [], '', '', '', []]

            reply_text = settings_alarm_text(bonds_alarm_settings)
            bot.edit_message_text(chat_id = chat_id, message_id = message_id, text=reply_text, parse_mode='Markdown')
            bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup = bonds_alarmsettings_keyboard(bonds_alarm_settings))
            pass

        elif call.data == 'stop':
            if message_id not in config.taker:
                bot.send_message(chat_id, text='Уведомления с данными настройками уже остановлены.')
                bot.unpin_chat_message(message_id=message_id, chat_id=chat_id)
                bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup=telebot.types.InlineKeyboardMarkup())
            else:
                try:
                    config.alarms.remove(config.taker[message_id])
                except:
                    pass
                bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup = taker_alarm(config.taker[message_id]))
                bot.send_message(chat_id, text='Уведомления с заданными параметрами приостановлены.')

        elif call.data == 'restart':
            if message_id not in config.taker:
                bot.send_message(chat_id, text='Настройки не найдены, задайте заново в разделе "настройки уведомлений".')
                bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup=telebot.types.InlineKeyboardMarkup())
                bot.unpin_chat_message(message_id=message_id, chat_id=chat_id)
            else:
                counter = 0
                for alarm in config.alarms:
                    if alarm == bonds_alarm_settings:
                        counter += 1

                if counter != 0:
                    bot.send_message(chat_id, text='Уведомление с такими настройками уже запущено.')
                    bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup=telebot.types.InlineKeyboardMarkup())
                    return

                config.settings_alarm_flag = True
                threading.Thread(daemon=True, target=wrapper_restart, args=(config.taker[message_id],)).start()

                reply_text = current_alarm_settings(config.taker[message_id])

                config.taker.pop(message_id)

                bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup=telebot.types.InlineKeyboardMarkup())
                bot.unpin_chat_message(message_id=message_id, chat_id=chat_id)

                bot.send_message(chat_id, text=reply_text, parse_mode='Markdown')

        elif call.data == 'delete':
            bot.unpin_chat_message(message_id=message_id, chat_id=chat_id)
            if message_id not in config.taker:
                bot.send_message(chat_id, text='Настройки с заданными параметрами не найдены.')
                bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup=telebot.types.InlineKeyboardMarkup())
            else:
                config.taker.pop(message_id)
                bot.send_message(chat_id, text='Уведомления с заданными параметрами отменены.')
                bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup=telebot.types.InlineKeyboardMarkup())

    elif len_data == 2:
        # обрабатываются кнопки выбора биржи для p2p
        if action == 'p2p':
            exchange = call_data[1]

            # выполняем поиск монеты на p2p в соответствии с заданными настройками    
            if exchange == 'search' or exchange == 'refresh':
                if len(p2p_settings) != 7:
                    bot.send_message(chat_id, 'Ошибка, настройки не заданы. Используйте команду /start.')
                elif p2p_settings[3] == []:
                    bot.send_message(chat_id, 'Ошибка, настройки не заданы. Используйте команду /start.')
                else:
                    reply_text = p2p_search(p2p_settings)
                    if reply_text != 'Ошибка соединения':
                        bot.edit_message_text(chat_id = chat_id, message_id = message_id, text=reply_text, parse_mode='Markdown')
                        bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup=p2p_refresh())
                    else:
                        bot.send_message(chat_id, 'Ошибка соединения.')
            
            elif exchange == 'new':
                p2p_settings.clear()
                bot.send_message(chat_id, 'Выберите биржу (p2p):', reply_markup=p2p_exchange(exchanges))

            else:
                bot.edit_message_text(chat_id = chat_id, message_id = message_id, text='Выберите монету:')
                bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup = p2p_coins(exchange))
        
        elif action == 'spot':
            exchange = call_data[1]
            if exchange == 'refresh':
                if len(spot_settings) == 3:
                    price, reply_text = spot_search(spot_settings[0], spot_settings[1])

                    if price == 'Ошибка соединения':
                        bot.send_message(chat_id, 'Ошибка соединения.')
                    else:
                        bot.edit_message_text(chat_id = chat_id, message_id = message_id, text=reply_text, parse_mode='Markdown')
                        bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup = spot_refresh())  

                else:
                    bot.send_message(chat_id, 'Ошибка, настройки не заданы. Используйте команду /start.')

            elif exchange == 'new':
                spot_settings.clear()
                bot.send_message(chat_id, 'Выберите биржу (spot):', reply_markup=spot_exchange(exchanges))

            else:
                bot.edit_message_text(chat_id = chat_id, message_id = message_id, text='Выберите пару:')
                bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup = spot_pairs(exchange))

        # обрабатывется кнопка возврата в главное меню
        elif call.data == 'back_main':
            bot.edit_message_text(chat_id = chat_id, message_id = message_id, text='Выберите интересующий вас раздел:')
            bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup = start_menu())
        
        # обрабатывается кнопка возврата к выбору бирж на р2р
        elif call.data == 'back_p2pexchange':
            bot.edit_message_text(chat_id = chat_id, message_id = message_id, text='Выберите биржу (p2p):')
            bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup = p2p_exchange(exchanges))

        # обрабатывается кнопка возврата к выбору бирж на spot
        elif call.data == 'back_spotexchange':
            bot.edit_message_text(chat_id = chat_id, message_id = message_id, text='Выберите биржу (spot):')
            bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup = spot_exchange(exchanges))

        elif call.data == 'settings_accept':
            if bonds_settings[0] == [] or bonds_settings[1] == [] or bonds_settings[2] == [] or bonds_settings[3] == '':
                bot.edit_message_text(chat_id = chat_id, message_id = message_id, text='Задайте настройки')
            else:
                if bonds_settings[6] == []:
                    for exchange in bonds_settings[0]:
                        for coin in config.coins[exchange]:
                            if coin not in bonds_settings[6]:
                                bonds_settings[6].append(coin)

                config.settings_flag = True
                threading.Thread(daemon=True, target=wrapper_bonds).start()
                reply_text = current_settings(bonds_settings)
                bot.edit_message_text(chat_id = chat_id, message_id = message_id, text=reply_text, parse_mode='Markdown')
                                  
        elif call.data == 'alarmsettings_accept':
            if bonds_alarm_settings[0] == [] or bonds_alarm_settings[1] == [] or bonds_alarm_settings[2] == [] or bonds_alarm_settings[3] == '':
                bot.edit_message_text(chat_id = chat_id, message_id = message_id, text='Задайте настройки')
            else:
                counter = 0
                for alarm in config.alarms:
                    if alarm == bonds_alarm_settings:
                        counter += 1

                if counter != 0:
                    bot.send_message(chat_id, text='Уведомление с такими настройками уже запущено.')
                    return
                
                if bonds_alarm_settings[6] == []:
                    for exchange in bonds_alarm_settings[0]:
                        for coin in config.coins[exchange]:
                            if coin not in bonds_alarm_settings[6]:
                                bonds_alarm_settings[6].append(coin)

                config.settings_alarm_flag = True
                threading.Thread(daemon=True, target=wrapper_alarm_bonds).start()
                reply_text = current_alarm_settings(bonds_alarm_settings)
                bot.edit_message_text(chat_id = chat_id, message_id = message_id, text=reply_text, parse_mode='Markdown')


    elif len_data == 3:
        # обрабатываются кнопки выбора монет для р2р
        if action == 'p2p':
            exchange = call_data[1]
            coin = call_data[2]

            bot.edit_message_text(chat_id = chat_id, message_id = message_id, text='Выберите способ:')
            bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup = p2p_method(exchange, coin))

        elif action == 'spot':
            exchange = call_data[1]

            if exchange == 'refresh':
                trade = float(call_data[2])

                if len(spot_settings) != 3:
                    bot.send_message(chat_id, 'Задайте настройки, используйте команду /start.')
                else:
                    price, reply_text = spot_search(spot_settings[0], spot_settings[1])
                    if price == 'Ошибка соединения':
                        bot.send_message(chat_id, 'Ошибка соединения.')
                    else:
                        spot_settings[2] = price
                        reply_text = spot_price(spot_settings, trade)
                        bot.edit_message_text(chat_id = chat_id, message_id = message_id, text=reply_text, parse_mode='Markdown')
                        bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup=spot_renew(trade))

            else:
                pair = call_data[2]
                price, reply_text = spot_search(exchange, pair)

                if price == 'Ошибка соединения':
                    bot.send_message(chat_id, 'Ошибка соединения.')
                else:
                    spot_settings.append(exchange)
                    spot_settings.append(pair)
                    spot_settings.append(price)

                    bot.edit_message_text(chat_id = chat_id, message_id = message_id, text=reply_text, parse_mode='Markdown')
                    bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup = spot_refresh())


        # обрабатывается кнопка назад
        elif action == 'back':
            subaction = call_data[1]
            exchange = call_data[2]

            # если необходимо вернуться к выбору монеты на p2p
            if subaction == 'p2pexchange':
                bot.edit_message_text(chat_id = chat_id, message_id = message_id, text='Выберите монету:')
                bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup = p2p_coins(exchange))
        
        # обрабатываются кнопки настроек:
        elif action == 'settings':
            param = call_data[1]
            setting = call_data[2]

            if param != 'addall':
                if param == 'exchange':
                    bonds_settings[0].append(setting)
                elif param == 'bank':
                    bonds_settings[1].append(setting)
                elif param == 'method':
                    bonds_settings[2].append(setting)
                elif param == 'coin':
                    bonds_settings[6].append(setting)
                
            else:
                if setting == 'exchanges':
                    bonds_settings[0] = ['BINANCE', 'HUOBI', 'BYBIT']
                elif setting == 'banks':
                    bonds_settings[1] = ['TINKOFF', 'SBER', 'RAIF']
                elif setting == 'methods':
                    bonds_settings[2] = ['taker-taker', 'maker-maker', 'taker-maker', 'maker-taker'] 
            
            reply_text = settings_text(bonds_settings)
            bot.edit_message_text(chat_id = chat_id, message_id = message_id, text=reply_text, parse_mode='Markdown')
            bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup = bonds_settings_keyboard(bonds_settings))

        elif action == 'alarmsettings':
            param = call_data[1]
            setting = call_data[2]

            if param != 'addall':
                if param == 'exchange':
                    bonds_alarm_settings[0].append(setting)
                elif param == 'bank':
                    bonds_alarm_settings[1].append(setting)
                elif param == 'method':
                    bonds_alarm_settings[2].append(setting)
                elif param == 'coin':
                    bonds_alarm_settings[6].append(setting)
                
            else:
                if setting == 'exchanges':
                    bonds_alarm_settings[0] = ['BINANCE', 'HUOBI', 'BYBIT']
                elif setting == 'banks':
                    bonds_alarm_settings[1] = ['TINKOFF', 'SBER', 'RAIF']
                elif setting == 'methods':
                    bonds_alarm_settings[2] = ['taker-taker', 'maker-maker', 'taker-maker', 'maker-taker'] 
            
            reply_text = settings_alarm_text(bonds_alarm_settings)
            bot.edit_message_text(chat_id = chat_id, message_id = message_id, text=reply_text, parse_mode='Markdown')
            bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup = bonds_alarmsettings_keyboard(bonds_alarm_settings))
            
    elif len_data == 4:
        p2p_settings.clear()

        # обрабатываются кнопки выбора метода для p2p (мэйкер/тэйкер)
        if action == 'p2p':
            exchange = call_data[1]
            p2p_settings.append(exchange)

            coin = call_data[2]
            p2p_settings.append(coin)

            method = call_data[3]
            p2p_settings.append(method)

            p2p_settings.append(set())

            p2p_settings.append(0)
            p2p_settings.append(0)
            p2p_settings.append(0)

            bot.edit_message_text(chat_id = chat_id, message_id = message_id, text='Выберите банк:')
            bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup = p2p_banks(banks, p2p_settings))
        
        elif action == 'back':
            subaction = call_data[3]

            # если необходимо вернуться к выбору метода (мэйкер/тэйкер)
            if subaction == 'method':
                exchange = call_data[1]
                coin = call_data[2]
                bot.edit_message_text(chat_id = chat_id, message_id = message_id, text='Выберите способ:')
                bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup = p2p_method(exchange, coin))

    elif len_data == 5:
        if action == 'p2p':
            if len(p2p_settings) != 7:
                bot.send_message(chat_id, 'Задайте настройки, используйте команду /start.')

            else:
                bank = call_data[4]
                
                # если нажата кнопка "выбрать все банки" - в фильтр добавляются все банки
                if bank == 'addall':
                    p2p_settings[3] = set(banks.keys())
                
                # если выбран конкретный банк - добавляется он
                else:
                    p2p_settings[3].add(bank)

                reply_text = p2p_settings_text(p2p_settings)

                bot.edit_message_text(chat_id = chat_id, message_id = message_id, text=reply_text, parse_mode='Markdown')
                bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup = p2p_banks(banks, p2p_settings))


@bot.message_handler(commands=['a'])
def start_message(message):
    try:             
        amount = abs(int(message.text.replace(' ', '').replace('/a', '')))
    except:
        bot.send_message(message.chat.id, 'Введено некорректное значение.')
        return 
    
    if len(p2p_settings) != 7:
        bot.send_message(message.chat.id, 'Задайте настройки, используйте команду /start.')
    else:
        p2p_settings[4] = amount
        reply_text = p2p_settings_text(p2p_settings)
        bot.send_message(message.chat.id, text=reply_text, reply_markup=p2p_banks(banks, p2p_settings), parse_mode='Markdown')


@bot.message_handler(commands=['o'])
def start_message(message):
    try:             
        orders = abs(int(message.text.replace(' ', '').replace('/o', '')))
    except:
        bot.send_message(message.chat.id, 'Введено некорректное значение.')
        return 
    
    if len(p2p_settings) != 7:
        bot.send_message(message.chat.id, 'Задайте настройки, используйте команду /start.')
    else:
        p2p_settings[5] = orders
        reply_text = p2p_settings_text(p2p_settings)
        bot.send_message(message.chat.id, text=reply_text, reply_markup=p2p_banks(banks, p2p_settings), parse_mode='Markdown')


@bot.message_handler(commands=['r'])
def start_message(message):
    try:             
        rate = abs(int(message.text.replace(' ', '').replace('/r', '')))
    except:
        bot.send_message(message.chat.id, 'Введено некорректное значение.')
        return 
    
    if len(p2p_settings) != 7:
        bot.send_message(message.chat.id, 'Задайте настройки, используйте команду /start.')
    else:
        p2p_settings[6] = rate
        reply_text = p2p_settings_text(p2p_settings)
        bot.send_message(message.chat.id, text=reply_text, reply_markup=p2p_banks(banks, p2p_settings), parse_mode='Markdown')


@bot.message_handler(commands=['sa'])
def start_message(message):
    if config.settings_flag is True:
        bot.send_message(message.chat.id, 'Настройки уже применены, для изменения перейдите в пункт меню "настройки".')
        return
    
    try:             
        amount = abs(int(message.text.replace(' ', '').replace('/sa', '')))
    except:
        bot.send_message(message.chat.id, 'Введено некорректное значение.')
        return 
    
    bonds_settings[3] = amount

    reply_text = settings_text(bonds_settings)
    bot.send_message(message.chat.id, text=reply_text, reply_markup = bonds_settings_keyboard(bonds_settings), parse_mode='Markdown')


@bot.message_handler(commands=['so'])
def start_message(message):
    if config.settings_flag is True:
        bot.send_message(message.chat.id, 'Настройки уже применены, для изменения перейдите в пункт меню "настройки".')
        return
    
    try:             
        orders = abs(int(message.text.replace(' ', '').replace('/so', '')))
    except:
        bot.send_message(message.chat.id, 'Введено некорректное значение.')
        return 
    
    bonds_settings[4] = orders

    reply_text = settings_text(bonds_settings)
    bot.send_message(message.chat.id, text=reply_text, reply_markup = bonds_settings_keyboard(bonds_settings), parse_mode='Markdown')


@bot.message_handler(commands=['sr'])
def start_message(message):
    if config.settings_flag is True:
        bot.send_message(message.chat.id, 'Настройки уже применены, для изменения перейдите в пункт меню "настройки".')
        return
    
    try:             
        rate = abs(int(message.text.replace(' ', '').replace('/sr', '')))
    except:
        bot.send_message(message.chat.id, 'Введено некорректное значение.')
        return 
    
    bonds_settings[5] = rate

    reply_text = settings_text(bonds_settings)
    bot.send_message(message.chat.id, text=reply_text, reply_markup = bonds_settings_keyboard(bonds_settings), parse_mode='Markdown')


@bot.message_handler(commands=['aa'])
def start_message(message):
    try:             
        amount = abs(int(message.text.replace(' ', '').replace('/aa', '')))
    except:
        bot.send_message(message.chat.id, 'Введено некорректное значение.')
        return 
    
    bonds_alarm_settings[3] = amount

    reply_text = settings_alarm_text(bonds_alarm_settings)
    bot.send_message(message.chat.id, text=reply_text, reply_markup = bonds_alarmsettings_keyboard(bonds_alarm_settings), parse_mode='Markdown')


@bot.message_handler(commands=['ao'])
def start_message(message):
    try:             
        orders = abs(int(message.text.replace(' ', '').replace('/ao', '')))
    except:
        bot.send_message(message.chat.id, 'Введено некорректное значение.')
        return 
    
    bonds_alarm_settings[4] = orders

    reply_text = settings_alarm_text(bonds_alarm_settings)
    bot.send_message(message.chat.id, text=reply_text, reply_markup = bonds_alarmsettings_keyboard(bonds_alarm_settings), parse_mode='Markdown')


@bot.message_handler(commands=['ar'])
def start_message(message):
    try:             
        rate = abs(int(message.text.replace(' ', '').replace('/ar', '')))
    except:
        bot.send_message(message.chat.id, 'Введено некорректное значение.')
        return 
    
    bonds_alarm_settings[5] = rate

    reply_text = settings_alarm_text(bonds_alarm_settings)
    bot.send_message(message.chat.id, text=reply_text, reply_markup = bonds_alarmsettings_keyboard(bonds_alarm_settings), parse_mode='Markdown')


@bot.message_handler(commands=['t'])
def start_message(message):
    try:             
        trade = abs(float(message.text.replace(' ', '').replace('/t', '').replace(',', '.')))
    except:
        bot.send_message(message.chat.id, 'Введено некорректное значение.')
        return 
    
    if len(spot_settings) != 3:
        bot.send_message(message.chat.id, 'Задайте настройки, используйте команду /start.')
    else:
        reply_text = spot_price(spot_settings, trade)
        bot.send_message(message.chat.id, text=reply_text, reply_markup=spot_renew(trade), parse_mode='Markdown')


@bot.message_handler(commands=['show'])
def start_message(message):
    if config.settings_flag is False:
        bot.send_message(message.chat.id, 'Поиск связок не запущен - перейдите в раздел "настройки" и надмите "подтвердить".')
        return
    
    profit = message.text.replace('/show', '').replace(' ', '').replace(',', '.')

    if profit == '':
        profit = 0.1
    else:
        try:
            profit = abs(float(profit))
        except:
            bot.send_message(message.chat.id, 'Введено некорректное значение.')
            return
    
    if profit > 2:
        profit = 2
    
    if config.profit_bonds == []:
        bot.send_message(message.chat.id, 'Нет связок, соответствующих заданным настройкам.')
        return
    
    else:
        final_bonds = []
        for bond in config.profit_bonds:
            if bond.profit >= profit and bond.profit <= 2:
                final_bonds.append(bond)
        
        if final_bonds == []:
            bot.send_message(message.chat.id, 'Нет связок, соответствующих заданным настройкам.')
            return
        
        else:
            final_bonds = sorted(final_bonds, key=lambda x: x.profit)[::-1]
            replies = bonds_text(final_bonds)
            for reply in replies:
                bot.send_message(message.chat.id, text=reply, parse_mode='Markdown')


@bot.message_handler(commands=['show_all'])
def start_message(message):
    if config.settings_flag is False:
        bot.send_message(message.chat.id, 'Поиск связок не запущен - перейдите в раздел "настройки" и надмите "подтвердить".')
        return

    if config.profit_bonds == []:
        bot.send_message(message.chat.id, 'Нет связок, соответствующих заданным настройкам.')
        return
    
    else:
        final_bonds = sorted(config.profit_bonds, key=lambda x: x.profit)[::-1]
        replies = bonds_text(final_bonds)
        for reply in replies:
            bot.send_message(message.chat.id, text=reply, parse_mode='Markdown')


@bot.message_handler(commands=['show_high'])
def start_message(message):
    if config.settings_flag is False:
        bot.send_message(message.chat.id, 'Поиск связок не запущен - перейдите в раздел "настройки" и надмите "подтвердить".')
        return
    
    if config.profit_bonds == []:
        bot.send_message(message.chat.id, 'Нет связок, соответствующих заданным настройкам.')
        return
    
    else:
        final_bonds = []
        for bond in config.profit_bonds:
            if bond.profit > 2:
                final_bonds.append(bond)
        
        if final_bonds == []:
            bot.send_message(message.chat.id, 'Нет связок, соответствующих заданным настройкам.')
            return
        
        else:
            final_bonds = sorted(final_bonds, key=lambda x: x.profit)[::-1]
            replies = bonds_text(final_bonds)
            for reply in replies:
                bot.send_message(message.chat.id, text=reply, parse_mode='Markdown')


@bot.message_handler(commands=['show_settings'])
def start_message(message):
    if config.settings_flag is False:
        bot.send_message(message.chat.id, 'Настройки не заданы, перейдите в пункт меню "настройки" и нажмите "подтвердить".')
        return
    
    reply_text = current_settings(bonds_settings)
    bot.send_message(message.chat.id, text=reply_text, parse_mode='Markdown')


@bot.message_handler(commands=['show_alarm_settings'])
def start_message(message):
    if config.alarms == []:
        bot.send_message(message.chat.id, 'Настройки не заданы, перейдите в пункт меню "настройки уведомлений" и нажмите "подтвердить".')
        return
    
    replies = all_alarms(config.alarms)
    for reply in replies:
        bot.send_message(message.chat.id, text=reply, parse_mode='Markdown')


@bot.message_handler(commands=['stop_alarm'])
def start_message(message):
    config.settings_alarm_flag = False
    bot.send_message(message.chat.id, text='Уведомления отменены.')


@bot.message_handler(commands=['stop_all'])
def start_message(message):
    config.taker.clear()
    config.settings_alarm_flag = False
    config.settings_flag = False
    bot.send_message(message.chat.id, text='Уведомления и поиск связок отменены.')


@bot.message_handler(commands=['help'])
def start_message(message):
    reply_text = f'''
                    \n/start - стартовое меню;\
                    \n/keyboard - добавляет клавиатуру;\
                    \n/show - показывает найденные связки по заданным настройкам (профит от 0.1% до 2%), если после команды указать значение, н/р:\n/show 0.5 - будут показаны связки с профитом от 0.5% до 2%;\
                    \n/show_all - показывает все найденные связки по заданным настройкам;\
                    \n/show_high - показывает найденные связки по заданным настройкам с профитом выше 2%;\
                    \n/show_settings - показывает текущие настройки для поиска связок;\
                    \n/show_alarm_settings - показывает текущие настройки для поиска связок c уведомлениями;\
                    \n/stop_alarm - останавливает поиск связок с уведомлениями;\
                    \n/stop_all - останавливает поиск всех связок;\
                    \n\
                    \nИспользовать при нахождении в соответствующем разделе меню:\
                    \n<b>1. P2P:</b>\
                    \n<b>/a значение</b> - устанавливает сумму;\
                    \n<b>/o значение</b> - устанавливает кол-во ордеров;\
                    \n<b>/r значение</b> - устанавливает процент выполнения;\
                    \n\
                    \n<b>2. Спот:</b>\
                    \n<b>/t значение</b> - устаналивает сумму обмена;\
                    \n\
                    \n<b>3. Настройки поиска связок:</b>\
                    \n<b>/sa значение</b> - устаналивает сумму;\
                    \n<b>/so значение</b> - устаналивает кол-во ордеров;\
                    \n<b>/sr значение</b> - устаналивает процент выполнения;\
                    \n\
                    \n<b>4. Настройки поиска связок c уведомлениями:</b>\
                    \n<b>/aa значение</b> - устаналивает сумму;\
                    \n<b>/ao значение</b> - устаналивает кол-во ордеров;\
                    \n<b>/ar значение</b> - устаналивает процент выполнения.\
    '''
    bot.send_message(message.chat.id, text=reply_text, parse_mode='HTML')


@bot.message_handler(commands=['keyboard'])
def start_message(message):
    bot.send_message(message.chat.id, text='Клавиатура добавлена.', reply_markup=reply_menu())


@bot.message_handler(content_types=['text'])
def send_text(message):
    message_text = message.text

    if message_text == 'P2P':
        p2p_settings.clear()
        bot.send_message(message.chat.id, 'Выберите биржу (p2p):', reply_markup=p2p_exchange(exchanges))

    elif message_text == 'Спот':
        spot_settings.clear()
        bot.send_message(message.chat.id, 'Выберите биржу (spot):', reply_markup=spot_exchange(exchanges))

    elif message_text == 'Настройки':
        global bonds_settings
        bonds_settings = [[], [], [], '', '', '', []]

        config.settings_flag = False
        config.profit_bonds = []

        reply_text = settings_text(bonds_settings)
        bot.send_message(message.chat.id, text=reply_text, reply_markup = bonds_settings_keyboard(bonds_settings), parse_mode='Markdown')
    
    elif message_text == 'Настройки уведомлений':
        global bonds_alarm_settings
        bonds_alarm_settings = [[], [], [], '', '', '', []]

        reply_text = settings_alarm_text(bonds_alarm_settings)
        bot.send_message(message.chat.id, text=reply_text, reply_markup = bonds_alarmsettings_keyboard(bonds_alarm_settings), parse_mode='Markdown')


if __name__ == '__main__':
    # bot.polling(timeout=80)
    while True:
        try:
            bot.polling()
        except:
            pass