from FlaskApp import app
from flask import render_template, redirect, url_for, flash, request
from FlaskApp.models import User
from FlaskApp.forms import RegisterForm, LoginForm
from FlaskApp import db
from flask_login import login_user, logout_user, login_required
from datetime import datetime
import json

@app.route('/')
@app.route('/home')
def home_page():
    return render_template('home.html')


@app.route('/trades', methods=['GET'])
@login_required
def trades_page():
    if request.method == "GET":
        tickers = ['XETHZUSD', 'XXBTZUSD', "MANAUSD", 'GRTUSD', 'LSKUSD', 'SCUSD']
        try:
            with open(r"C:\Users\olive\FlaskApp\CryptoBot\jsonFiles\trades.json", "r") as f:
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
            with open(r"C:\Users\olive\FlaskApp\CryptoBot\jsonFiles\balance.json", "r") as f:
                balance = json.load(f)
        except:
            balance = {}

        return render_template('trades.html', data=data, balance=balance, tickers=tickers)


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        user_to_create = User(username=form.username.data,
                              email_address=form.email_address.data,
                              password=form.password1.data)
        db.session.add(user_to_create)
        db.session.commit()
        login_user(user_to_create)
        flash(f"Account created successfully! You are now logged in as {user_to_create.username}", category='success')
        return redirect(url_for('trades_page'))
    if form.errors != {}:
        for err_msg in form.errors.values():
            flash(f'There was an error with creating a user: {err_msg}', category='danger')

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        attempted_user = User.query.filter_by(username=form.username.data).first()
        if attempted_user and attempted_user.check_password_correction(
                attempted_password=form.password.data
        ):
            login_user(attempted_user)
            flash(f'Success! You are logged in as: {attempted_user.username}', category='success')
            return redirect(url_for('trades_page'))
        else:
            flash('Username and password are not match! Please try again', category='danger')

    return render_template('login.html', form=form)

@app.route('/logout')
def logout_page():
    logout_user()
    flash("You have been logged out!", category='info')
    return redirect(url_for("home_page"))









