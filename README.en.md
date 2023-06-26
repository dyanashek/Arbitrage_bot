# Arbitrage bot
## Изменить язык: [Русский](README.md)
***
Telegram bot for private use, assisting in arbitrage trading.
## [DEMO](README.demo.md)
## Functionality:
1. Parsing the p2p market on exchanges: Binance, Huobi, Bybit
2. Parsing spot market  on exchanges: Binance, Huobi, Bybit
3. Tracking profitable bundles according to specified settings (amount, number of successful transactions of the counterparty, percentage of successful transactions, exchanges, banks, coins, bundles methods)
4. Notifications when a given type of bundles appears, in accordance with the settings
5. Update information on the most valuable bundles (taker-taker) in real time
## Commands:
**For convenience, it is recommended to add these commands to the side menu of the bot using [BotFather](https://t.me/BotFather).**
- /start - start menu;
- /keyboard - adds a keyboard;
- /show - shows found bundles according to the specified settings (profit from 0.1% to 2%), if you specify a value after the command, eg: /show 0.5 - bundles with profit from 0.5% to 2% will be shown;
- /show_all - shows all found bundles according to the given settings;
- /show_high - shows found bundles according to the given settings with a profit above 2%;
- /show_settings - shows the current settings for searching for bundles;
- /show_alarm_settings - shows the current settings for searching for bundles with notifications;
- /stop_alarm - stops searching for bundles with notifications;
- /stop_all - stops searching for all bundles;

**Use when in the appropriate menu section:**
1. P2P:
   - /a value - sets the amount;
   - /o value - sets the number of orders;
   - /r value - sets the percentage of completion;
2. Spot:
   - /t value - sets the exchange amount.
3. Bundles search settings:
   - /sa value - sets the amount;
   - /so value - sets the number of orders;
   - /sr value - sets the percentage of completion.
4. Settings for searching for bundles with notifications:
   - /aa value - sets the amount;
   - /ao value - sets the number of orders;
   - /ar value - sets the percentage of completion.
## Installation and use:
- Create an .env file containing the following variables:
> the file is created in the root folder of the project
   - specify the bot's telegram token in the file:\
   **TG_TOKEN**=TOKEN
   - **MAIN_USER** contains the ID of the user who has access to execute commands and receives notifications. (for example: MAIN_USER=1234)
> To determine the user ID, you need to send any message from the corresponding account to the next [bot] (https://t.me/getmyid_bot). Value contained in **Your user ID** - User ID
- Install the virtual environment and activate it (if necessary):
> Installation and activation in the root folder of the project
```sh
python3 -m venv venv
source venv/bin/activate # for macOS
source venv/Scripts/activate # for Windows
```
- Install dependencies:
```sh
pip install -r requirements.txt
```
- Run project:
```sh
python3 main.py
```