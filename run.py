from FlaskApp import app
from CryptoBot import CryptoBot
from threading import Thread

def thread1():
    app.run(debug=True, use_reloader=False)

def thread2():
    CryptoBot.run()

if __name__ == "__main__":
    t1 = Thread(target=thread1).start()
    t2 = Thread(target=thread2).start()

