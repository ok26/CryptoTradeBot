#Importerar bibliotek
import numpy as np
import pandas as pd
import ta
import json
import time
import krakenex 

#Sättter up API och väljer interval på sökningar samt vilka cryptor som ska användas
k = krakenex.API() 
tickers = ['XETHZUSD', 'XXBTZUSD', "MANAUSD", 'GRTUSD', 'LSKUSD', 'SCUSD']
interval = 1


def load_data():
    #Laddar sparad data från data dokumentet
    with open("CryptoBot/jsonFiles/data.json", 'r') as f:
        data = json.load(f) 
    return data

def save_data(data):
    #Sparar data till data dokumentet
    with open("CryptoBot/jsonFiles/data.json", 'w') as f:
        json.dump(data, f, indent=4)

def load_balance():
    #Laddar den senaste saldot från balance dokumentet
    with open("CryptoBot/jsonFiles/balance.json", "r") as f:
        try:
            return json.load(f)
        except:
            #Om ingen data finns så sätts saldot deafult till 1000 dollar
            return {"USD":"1000.0", "LiveUSD":"1000.0"}

def update_balance(amount,ticker,price,sold):
    #Uppdaterar saldot efter en köpt eller såld crypto
    balance = load_balance()
    if sold:
        #Om såld så tas crypton bort från saldot och dess värde läggs till på saldots dollar
        balance.pop(ticker)
        balance["USD"] = str(float(balance["USD"]) + amount*price)
    else:
        #Om köpt så läggs crypton till i saldot och cryptons värde tas bort från saldots dollar
        balance["USD"] = str(float(balance["USD"]) - amount*price)
        balance[ticker] = str(amount)
    save_balance(balance) 
    return balance

def save_balance(balance):
    #Sparar updaterat saldo till balance dokumentet
    with open("CryptoBot/jsonFiles/balance.json", "w") as f:
        json.dump(balance, f, indent=4)
    
def load_trades():
    #Laddar alla trades som hittils utförts från trades dokumentet
    with open("CryptoBot/jsonFiles/trades.json", "r") as f:
        try:
            trades = json.load(f)
        except:
            #Om ingen tidigare data finns så skapas en tom lista för framtida trades för varje crypto
            trades = {}
            for ticker in tickers:
                trades[ticker] = []
    return trades

def save_trade(close, ticker, sold, amount, time):
    #Sparar en nyligen genomfört trade till trades dokumentet
    trades = load_trades()
    if not sold:
        #Om crypton köptes så sparas all data som är tillgänglig och annan sätts till 0
        trade = {
            "Bought" : time,
            "Sold" : 0,
            "PurchasePrice" : close,
            "SellingPrice" : 0,
            "Amount" : amount
        }
        trades[ticker].append(trade)

        #Sparar max 5 trades per crypto
        if len(trades[ticker]) > 5:
            trades[ticker] = trades[ticker][-5:]

    else:
      #Om crypton såldes så läggs den sista datan till i den senaste traden
      trades[ticker][-1]["Sold"] = time
      trades[ticker][-1]["SellingPrice"] = close
        
    with open("CryptoBot/jsonFiles/trades.json", "w") as f:
        json.dump(trades, f, indent=4)
    

def get_latest_trade(ticker):
    #Hittar tiden då senaste traden för en viss crypto genomfördes
    trades = load_trades()
    trade_time = trades[ticker][-1]["Bought"]
    return trade_time

def get_funds():
    #Räknar ut hur mycket pengar boten kan lägga på nästa köp för att inte riskera få slut på pengar
    balance = load_balance()
    money = float(balance["USD"])
    not_owned = 6-(len(balance)-2)
    funds = money/not_owned
    return funds

def buy(crypto_data, ticker):
    #Köper en crypto och uppdaterar den data som behövs uppdateras
    price = float(crypto_data["Close"][-1])
    funds = get_funds()
    amount = funds/price
    balance = update_balance(amount, ticker, price, False)
    save_trade(price, ticker, False, amount, crypto_data["Time"][-1])

def sell(crypto_data, ticker):
    #Säljer en crypto och uppdaterar den data som behövs uppdateras
    balance = load_balance()
    price = float(crypto_data["Close"][-1])
    amount = float(balance[ticker])
    balance = update_balance(amount, ticker, price, True)
    save_trade(price, ticker, True, amount, crypto_data["Time"][-1])


def update_LiveUSD():
    #Räknar ut hur många dollar boten hade haft om den i detta tillfället hade sålt alla de cryptorna den håller för tillfället
    data = load_data()
    trades = load_trades()
    balance = load_balance()
    balance["LiveUSD"] = balance["USD"]
    for ticker in tickers:
        if ticker in balance:
            balance["LiveUSD"] = str(float(balance["LiveUSD"])+float(trades[ticker][-1]["Amount"])*float(data[ticker]["Close"][-1]))
    save_balance(balance)

def add_new_data(data, ticker, new_data):
    #Lägger till nyligen nedladdad data till den redan sparade data
    data[ticker]["Close"].append(new_data[2])
    data[ticker]["Open"].append(new_data[1])
    data[ticker]["Time"].append(new_data[0])
    #Håller längden på den totala datan till 200 eftersom algoritmen inte kollar på äldre data än 100-200 interval bak beroende på denns inställningar
    data[ticker]["Close"] = data[ticker]["Close"][-200:]
    data[ticker]["Open"] = data[ticker]["Open"][-200:]
    data[ticker]["Time"] = data[ticker]["Time"][-200:]


def get_history_data(ticker, since):
    #Hämtar historisk data sen en specifik punkt med ett specifikt interval
    history_data = k.query_public('OHLC', data = {'pair': ticker, "interval":interval, 'since': since})
    history_data = history_data["result"][ticker]
    try:
        #Om tidigare data finns så läggs den nuvarande cryptons data till
        data = load_data()
        data[ticker] = {"Time": [], "Open": [], "Close": []}
    except:
        #Om ingen tidigare data finns så skapas ett dictionary vart den nuvarande cryptons data direkt läggs till
        data = {ticker: {"Time": [], "Open": [], "Close": []}}
    for i in range(len(history_data)):
        #Med formen som datan kommer med så ger följande formel datan Time, Open, Close i ordning
        history_data[i] = history_data[i][:2] + history_data[i][-4:-3]
        add_new_data(data, ticker, history_data[i])
    save_data(data)



def get_new_data(ticker):
    #Hämtar den senaste datan för en specifik crypto
    new_data = k.query_public('OHLC', data = {'pair': ticker, 'since': time.time()})
    new_data = new_data["result"][ticker]
    new_data = new_data[0][:2] + new_data[0][-4:-3] 
    data = load_data()
    add_new_data(data, ticker, new_data)
    save_data(data)



def RSIcalc(ticker):
    #Använder RSI för att hitta lämpliga tillfällen att köpa
    data = load_data()
    #Skapar en dataframe för att lättare göra uträkningar
    df = pd.DataFrame(data[ticker], columns=["Time","Open","Close","MA200","RSI","Signal"])
    df.Open = pd.to_numeric(df.Open)
    df.Close = pd.to_numeric(df.Close)
    #Sätter upp 3 kolumner enligt RSI strategin vart den sista anger med ett True value då man bör köpa
    df["MA200"] = ta.trend.sma_indicator(df.Close, window=110)
    df["RSI"] = ta.momentum.rsi(df.Close, window=6)
    df["Signal"] = np.where((df.Close > df.MA200) & (df.RSI < 30), True, False)
    df = df.set_index("Time")
    check_signal_buy(df, ticker, data)
    
    

def check_signal_buy(df, ticker, data):
    #Checkar om man bör köpa eller sälja
    balance = load_balance()
    if ticker in balance:
        #Om crypton finns i balance så kollar boten om den bör sälja
        latest_trade_time = get_latest_trade(ticker)
        if int(data[ticker]["Time"][-1]) - int(latest_trade_time) > (interval*60*17):
            #Säljer om crypton varit hålld i mer än 17 interval
            sell(data[ticker], ticker)
        elif df.RSI.iloc[-1] > 45:
            #Säljer även om RSI värdet för crypton överstiger 45
            sell(data[ticker], ticker)
    elif df.Signal.iloc[-1]:
        #Om man inte äger crypton och senaste värdet på Signal kollumnen är True => Köp crypto
        buy(data[ticker], ticker)
   


def run():
    for ticker in tickers:
        #Hämtar historisk data så att algoritmen direkt kan börja köra
        get_history_data(ticker, time.time()-(interval*60*150))
    while True:
        #Evig loop som hämtar ny data, kollar den och uppdaterar efter de olika värdena
        time.sleep(interval*60)
        for ticker in tickers:
            get_new_data(ticker)
            RSIcalc(ticker)
            update_LiveUSD()
            