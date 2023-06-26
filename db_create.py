import sqlite3

database = sqlite3.connect("arbitrage.db")
cursor = database.cursor()

# создает таблицу, содержащую информацию по монетам, торгующимся на р2р каждой из бирж
cursor.execute('''CREATE TABLE p2p_coins(
    id INTEGER PRIMARY KEY,
    name VARCHAR (10),
    coins 
)''')

# создает БД с обозначениями банков 
cursor.execute('''CREATE TABLE banks(
    id INTEGER PRIMARY KEY,
    name VARCHAR (10),
    bank VARCHAR (10),
    system
)''')

# создает БД с обозначениями монет
cursor.execute('''CREATE TABLE coins(
    id INTEGER PRIMARY KEY,
    name VARCHAR (10),
    coin VARCHAR (10),
    system
)''')

# создает БД с обозначениями валют
cursor.execute('''CREATE TABLE currency(
    id INTEGER PRIMARY KEY,
    name VARCHAR (10),
    currency VARCHAR (10),
    system
)''')

# создает БД с обозначениями стороны торговли (обозначение buy - когда хочешь купить, sell - когда хочешь продать)
cursor.execute('''CREATE TABLE side(
    id INTEGER PRIMARY KEY,
    name VARCHAR (10),
    side VARCHAR (10),
    system
)''')

# создает БД с комиссиями за перевод между биржами
cursor.execute('''CREATE TABLE coms(
    id INTEGER PRIMARY KEY,
    send VARCHAR (10),
    reciev VARCHAR (10),
    coms INTEGER
)''')