import sys
import os
import re
from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import json
from flask_sqlalchemy import SQLAlchemy
from helpers import apology, login_required, lookup, usd, crypto_info
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import and_, desc
from decimal import Decimal
import urllib.request
import urllib
# Configure application
app = Flask(__name__)

ENV = ''

if ENV == 'dev':
    app.debug = True # If in Devlopment Mode = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/finance'
else:
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://dtjowfzaqlolpp:abdb685c3766245e9a657874bf78b8c1f11aab9da5da1cba43ff8bb30dd5a4f9@ec2-3-233-7-12.compute-1.amazonaws.com:5432/d2pctr378ve0k9'

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached 
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
#engine = create_engine("sqlite:///finance.db")
#db = scoped_session(sessionmaker(bind=engine))
"""
# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")
"""


# We need to add this line to not have any warnings
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# We create a DataBase object
db = SQLAlchemy(app)

#________________ DATABASE models __________________________
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True, nullable=False)
    username = db.Column(db.String(30), unique=True, nullable=False)
    hash = db.Column(db.String, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    cash = db.Column(db.Numeric, default=10000, nullable=False)
    country = db.Column(db.String, nullable=False)
    def __init__(self, username, hash, email, cash, country):
        # Keep track of id number.
        # Details about users.
        self.username = username # self = this
        self.hash = hash
        self.email = email
        self.cash = cash
        self.country = country
        newUser = self.username
        print(newUser)

    def print_info(self):
        print(f"New username : {self.username}")
        print(f"Email of user : {self.email}")
        print(f"Country of orign : {self.country}")


class History(db.Model):
    __tablename__ = "history"
    transaction_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String, nullable=False)
    operation = db.Column(db.String, nullable=False)
    symbol = db.Column(db.String, nullable=False)
    price = db.Column(db.Numeric, nullable=False)
    shares = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, username, operation, symbol, price, shares, date):
        self.username = username # self = this
        self.operation = operation
        self.symbol = symbol
        self.price = price
        self.shares = shares
        self.date = date

class Portfolio(db.Model):
    __tablename__ = "portfolio"
    id = db.Column(db.Integer,db.ForeignKey('users.id'))
    transaction_id = db.Column(db.Integer, primary_key=True, nullable=False)
    username = db.Column(db.String, nullable=False)
    symbol = db.Column(db.Text, nullable=False)
    shares = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    def __init__(self, id, username, symbol, shares,date):
        self.id
        self.username = username # self = this
        self.symbol = symbol
        self.shares = shares
        self.date = date


class Countries(db.Model):
    __tablename__ = "countries"
    name = db.Column(db.String, nullable=False, primary_key=True)
    def __init__(self,country):
        self.country = country

class Contact(db.Model):
    __tablename__ = "contact"
    name = db.Column(db.String)
    lastname = db.Column(db.String)
    email = db.Column(db.String, nullable=False, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    def __init__(self,name, lastname, email, message):
        self.name = name
        self.lastname = lastname
        self.email = email
        self.message = message

class Deleted(db.Model):
    __tablename__ = "deleted_users"
    reason = db.Column(db.Text, nullable=False)
    email = db.Column(db.String, nullable=False)
    message = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, primary_key=True)
    def __init__(self,reason, email, message,date):
        self.reason = reason
        self.email = email
        self.message = message
        self.date = date

class Crypto(db.Model):
    __tablename__ = "crypto"
    id = db.Column(db.Integer,db.ForeignKey('users.id'), primary_key=True)
    username = db.Column(db.String)
    Bitcoin = db.Column(db.Float)
    Ethereum = db.Column(db.Float)
    Binance = db.Column(db.Float)
    Cardano = db.Column(db.Float)
    Ripple = db.Column(db.Float)
    Dogecoin = db.Column(db.Float)
    def __init__(self, username, Bitcoin, Ethereum, Binance, Cardano, Ripple, Dogecoin):
        self.username = username # self = this
        self.Bitcoin = Bitcoin
        self.Ethereum = Ethereum
        self.Binance = Binance
        self.Cardano = Cardano
        self.Ripple = Ripple
        self.Dogecoin = Dogecoin

class Cryptocurrency(db.Model):
    __tablename__ = "cryptocurrency"
    id = db.Column(db.Integer,db.ForeignKey('users.id'))
    transaction_id = db.Column(db.Integer, primary_key=True, nullable=False)
    username = db.Column(db.String, nullable=False)
    symbol = db.Column(db.Text, nullable=False)
    shares = db.Column(db.Numeric, nullable=False)
    price = db.Column(db.Numeric)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    def __init__(self, id, username, symbol, shares, price, date):
        self.id
        self.username = username # self = this
        self.symbol = symbol
        self.shares = shares
        self.price = price
        self.date = date


'''
#Show portfolio of stocks
# Store the User object of the logged user
username = User.query.filter(User.id==16).first()

# Get all stocks as objects portfolio
stocks = Portfolio.query.filter_by(username=username.username).all()

# The list for all totals
total_sum = []

# Iterate over the stocks list to append the information needed in index.html table
for stock in stocks:
    symbol = str(stock.symbol)
    shares = int(stock.shares)
    name = lookup(symbol)["name"]
    price = lookup(symbol)["price"]
    change = lookup(symbol)["change"]
    total = shares * price
    stock.name = name
    stock.price = usd(price)
    stock.total = usd(total)
    total_sum.append(float(total))

print(stocks[0].shares)
#History.query.order_by(desc(History.date)).all(),

# Join Users and Portfolio table on User.id=Portfolio.id
#xx = db.session.query(User, Portfolio).filter(User.id == Portfolio.id).all()

#zz = db.session.query(User, Portfolio).filter(User.id == Portfolio.id).filter(User.id=='1').all()

#url = "https://api.nomics.com/v1/currencies/sparkline?key=c8817a587f4f0a951898c421825860c7c1124593&ids=BTC&start=2018-04-14T00%3A00%3A00Z&end=2018-05-14T00%3A00%3A00Z"

username = User.query.filter(User.id==16).first()
cryptosOwned = Cryptocurrency.query.filter_by(username=username.username).all()
print(cryptosOwned)
symbol = 'ADA'
name = crypto_info(symbol)["name"]

for crypto in cryptosOwned:
    symbol = str(crypto.symbol)
    shares = float(crypto.shares)
    name = crypto_info(symbol)["name"]
    price = crypto_info(symbol)["price"]
    total = shares * price
    crypto.name = name
    crypto.price = usd(price)
    crypto.total = usd(total)


print(name)
'''


