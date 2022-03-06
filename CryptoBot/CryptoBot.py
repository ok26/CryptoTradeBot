import numpy as np
import pandas as pd
import ta
import json
import time
import krakenex 


k = krakenex.API() 
tickers = ['XETHZUSD', 'XXBTZUSD', "MANAUSD", 'GRTUSD', 'LSKUSD', 'SCUSD']
interval = 1


def load_data():
    with open(r"C:\Users\olive\FlaskApp\CryptoBot\jsonFiles\data.json", 'r') as f:
        data = json.load(f) 
    return data

def save_data(data):
    with open(r'C:\Users\olive\FlaskApp\CryptoBot\jsonFiles\data.json', 'w') as f:
        json.dump(data, f, indent=4)

def load_balance():
    with open(r"C:\Users\olive\FlaskApp\CryptoBot\jsonFiles\balance.json", "r") as f:
        try:
            return json.load(f)
        except:
            return {"USD":"1000.0", "LiveUSD":"1000.0"}

def update_balance(amount,ticker,price,sold):
    balance = load_balance()
    if sold:
        balance.pop(ticker)
        balance["USD"] = str(float(balance["USD"]) + amount*price)
    else:
        balance["USD"] = str(float(balance["USD"]) - amount*price)
        balance[ticker] = str(amount)
    save_balance(balance) 
    return balance

def save_balance(balance):
    with open(r"C:\Users\olive\FlaskApp\CryptoBot\jsonFiles\balance.json", "w") as f:
        json.dump(balance, f, indent=4)
    
def load_trades():
    with open(r"C:\Users\olive\FlaskApp\CryptoBot\jsonFiles\trades.json", "r") as f:
        try:
            trades = json.load(f)
        except:
            trades = {}
            for ticker in tickers:
                trades[ticker] = []
    return trades

def save_trade(close, ticker, sold, amount, time):
    trades = load_trades()
    if sold:
        trades[ticker][-1]["Sold"] = time
        trades[ticker][-1]["SellingPrice"] = close
    else:
        trade = {
            "Bought" : time,
            "Sold" : 0,
            "PurchasePrice" : close,
            "SellingPrice" : 0,
            "Amount" : amount
        }
        trades[ticker].append(trade)
        if len(trades[ticker]) > 5:
            trades[ticker] = trades[ticker][-5:]
    with open(r"C:\Users\olive\FlaskApp\CryptoBot\jsonFiles\trades.json", "w") as f:
        json.dump(trades, f, indent=4)

def get_latest_trade(ticker):
    trades = load_trades()
    trade_time = trades[ticker][-1]["Bought"]
    return trade_time

def get_funds():
    balance = load_balance()
    money = float(balance["USD"])
    not_owned = 6-(len(balance)-2)
    funds = money/not_owned
    return funds

def buy(crypto_data, ticker):
    price = float(crypto_data["Close"][-1])
    funds = get_funds()
    amount = funds/price
    balance = update_balance(amount, ticker, price, False)
    save_trade(price, ticker, False, amount, crypto_data["Time"][-1])

def sell(crypto_data, ticker):
    balance = load_balance()
    price = float(crypto_data["Close"][-1])
    amount = float(balance[ticker])
    balance = update_balance(amount, ticker, price, True)
    save_trade(price, ticker, True, amount, crypto_data["Time"][-1])


def update_LiveUSD():
    data = load_data()
    trades = load_trades()
    balance = load_balance()
    balance["LiveUSD"] = balance["USD"]
    for ticker in tickers:
        if ticker in balance:
            balance["LiveUSD"] = str(float(balance["LiveUSD"])+float(trades[ticker][-1]["Amount"])*float(data[ticker]["Close"][-1]))
    save_balance(balance)

def add_new_data(data, ticker, new_data):
    data[ticker]["Close"].append(new_data[2])
    data[ticker]["Open"].append(new_data[1])
    data[ticker]["Time"].append(new_data[0])
    data[ticker]["Close"] = data[ticker]["Close"][-200:]
    data[ticker]["Open"] = data[ticker]["Open"][-200:]
    data[ticker]["Time"] = data[ticker]["Time"][-200:]


def get_history_data(ticker, since):
    history_data = k.query_public('OHLC', data = {'pair': ticker, "interval":interval, 'since': since})
    history_data = history_data["result"][ticker]
    try:
        data = load_data()
        data[ticker] = {"Time": [], "Open": [], "Close": []}
    except:
        data = {ticker: {"Time": [], "Open": [], "Close": []}}
    for i in range(len(history_data)):
        history_data[i] = history_data[i][:2] + history_data[i][-4:-3]
        add_new_data(data, ticker, history_data[i])
    save_data(data)



def get_new_data(ticker):
    new_data = k.query_public('OHLC', data = {'pair': ticker, 'since': time.time()})
    new_data = new_data["result"][ticker]
    new_data = new_data[0][:2] + new_data[0][-4:-3] 
    data = load_data()
    add_new_data(data, ticker, new_data)
    save_data(data)



def RSIcalc(ticker):
    data = load_data()
    df = pd.DataFrame(data[ticker], columns=["Time","Open","Close","MA200","RSI","Signal"])
    df.Open = pd.to_numeric(df.Open)
    df.Close = pd.to_numeric(df.Close)
    df["MA200"] = ta.trend.sma_indicator(df.Close, window=110)
    df["RSI"] = ta.momentum.rsi(df.Close, window=6)
    df["Signal"] = np.where((df.Close > df.MA200) & (df.RSI < 30), True, False)
    df = df.set_index("Time")
    check_signal_buy(df, ticker, data)
    
    

def check_signal_buy(df, ticker, data):
    balance = load_balance()
    if ticker in balance:
        latest_trade_time = get_latest_trade(ticker)
        if int(data[ticker]["Time"][-1]) - int(latest_trade_time) > (interval*60*17):
            sell(data[ticker], ticker)
        elif df.RSI.iloc[-1] > 45:
            sell(data[ticker], ticker)
    elif df.Signal.iloc[-1]:
        buy(data[ticker], ticker)
   


def run():
    for ticker in tickers:
        get_history_data(ticker, time.time()-(interval*60*150))
    while True:
        time.sleep(interval*60)
        for ticker in tickers:
            try:
                get_new_data(ticker)
                RSIcalc(ticker)
                update_LiveUSD()
            except Exception as err:
                print(err)