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
from sqlalchemy import create_engine, and_, desc
from sqlalchemy.orm import scoped_session, sessionmaker
from decimal import Decimal
import urllib.request
import urllib



# Configure application
app = Flask(__name__)

ENV = ''

def default(o):
    return o._asdict()

if ENV == 'dev':
    app.debug = True # If in Devlopment Mode = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/finance'
else:
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://dtjowfzaqlolpp:abdb685c3766245e9a657874bf78b8c1f11aab9da5da1cba43ff8bb30dd5a4f9@ec2-3-233-7-12.compute-1.amazonaws.com:5432/d2pctr378ve0k9'


# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached 
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

app.secret_key = "supersecretkey"
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


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    #Show portfolio of stocks
    # Store the User object of the logged user
    username = User.query.filter(User.id==int(session["user_id"])).first()

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

    # Logged user's cash balance
    cash = username.cash

    # Get the Total balance
    total = sum(total_sum) + float(cash)

    return render_template("index.html", username=username.username,total=usd(total), stocks=stocks,cash=usd(cash))

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    username = User.query.filter(User.id==int(session["user_id"])).first()
    """Buy shares of stock"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        symbol = request.form["symbol"]

        # Stores user's symbol input, returns stock info
        share = lookup(symbol)

        # Stores user's shares quantity input
        quantity = int(request.form["shares"])

        # If the symbol searched or number of shares is invalid, return apology
        if share is None:
            return apology("invalid symbol", 400)
        elif quantity < 1:
            return apology("value must be positive integer", 400)

        # Get the current user's User Object
        username = User.query.filter(User.id==int(session["user_id"])).first()
        # Username of User
        LoggedUser = username.username
        # Gets User's ID #
        id = username.id
        # Gets User's cash balance
        cash = username.cash

        # Store the value of purchase
        value = share["price"] * quantity

        # If the user don't have enough money, apologize
        if cash < value:
            return apology("can't afford", 400)
        

        # Subtract the value of purchase from the user's cash
        username.cash = float(cash) - value

        # Add details to History table
        operation='BUY'
        symbol = symbol
        price = share['price']
        shares=quantity
        date = datetime.now()

        # Add the transaction to the user's history
        update_History = History(LoggedUser,operation, symbol, price, shares, date)

        # Check if stock exists in user's Portfolio
        stock_exists = Portfolio.query.filter(and_(Portfolio.username==LoggedUser, Portfolio.symbol==symbol)).all()

        # Add stock to user's Portfolio if it doesn't exist
        if len(stock_exists) != 1:
            add_stock = Portfolio(id,LoggedUser,symbol,shares,date)
            db.session.add(add_stock)
        else:
            # If stock exists, get it's ID
            updatePortfolio = Portfolio.query.filter(and_(Portfolio.username==LoggedUser, Portfolio.symbol==symbol)).first()
            id = updatePortfolio.id
            updatePortfolio.shares += quantity
            # Update the shares, after the transaction


        db.session.add(update_History)
        db.session.commit()

        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    """Show history of transactions"""
    # Gets User Object of logged user
    username = User.query.filter_by(id=int(session["user_id"])).first()

    # Saves user's username 
    LoggedUser = username.username
    # Gets user's stocks as objects
    stocks = History.query.filter_by(username=LoggedUser).all()


    return render_template("history.html", stocks=stocks, username=LoggedUser)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()
    # Copy usernames into the list for username availability
    usernames2 = []
    users = User.query.all()
    for i in range(len(users)):
        usernames2.append(users[i].username)
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form["username"]:
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form["password"]:
            return apology("must provide password", 403)

        # Get the input from username field
        username =  request.form["username"]

        # Query database for that username
        rows = User.query.filter(User.username==username).all()
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0].hash, request.form["password"]):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0].id

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html", users=json.dumps(usernames2), usernames=usernames2)


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == 'POST':
        # Saves stock's info entered by user
        share = lookup(request.form["symbol"])

        # Contains the User Object
        username = User.query.filter(User.id==int(session["user_id"])).first()
        user_cash = usd(username.cash)

        if not share:
            return apology("Stock not found", 403)

        return render_template("quoted.html",
        name=share["name"],
        price=usd(share["price"]),
        symbol=share["symbol"],
        high=share["high"],
        low=share["low"],balance=json.dumps(user_cash))

    """Get stock quote."""
    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Copy username into a list for availability
    usernames2 = []
    users = User.query.all()
    for i in range(len(users)):
        usernames2.append(users[i].username)

    emails = []
    user_emails = User.query.all()
    for i in range(len(user_emails)):
        emails.append(user_emails[i].email)
    if request.method == "POST":
            # Ensure the user typed his wished username
        if not request.form["username"]:
            return apology("must provide username", 403)
        # Ensure the user typed in his password
        elif not request.form["password"]:
            return apology("must provide password", 403)

        # Get username from input field
        username =  request.form["username"]
        # Get email from input field
        email = request.form["email"]
        # Get country from input field
        country = request.form["country"]
        # Search if the user exists
        rows = User.query.filter(User.username==username).all()
        if len(rows) == 1:
            return apology("Username already exists!", 403)

        # Get the password and ensure that they match!
        password = request.form["password"]
        confirm = request.form["confirmation"]
        if password != confirm:
            return apology("Password does not match!", 403)

        # Ensure the user's password get converted into hashes when inserted into the database
        hash = generate_password_hash(password)

        # Create new user
        cash = '10000'
        new_user = User(username,hash,email,cash,country)
        db.session.add(new_user)
        db.session.commit()
        message = 'Your registration is completed!'
        #return render_template("success.html", message=message)


    return render_template("register.html", countries=COUNTRIES,users=json.dumps(usernames2),emails=json.dumps(emails))


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
        #Sell shares of stock
    username = User.query.get(int(session["user_id"]))
        # Get all stocks as objects portfolio
    stockss = Portfolio.query.filter_by(username=username.username).all()

    balance = float("{:.2f}".format(username.cash))

    stonks = []
    stonk = Portfolio.query.all()
    for i in range(len(stonk)):
        stonks.append(stonk[i].symbol)

    # Iterate over the stocks list to append the information needed in index.html table
    for stocks in stockss:
        symbol = str(stocks.symbol)
        shares = int(stocks.shares)
        name = lookup(symbol)["name"]
        price = lookup(symbol)["price"]
        change = lookup(symbol)["change"]
        total = shares * price
        stocks.name = name
        stocks.price = usd(price)
        stocks.total = usd(total)

    if request.method == 'POST':
        
        # Lookup stock and save it's info
        share = lookup(request.form["share"])
        stock = request.form["share"].upper()
        # Get # of shares
        quantity = int(request.form["quantity"])

        if not share:
            return apology("Stock not found", 403)
        elif quantity < 1:
            return apology("Please enter the number of shares", 403)

        # Store Total value, shares * quantity
        value = share["price"] * quantity
        # Get the current user's user object
        User_Object = User.query.filter(User.id==int(session["user_id"])).first()
        # Username of User
        username = User_Object.username
        # Gets User's ID #
        id = User_Object.id
        # Gets User's cash balance
        cash = User_Object.cash

        
        # Get number of shares the logged-in user has of the entered stock
        user_shares = Portfolio.query.filter(and_(Portfolio.username==username, Portfolio.symbol==stock)).first()
        shares = user_shares.shares


        if not shares:
            return apology("You don't own this stock", 403)
        # Check if the user has enough shares
        if int(shares) < quantity:
            return apology("Not enough shares", 400)

        # Update user's cash balance after transaction
        updateCash = User.query.get(int(session["user_id"]))
        updateCash.cash = float(cash) + value

        # Get id of row matching the username and sold stock
        updatePortfolio = Portfolio.query.filter(and_(Portfolio.username==username, Portfolio.symbol==stock)).first()

        # Update shares after transaction
        updateShares = Portfolio.query.get(updatePortfolio.transaction_id)
        updateShares.shares -= quantity

        # If 0 shares, remove stock from Portfolio
        check_shares = Portfolio.query.filter(and_(Portfolio.username==username, Portfolio.shares=='0')).all()
        # If there are rows with 0 shares.
        if len(check_shares) == 1:
            # Search for that row
            deleteStock = Portfolio.query.filter(and_(Portfolio.username==username, Portfolio.shares=='0')).first()

            # Get and delete the selected row
            removeRow = Portfolio.query.get(deleteStock.transaction_id)
            db.session.delete(removeRow)

        operation='SELL'
        price = share['price']
        shares=quantity
        date = datetime.now()
        # Add the transaction to the user's history
        UpdateHistory = History(username,operation, stock, price, shares, date)
        db.session.add(UpdateHistory)
        
        # Saves changes
        db.session.commit()
        # return redirect("/")

    return render_template("sell.html", stockss=stockss, balance=json.dumps(balance))
    return jsonify({'error' : 'Missing data!'})


@app.route("/customer_service", methods=["GET","POST"])
@login_required
def customer_service():
    if request.method == "POST":
        email = request.form["email"]
        message = request.form["message"]
        username = db.execute("SELECT username FROM users WHERE id = (:id)", id=int(session["user_id"]))[0]["username"]

        db.execute("INSERT INTO customer_service (username, message, email) VALUES (:username, :message, :email)", username=username, message=message, email=email)
    return render_template("customer_service.html")

@app.route("/rate", methods=["GET", "POST"])
@login_required
def rate():
    user = User.query.filter(User.id==int(session["user_id"])).first()
    id=user.id
    emails = user.email
    if request.method == 'POST':
        user = User.query.filter(User.id==int(session["user_id"])).first()
        id=user.id
        emails = user.email
        message = request.form['message']
        reason = request.form['reason']
        email = request.form['email']
        reason = reason
        message = message
        email = email
        date = datetime.now()
        deleted = Deleted(reason,email,message,date)
        db.session.add(deleted)

        user_portfolio = Portfolio.query.filter(Portfolio.username==user.username).all()

        x = []
        for i in range(len(user_portfolio)):
            x.append(user_portfolio[i])
        if len(x) > 0:
            delete = Portfolio.query.filter(Portfolio.username==user.username).first()
            db.session.delete(delete)
            db.session.commit()

        delete_user = User.query.get(id)
        db.session.delete(delete_user)
        db.session.commit()
        # Forget any user_id
        session.clear()
        deleteMessage = "You account has been deleted!"
        # Redirect user to login form
        return render_template("success.html", message=deleteMessage)
        session.clear()
        return redirect('/')


    return render_template("rate.html", emails=json.dumps(emails))

@app.route("/crypto", methods=["GET", "POST"])
@login_required
def crypto():
        # Store the User object of the logged user
    username = User.query.filter(User.id==int(session["user_id"])).first()

    # Info about our 6 Cryptocurrencies
    url = "https://api.nomics.com/v1/currencies/ticker?key=8359a16b23c77eed9ab3298d72106e7783bc32dc&ids=BTC,ETH,BNB,ADA,XRP,DOGE,SHIBA,DOT,LTC,MATIC,SHIB&interval=1d,30d&convert=USD&per-page=100&page=1"

    crypto = urllib.request.urlopen(url)
    cryptojson = crypto.read()
    cryptojdata = json.loads(cryptojson)

    cryptos = []
    for i in range(len(cryptojdata)):
        cryptos.append(cryptojdata[i])

    for crypto in cryptos:
        symbol = crypto['id'].upper()
        name = crypto['name']
        price = float(crypto['price'])
        crypto['price'] = usd(price)
        logo = crypto['logo_url']

    # Get all cryptos as objects portfolio
    cryptosOwned = Cryptocurrency.query.filter_by(username=username.username).all()


    # The list for all totals
    total_sum = []
    user_cryptos = []
    # The list for all totals
    for i in range(len(cryptosOwned)):
        user_cryptos.append(cryptosOwned[i])
    # Iterate over the stocks list to append the information needed in index.html table
    for crypto in user_cryptos:
        symbol = str(crypto.symbol)
        shares = float(crypto.shares)
        price = float(crypto.price)
        crypto.price = usd(price)
        cryptocash = float(shares) * float(price)
        crypto.cryptocash = usd(cryptocash)

    return render_template("crypto.html",cryptos=cryptos, cryptosOwned=user_cryptos)

@app.route("/buycrypto", methods=["GET", "POST"])
@login_required
def buycrypto():
    if request.method == 'POST':
        username = User.query.filter(User.id==int(session["user_id"])).first()
        cash = float(username.cash)
        LoggedUser = username.username
        CryptoSymbol = request.form['cryptosymbol']
        amount = request.form['buyamount']
        Crypto = crypto_info(CryptoSymbol)
        symbol = Crypto['symbol'].upper()
        name = Crypto['name']
        price = float(Crypto['price'])


        cryptoPurchased = float(amount) / price
        # Update user's balance
        username.cash = cash - float(amount)

        # Add details to History table
        operation='BUY'
        symbol = symbol
        price = price
        shares=cryptoPurchased
        date = datetime.now()

        # Add the transaction to the user's history
        update_History = History(LoggedUser,operation, symbol, price, shares, date)
        db.session.add(update_History)
        db.session.commit()
        # Check if stock exists in user's Portfolio
        symbol_exists = Cryptocurrency.query.filter(and_(Cryptocurrency.username==LoggedUser, Cryptocurrency.symbol==symbol)).all()
        # Add stock to user's Portfolio if it doesn't exist
        user_id = username.id
        if len(symbol_exists) != 1:
            add_symbol = Cryptocurrency(user_id,LoggedUser,symbol,shares,price,date)
            db.session.add(add_symbol)
            db.session.commit()
        else:
            # If stock exists, get it's ID
            updatePortfolio = Cryptocurrency.query.filter(and_(Cryptocurrency.username==LoggedUser, Cryptocurrency.symbol==symbol)).first()
            id = updatePortfolio.transaction_id
            UpdateNow = Cryptocurrency.query.get(id)
            UpdateNow.shares += Decimal(shares)
            db.session.commit()
            # Update the shares, after the transaction

            
    return render_template("/crypto.html")


# Sell crypto
@app.route("/sellcrypto", methods=["GET", "POST"])
@login_required
def sellcrypto():
    if request.method == 'POST':
        username = User.query.filter(User.id==int(session["user_id"])).first()
        cash = float(username.cash)
        LoggedUser = username.username

        CryptoSymbol = request.form["cryptosmbl"]
        quantity = float(request.form["sellamount"])

        Crypto = crypto_info(CryptoSymbol)

        price = float(Crypto['price'])

        # Check if stock exists in user's Portfolio
        shares = Cryptocurrency.query.filter(and_(Cryptocurrency.username==LoggedUser, Cryptocurrency.symbol==CryptoSymbol)).all()
        quantityOwed = shares[0].shares

        if quantity > quantityOwed:
            return apology('Enter a lower quantity', 400)
        else:
            cryptoSold = quantity * price
            # Update user's balance
            username.cash = cash + cryptoSold

            # Add details to History table
            operation='SELL'
            symbol = CryptoSymbol
            price = price
            shares = quantity
            date = datetime.now()

            # Add the transaction to the user's history
            update_History = History(LoggedUser,operation, symbol, price, shares, date)
            db.session.add(update_History)
            db.session.commit()
            # Check if stock exists in user's Portfolio
            symbol_exists = Cryptocurrency.query.filter(and_(Cryptocurrency.username==LoggedUser, Cryptocurrency.symbol==symbol)).all()
            # Add stock to user's Portfolio if it doesn't exist
            user_id = username.id

            # If stock exists, get it's ID
            updatePortfolio = Cryptocurrency.query.filter(and_(Cryptocurrency.username==LoggedUser, Cryptocurrency.symbol==symbol)).first()
            id = updatePortfolio.transaction_id
            UpdateNow = Cryptocurrency.query.get(id)
            UpdateNow.shares -= Decimal(shares)
            db.session.commit()
        return render_template("crypto.html")


def validUsername():
    q = request.args.get("q")
    if q:
        usernames = db.execute("SELECT username FROM users WHERE username LIKE ?", "%" + q + "%")
    else:
        users = []
    usernames = db.execute("SELECT username FROM users")    
    return jsonify(usernames)



# Lookup this error sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread. The object was created in thread id 17032 and this is thread id 1456.
def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

def checkBalance():
    cash = db.execute("SELECT cash FROM users WHERE id = (:id)", id=int(session["user_id"]))
    return render_template("quote.html", balance=json.dumps(cash))

@app.route("/content", methods=["GET", "POST"])
def welcome():
    if request.method == "POST":
        name = request.form["name"]
        lastname = request.form["lastname"]
        email = request.form["email"]
        message = request.form["message"]
        name=name
        lastname=lastname
        email=email
        message=message
        add_message = Contact(name,lastname,email,message)
        db.session.add(add_message)
        db.session.commit()
        message = 'We will get back to you shortly!'



    return render_template("content.html")


def main():
    db.session.commit()

if __name__ == "__main__":
    with app.app_context():
        main()



COUNTRIES = [
    "Canada",
  "Åland Islands",
  "Albania",
  "Algeria",
  "American Samoa",
  "Andorra",
  "Angola",
  "Anguilla",
  "Antarctica",
  "Antigua and Barbuda",
  "Argentina",
  "Armenia",
  "Aruba",
  "Australia",
  "Austria",
  "Azerbaijan",
  "Bahamas (the)",
  "Bahrain",
  "Bangladesh",
  "Barbados",
  "Belarus",
  "Belgium",
  "Belize",
  "Benin",
  "Bermuda",
  "Bhutan",
  "Bolivia (Plurinational State of)",
  "Bonaire, Sint Eustatius and Saba",
  "Bosnia and Herzegovina",
  "Botswana",
  "Bouvet Island",
  "Brazil",
  "British Indian Ocean Territory (the)",
  "Brunei Darussalam",
  "Bulgaria",
  "Burkina Faso",
  "Burundi",
  "Cabo Verde",
  "Cambodia",
  "Cameroon",
  "Cayman Islands (the)",
  "Central African Republic (the)",
  "Chad",
  "Chile",
  "China",
  "Christmas Island",
  "Cocos (Keeling) Islands (the)",
  "Colombia",
  "Comoros (the)",
  "Congo (the Democratic Republic of the)",
  "Congo (the)",
  "Cook Islands (the)",
  "Costa Rica",
  "Croatia",
  "Cuba",
  "Curaçao",
  "Cyprus",
  "Czechia",
  "Côte d'Ivoire",
  "Denmark",
  "Djibouti",
  "Dominica",
  "Dominican Republic (the)",
  "Ecuador",
  "Egypt",
  "El Salvador",
  "Equatorial Guinea",
  "Eritrea",
  "Estonia",
  "Eswatini",
  "Ethiopia",
  "Falkland Islands (the) [Malvinas]",
  "Faroe Islands (the)",
  "Fiji",
  "Finland",
  "France",
  "French Guiana",
  "French Polynesia",
  "French Southern Territories (the)",
  "Gabon",
  "Gambia (the)",
  "Georgia",
  "Germany",
  "Ghana",
  "Gibraltar",
  "Greece",
  "Greenland",
  "Grenada",
  "Guadeloupe",
  "Guam",
  "Guatemala",
  "Guernsey",
  "Guinea",
  "Guinea-Bissau",
  "Guyana",
  "Haiti",
  "Heard Island and McDonald Islands",
  "Holy See (the)",
  "Honduras",
  "Hong Kong",
  "Hungary",
  "Iceland",
  "India",
  "Indonesia",
  "Iran (Islamic Republic of)",
  "Iraq",
  "Ireland",
  "Isle of Man",
  "Israel",
  "Italy",
  "Jamaica",
  "Japan",
  "Jersey",
  "Jordan",
  "Kazakhstan",
  "Kenya",
  "Kiribati",
  "Korea (the Democratic People's Republic of)",
  "Korea (the Republic of)",
  "Kosovo",
  "Kuwait",
  "Kyrgyzstan",
  "Lao People's Democratic Republic (the)",
  "Latvia",
  "Lebanon",
  "Lesotho",
  "Liberia",
  "Libya",
  "Liechtenstein",
  "Lithuania",
  "Luxembourg",
  "Macao",
  "Madagascar",
  "Malawi",
  "Malaysia",
  "Maldives",
  "Mali",
  "Malta",
  "Marshall Islands (the)",
  "Martinique",
  "Mauritania",
  "Mauritius",
  "Mayotte",
  "Mexico",
  "Micronesia (Federated States of)",
  "Moldova (the Republic of)",
  "Monaco",
  "Mongolia",
  "Montenegro",
  "Montserrat",
  "Morocco",
  "Mozambique",
  "Myanmar",
  "Namibia",
  "Nauru",
  "Nepal",
  "Netherlands (the)",
  "New Caledonia",
  "New Zealand",
  "Nicaragua",
  "Niger (the)",
  "Nigeria",
  "Niue",
  "Norfolk Island",
  "Northern Mariana Islands (the)",
  "Norway",
  "Oman",
  "Pakistan",
  "Palau",
  "Palestine, State of",
  "Panama",
  "Papua New Guinea",
  "Paraguay",
  "Peru",
  "Philippines (the)",
  "Pitcairn",
  "Poland",
  "Portugal",
  "Puerto Rico",
  "Qatar",
  "Republic of North Macedonia",
  "Romania",
  "Russian Federation (the)",
  "Rwanda",
  "Réunion",
  "Saint Barthélemy",
  "Saint Helena, Ascension and Tristan da Cunha",
  "Saint Kitts and Nevis",
  "Saint Lucia",
  "Saint Martin (French part)",
  "Saint Pierre and Miquelon",
  "Saint Vincent and the Grenadines",
  "Samoa",
  "San Marino",
  "Sao Tome and Principe",
  "Saudi Arabia",
  "Senegal",
  "Serbia",
  "Seychelles",
  "Sierra Leone",
  "Singapore",
  "Sint Maarten (Dutch part)",
  "Slovakia",
  "Slovenia",
  "Solomon Islands",
  "Somalia",
  "South Africa",
  "South Georgia and the South Sandwich Islands",
  "South Sudan",
  "Spain",
  "Sri Lanka",
  "Sudan (the)",
  "Suriname",
  "Svalbard and Jan Mayen",
  "Sweden",
  "Switzerland",
  "Syrian Arab Republic",
  "Taiwan (Province of China)",
  "Tajikistan",
  "Tanzania, United Republic of",
  "Thailand",
  "Timor-Leste",
  "Togo",
  "Tokelau",
  "Tonga",
  "Trinidad and Tobago",
  "Tunisia",
  "Turkey",
  "Turkmenistan",
  "Turks and Caicos Islands (the)",
  "Tuvalu",
  "Uganda",
  "Ukraine",
  "United Arab Emirates (the)",
  "United Kingdom of Great Britain and Northern Ireland (the)",
  "United States Minor Outlying Islands (the)",
  "United States of America (the)",
  "Uruguay",
  "Uzbekistan",
  "Vanuatu",
  "Venezuela (Bolivarian Republic of)",
  "Viet Nam",
  "Virgin Islands (British)",
  "Virgin Islands (U.S.)",
  "Wallis and Futuna",
  "Western Sahara",
  "Yemen",
  "Zambia",
  "Zimbabwe"
]

