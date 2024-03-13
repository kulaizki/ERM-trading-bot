import os
from dotenv import load_dotenv
from binance.um_futures import UMFutures
import ta
import pandas as pd
from time import sleep
from binance.error import ClientError

load_dotenv(dotenv_path="keys.env")
api = os.getenv("api")
secret = os.getenv("secret")
client = UMFutures(key=api, secret=secret)

tp = 0.01
sl = 0.01
volume = 50
leverage = 10
type = 'ISOLATED'

def get_balance_usdt():
    try:
        response = client.balance(recvWindow=6000)
        for e in response:
            if e['asset'] == 'USDT':
                return float(e['balance'])
        
    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )

print("USDM Balance: ", get_balance_usdt(), " USDT")

def get_tickers_usdt():
    tickers = []
    resp = client.ticker_price()
    for e in resp:
        if 'USDT' in e['symbol']:
            tickers.append(e['symbol'])
    return tickers

# print(get_tickers_usdt())
def klines(symbol):
    try:
        resp = pd.DataFrame(client.klines(symbol, '1h'))
        resp = resp.iloc[:, :6]
        resp.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
        resp = resp.set_index('Time')
        resp.index = pd.to_datetime(resp.index, unit = 'ms')
        resp = resp.astype(float)
        return resp
    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )       

# print(klines('BTCUSDT'))
def set_leverage(symbol, level):
    try:
        response = client.change_leverage(
            symbol=symbol, leverage=level, recvWindow=6000
        )
        print(response)
    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )

def set_mode(symbol, type):
    try:
        response = client.change_margin_type(
            symbol=symbol, marginType=type, recvWindow=6000
        )
        print(response)
    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )

def get_price_precision(symbol):
    resp = client.exchange_info()['symbols']
    for e in resp:
        if e['symbol'] == symbol:
            return e['pricePrecision']

def get_qty_precision(symbol):
    resp = client.exchange_info()['symbols']
    for e in resp:
        if e['symbol'] == symbol:
            return e['quantityPrecision']

def open_order(symbol, side):
    price = float(client.ticker_price(symbol)['price'])
    price_precision = get_price_precision(symbol)
    qty_precision = get_qty_precision(symbol)
    qty = round(volume / price, qty_precision)
    if side == 'buy':
        try: 
            resp1 = client.new_order(
                symbol=symbol, side='BUY', type='LIMIT', quantity=qty, timeInForce='GTC', price=price
            )
            print(symbol, side, "placing order")
            print(resp1)
            sleep(2)
            sl_price = round(price - price * sl, price_precision)
            resp2 = client.new_order(
                symbol=symbol, side='SELL', type='STOP_MARKET', quantity=qty, timeInForce='GTC', stopPrice=sl_price
            )
            print(resp2)
            sleep(2)
            tp_price = round(price + price * tp, price_precision)
            resp3 = client.new_order(
                symbol=symbol, side='SELL', type='TAKE_PROFIT_MARKET', quantity=qty, timeInForce='GTC', stopPrice=tp_price
            )
            print(resp3)
        except ClientError as error:
            print(
                "Found error. status: {}, error code: {}, error message: {}".format(
                    error.status_code, error.error_code, error.error_message
                )
            )
    if side == 'sell':
        try: 
            resp1 = client.new_order(
                symbol=symbol, side='SELL', type='LIMIT', quantity=qty, timeInForce='GTC', price=price
            )
            print(symbol, side, "placing order")
            print(resp1)
            sleep(2)
            sl_price = round(price + price * sl, price_precision)
            resp2 = client.new_order(
                symbol=symbol, side='BUY', type='STOP_MARKET', quantity=qty, timeInForce='GTC', stopPrice=sl_price
            )
            print(resp2)
            sleep(2)
            tp_price = round(price - price * tp, price_precision)
            resp3 = client.new_order(
                symbol=symbol, side='BUY', type='TAKE_PROFIT_MARKET', quantity=qty, timeInForce='GTC', stopPrice=tp_price
            )
            print(resp3)
        except ClientError as error:
            print(
                "Found error. status: {}, error code: {}, error message: {}".format(
                    error.status_code, error.error_code, error.error_message
                )
            )

def check_positions():
    try:
        resp = client.get_position_risk()
        positions = 0
        for e in resp:
            if float(e['positionAmt']) != 0:
                positions += 1
        return positions
    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )

def close_open_orders(symbol):
    try:
        response = client.cancel_open_orders(symbol=symbol, recvWindow=6000)
        print(response)
    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )

# technical analysis
def check_macd_ema(symbol):
    kl = klines(symbol)
    if ta.trend.macd_diff(kl.close).iloc[-1] > 0 and ta.trend.macd_diff(kl.close).iloc[-2] < 0 \
    and ta.trend.ema_indicator(kl.close, window=200).iloc[-1] < kl.close.iloc[-1]:
        return 'up'
    
    elif ta.trend.macd_diff(kl.close).iloc[-1] < 0 and ta.trend.macd_diff(kl.close).iloc[-2] > 0 \
    and ta.trend.ema_indicator(kl.close, window=200).iloc[-1] > kl.close.iloc[-1]:
        return 'down'

    else:
        return 'none'

order = False
symbol = ''
symbols = get_tickers_usdt()

while True:
    positions = check_positions()
    print(f'You have {positions} opened positions')
    if positions == 0:
        order = False
        if symbol != '':
            close_open_orders(symbol)
    
    if order == False:
        for e in symbols:
            signal = check_macd_ema(e)
            if signal == 'up':
                print('Found BUY signal for ', e)
                set_mode(e, type)
                sleep(1)
                set_leverage(e, leverage)
                sleep(1)
                print('Placing order for ', e)
                open_order(e, 'buy')
                symbol = e
                order = True
                break
            if signal == 'down':
                print('Found SELL signal for ', e)
                set_mode(e, type)
                sleep(1)
                set_leverage(e, leverage)
                sleep(1)
                print('Placing order for ', e)
                open_order(e, 'sell')
                symbol = e
                order = True
                break
    print('Waiting 60 sec')
    sleep(60)