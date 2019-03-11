from flask import jsonify, abort, request
from flask_app import app
from app import Account, Position, Trade
from app import util

@app.errorhandler(404)
def error404(error):
    return jsonify({"error": "404 not found"}), 404

@app.errorhandler(500)
def error500(error):
    return jsonify({'error': "application error"}), 500

@app.route('/api/<api_key>/balance', methods=['GET'])
def balance(api_key):
    account = Account.authenticate_api(api_key)
    if not account:
        return jsonify({"error": "authentication error"}), 400
    return jsonify({"username": account.username, "balance": account.balance})

@app.route('/api/price/<ticker>', methods=['GET'])
def lookup(ticker):
    ticker = util.get_price(ticker)
    if not ticker:
        return jsonify({'error': "ticker error"}), 400
    return jsonify({'ticker': ticker})

@app.route('/api/<api_key>/position/<ticker>')
def position(api_key, ticker):
    account = Account.authenticate_api(api_key)
    position = account.get_position_for_json(ticker)
    if not account:
        return jsonify({"error": "authentication error"}), 400
    return jsonify({"position": position})

@app.route('/api/<api_key>/positions', methods=['GET'])
def positions(api_key):
    account = Account.authenticate_api(api_key)
    positions = account.get_positions_json()
    if not account:
        return jsonify({"error": "authentication error"}), 401
    return jsonify({"positions": positions})

@app.route('/api/<api_key>/trades/<ticker>', methods=['GET'])
def trades(api_key, ticker):
    account = Account.authenticate_api(api_key)
    trade = account.trades_for_json(ticker)
    if not account:
        return jsonify({"error": "authentication error"}), 400
    return jsonify({"trade": trade})

@app.route('/api/<api_key>/alltrades', methods=['GET'])
def alltrades(api_key):
    account = Account.authenticate_api(api_key)
    trades = account.get_trades_json()
    if not account:
        return jsonify({"error": "authentication error"}), 400
    return jsonify({"trades": trades})


@app.route('/api/<api_key>/deposit', methods=['PUT'])
def deposit(api_key):
    account = Account.authenticate_api(api_key)
    if not account:
        return jsonify({"error": "authentication error"}), 401
    if not request.json:
        return jsonify({"error": "bad request"}), 400
    try:
        amount = request.json['amount']
        if amount < 0.0:
            raise ValueError
        account.balance += amount
    except (ValueError, KeyError):
        return jsonify({"error": "bad request"}), 400
    account.save()
    return jsonify({"username": account.username, "balance": account.balance})


@app.route('/api/<api_key>/buy/<ticker>/<amount>', methods=['POST'])
def buy(api_key, ticker, amount):
    account = Account.authenticate_api(api_key)
    price = util.get_price(ticker)[1]
    purchase = int(amount) * int(price)
    if not account:
        return jsonify({"error": "authentication error"}), 401
    if not price:
        return jsonify({"error": "bad ticker data"}), 400
    if not request.json:
        return jsonify({"error": "bad request"}), 400
    try:
        if request.json['amount'] and request.json['ticker']:
            if account.balance > purchase:
                account.buy(ticker, int(amount), int(price), purchase)
    except (ValueError, KeyError):
        return jsonify({'error': 'bad request'}), 400
    return jsonify({'username': account.username, "balance": account.balance})

@app.route('/api/<api_key>/sell/<ticker>/<amount>', methods=['GET'])
def sell(api_key, ticker, amount):
    account = Account.authenticate_api(api_key)
    trade = account.trades_for_json(ticker)
    price = util.get_price(ticker)[1]
    position = account.get_position_for_json(ticker) 
    sale = int(amount) * int(price)
    if not account:
        return jsonify({"error": "authentication error"}), 401
    if not price:
        return jsonify({"error": "bad ticker data"}), 400
    if not position:
        return jsonify({"error": "bad position data"}), 400
    if not request.json:
        return jsonify({"error": "bad request"}), 400
    try:
        if request.json['amount'] and request.json['ticker']:
            if trade.volume > position:
                account.buy(ticker, int(amount), int(price), purchase)
    except (ValueError, KeyError):
        return jsonify({'error': 'bad request'}), 400
    return jsonify({'username': account.username, "balance": account.balance})