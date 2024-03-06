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
        for elem in response:
            if elem['asset'] == 'USDT':
                return float(elem['balance'])
        
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
    for elem in resp:
        if 'USDT' in elem['symbol']:
            tickers.append(elem['symbol'])
    return tickers

print(get_tickers_usdt())
