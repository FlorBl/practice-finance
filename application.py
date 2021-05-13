import os
import re
import mysql.connector
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
import json

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

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
db = SQL("sqlite:///finance.db")


"""
# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")
"""
usernames = db.execute("SELECT username FROM users")
emails = db.execute("SELECT email FROM users")

@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # Store the username of the user logged
    username = db.execute("SELECT username FROM users WHERE id= (:id)", id=int(session["user_id"]))[0]["username"]

    # Get stocks portfolio
    stocks = db.execute("SELECT * FROM portfolio WHERE username = :username ORDER BY symbol ASC", username=username)

    # List to add all totals
    total_sum = []

     # Iterate over the stocks list to append the information needed in index.html table
    for stock in stocks:
        symbol = str(stock["symbol"])
        shares = int(stock["shares"])
        name = lookup(symbol)["name"]
        price = lookup(symbol)["price"]
        change = lookup(symbol)["change"]
        total = shares * price
        stock["change"] = change
        stock["name"] = name
        stock["price"] = usd(price)
        stock["total"] = usd(total)
        total_sum.append(float(total))

    cash = db.execute("SELECT cash FROM users WHERE username = :username", username=username)[0]["cash"]
    total = sum(total_sum) + cash

    return render_template("index.html", stocks=stocks, cash=usd(cash), total=usd(total), username=username)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
       # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        symbol = request.form.get("symbol")
        # Store the dictionary returned from the search in a variable
        share = lookup(symbol)

        # Store the shares inputed
        quantity = int(request.form.get("shares"))

        # If the symbol searched or number of shares is invalid, return apology
        if share is None:
            return apology("invalid symbol", 400)
        elif quantity < 1:
            return apology("value must be positive integer", 400)

        # Store how much money the user has
        cash = db.execute("SELECT cash FROM users WHERE id = (:id)", id=int(session["user_id"]))

        # Store the value of purchase
        value = share["price"] * quantity

        # If the user don't have enough money, apologize
        if int(cash[0]["cash"]) < value:
            return apology("can't afford", 400)
        
        # Get the current user's username
        username = db.execute("SELECT username FROM users WHERE id= (:id)", id=int(session["user_id"]))[0]["username"]

        # Subtract the value of purchase from the user's cash
        db.execute("UPDATE users SET cash = cash - :value WHERE id = :uid", value=value, uid=int(session['user_id']))

        # Add the transaction to the user's history
        db.execute("INSERT INTO history (username, operation, symbol, price, shares) VALUES (:username, 'BUY', :symbol, :price, :shares)",
            username=username, symbol=share["symbol"], price=share["price"], shares=quantity)

        # Update the stock in portfolio
        updated = db.execute("UPDATE portfolio SET shares = shares + :shares WHERE username = :username AND symbol = :symbol",
            shares=quantity, username=username, symbol=share["symbol"])

        if updated != 1:
            # Add the stock to the user's portfolio if it doesn't exist
            db.execute("INSERT INTO portfolio (username, symbol, shares) VALUES (:username, :symbol, :shares)",
            username=username, symbol=share["symbol"], shares=quantity)


        # Send them to the portfolio
        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    username = db.execute("SELECT username FROM users WHERE id= (:id)", id=int(session["user_id"]))[0]["username"]
    stocks = db.execute("SELECT * FROM history WHERE username = (:username) ORDER BY date, time DESC", username=username)

    for stock in stocks:
        symbol = str(stock["symbol"])
        shares = int(stock["shares"])
        operation = stock["operation"]
        price = int(stock["price"])
        date = str(stock["date"])
        time = str(stock["time"])



    return render_template("history.html", stocks=stocks, username=username)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html", users=json.dumps(usernames))


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
def quote():
    if request.method == 'POST':
        share = lookup(request.form.get("symbol"))
        cash = db.execute("SELECT cash FROM users WHERE id = (:id)", id=int(session["user_id"]))

        if not share:
            return apology("Stock not found", 403)

        return render_template("quoted.html",
        name=share["name"],
        price=usd(share["price"]),
        symbol=share["symbol"],
        high=share["high"],
        low=share["low"],balance=json.dumps(cash))

    """Get stock quote."""
    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
            # Ensure the user typed his wished username
        if not request.form.get("username"):
            return apology("must provide username", 403)
        # Ensure the user typed in his password
        elif not request.form.get("password"):
            return apology("must provide password", 403)
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        email = db.execute("SELECT * FROM users WHERE email = ?", request.form.get("email"))

        # Ensure username exists and password is correct
        if len(rows) == 1:
            return apology("Username already exists!", 403)
        elif len(email) == 1:
            return apology("A username already exist with that email!", 403)

        # Get the password and ensure that they match!
        password = request.form.get("password")
        confirm = request.form.get("confirmation")
        if password != confirm:
            return apology("Password does not match!", 403)

        # Ensure the user's password get converted into hashes when inserted into the database
        hash_password = generate_password_hash(password)
      
        new_user = db.execute("INSERT INTO users (username, hash, email, country) VALUES (?, ?, ?, ?)", request.form.get("username"), hash_password, request.form.get("email"), request.form.get("country"))
        message = 'Your registration is completed!'
        return render_template("success.html", message=message)

    return render_template("register.html", countries=COUNTRIES,users=json.dumps(usernames), emails=json.dumps(emails))


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
       # User reached route via POST (as by submitting a form via POST)
    if request.method == 'POST':
        share = lookup(request.form.get("symbol"))
        stock = request.form.get("symbol").upper()
        quantity = int(request.form.get('shares'))
        if not share:
            return apology("Stock not found", 403)
        elif quantity < 1:
            return apology("Please enter the number of shares", 403)

         # Store the dictionary returned from the search in a variable
        value = share["price"] * quantity
        # Get the current user's username
        username = db.execute("SELECT username FROM users WHERE id= (:id)", id=int(session["user_id"]))[0]["username"]
        shares = db.execute("SELECT shares FROM portfolio WHERE username = (:username) AND symbol = (:stock)", username=username, stock=stock)

        cash = db.execute("SELECT cash FROM users WHERE id = (:id)", id=int(session["user_id"]))
        if not shares:
            return apology("You don't own this stock", 403)
        # Check if the user has enough shares
        if int(shares[0]["shares"]) < quantity:
            return apology("Not enough shares", 400)
         # Store how much money the loggen in user has
        db.execute("UPDATE users SET cash = cash + :value WHERE id = :uid", value=value, uid=int(session['user_id']))
        db.execute("UPDATE portfolio SET shares = shares - :quantity WHERE username = (:username)", quantity=quantity, username=username)
        db.execute("DELETE FROM portfolio WHERE shares = '0' AND username = (:username)", username=username)
        # Add the transaction to the user's history
        db.execute("INSERT INTO history (username, operation, symbol, price, shares) VALUES (:username, 'SELL', :symbol, :price, :shares)",
            username=username, symbol=share["symbol"], price=share["price"], shares=quantity)

    return render_template("sell.html")
    """Sell shares of stock"""

@app.route("/customer_service", methods=["GET","POST"])
@login_required
def customer_service():
    if request.method == "POST":
        email = request.form.get("email")
        message = request.form.get("message")
        username = db.execute("SELECT username FROM users WHERE id = (:id)", id=int(session["user_id"]))[0]["username"]

        db.execute("INSERT INTO customer_service (username, message, email) VALUES (:username, :message, :email)", username=username, message=message, email=email)
    return render_template("customer_service.html")

@app.route("/rate", methods=["GET", "POST"])
@login_required
def rate():
    return render_template("rate.html")


def validUsername():
    q = request.args.get("q")
    if q:
        usernames = db.execute("SELECT username FROM users WHERE username LIKE ?", "%" + q + "%")
    else:
        users = []
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

@app.route("/welcome", methods=["GET", "POST"])
def welcome():
    return render_template("welcome.html")

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