from FlaskApp import app
from flask import render_template, request
from datetime import datetime
import json

@app.route('/')
@app.route('/home')
def home_page():
    return render_template('home.html')


@app.route('/trades', methods=['GET'])
def trades_page():
    if request.method == "GET":
        tickers = ['XETHZUSD', 'XXBTZUSD', "MANAUSD", 'GRTUSD', 'LSKUSD', 'SCUSD']
        try:
            with open("CryptoBot/jsonFiles/trades.json", "r") as f:
                data = json.load(f)
            for ticker in tickers:
                for trade in data[ticker]:
                    if trade["Sold"] == 0:
                        trade["Bought"] = datetime.fromtimestamp(trade["Bought"]).strftime('%Y-%m-%d %H:%M:%S')
                    else: 
                        trade["Bought"] = datetime.fromtimestamp(trade["Bought"]).strftime('%Y-%m-%d %H:%M:%S')
                        trade["Sold"] = datetime.fromtimestamp(trade["Sold"]).strftime('%Y-%m-%d %H:%M:%S')
        except:
            data = {}
        try:
            with open("CryptoBot/jsonFiles/balance.json", "r") as f:
                balance = json.load(f)
        except:
            balance = {}

        return render_template('trades.html', data=data, balance=balance, tickers=tickers)