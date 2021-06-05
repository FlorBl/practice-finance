import os
import requests
import urllib.parse
import json
import urllib
from flask import redirect, render_template, request, session, json
from functools import wraps
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/content")
        return f(*args, **kwargs)
    return decorated_function

# api_key = os.environ.get("API_KEY"), if we don't want to display the key
def lookup(symbol):
    """Look up quote for symbol."""

    # Contact API
    try:
        api_key = "pk_8a2179db5a5c4bd4a1c8e6e2d6e51cc8"
        url = f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None
        #https://cloud.iexapis.com/stable/stock/aapl/quote?token=pk_8a2179db5a5c4bd4a1c8e6e2d6e51cc8
    # Parse response
    try:
        quote = response.json()
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"],
            "high": float(quote["week52High"]),
            "low": float(quote["week52Low"]),
            "change": float(quote["change"])
        }
    except (KeyError, TypeError, ValueError):
        return None


def usd(value):
    """Format value as USD."""
    return f"{value:,.2f}"

# Crypto function, returns information about the crypto
def crypto_info(selectedSymbol):
    try:
        api_key = 'c8817a587f4f0a951898c421825860c7c1124593'
        url = f"https://api.nomics.com/v1/currencies/ticker?key={api_key}&ids={urllib.parse.quote_plus(selectedSymbol)}&interval=1dd&convert=USD"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    try:
        crypto = response.json()
        return {
            "symbol": crypto[0]["symbol"],
            "name": crypto[0]["name"],
            "price": float(crypto[0]["price"]),
            "logo": crypto[0]["logo_url"]
        }
    except (KeyError, TypeError, ValueError):
        return None
        