import sqlite3
from app.orm import ORM
from app.util import hash_password
from app.util import get_price
from app.util import api_key
from app.position import Position
from app.trade import Trade
from app.util import hash_password
from app.view import View 

class Account(ORM):
    tablename = "accounts"
    fields = ["username", "password_hash", "balance", "api_key"]

    def __init__(self, *args, **kwargs):
        self.pk = kwargs.get('pk')
        self.username = kwargs.get('username')
        self.password_hash = kwargs.get('password_hash')
        self.api_key = kwargs.get('api_key')
        self.balance = kwargs.get('balance')
        self.api_key = kwargs.get('api_key')

    @classmethod
    def login(cls, username, password):
        return cls.select_one_where("WHERE username = ? AND password_hash = ?",
                                    (username, hash_password(password)))

    @classmethod
    def authenticate_api(cls,key):
        return cls.select_one_where("WHERE api_key = ?", (key,))

    def set_password(self, password):
        hashed_pw = hash_password(password)
        self.password_hash = hashed_pw 
        return hashed_pw

    def set_api_key(self):
        key = api_key()
        self.api_key = key
        return api_key

    def get_positions(self):
        view = View()
        positions = Position.select_many_where("WHERE accounts_pk = ? AND shares", (self.pk, ))
        for position in positions:
            view.positions(self, position)

    def get_position_for_json(self, ticker):
        get_positions = {}
        position = Position.select_one_where("WHERE ticker = ? AND accounts_pk = ?", (ticker, self.pk))
        get_positions[position.ticker] = {'ticker': position.ticker, 'shares': position.shares}
        return get_positions

    
    def get_positions_json(self):
        positions = {}
        all_positions = Position.select_many_where("WHERE accounts_pk = ? AND shares", (self.pk, ))
        for position in all_positions:
            positions[position.ticker] = {'ticker': position.ticker, 'shares': position.shares}
        return positions
    
    def get_trades_json(self):
        trades = {}
        all_trades = Trade.select_many_where("WHERE accounts_pk = ?", (self.pk, ))
        for trade in all_trades:
            trades[trade.pk] = {'ticker': trade.ticker, 'volume': trade.volume, 'price': trade.price, 'time': trade.time}
        return trades

    def trades_for_json(self, ticker):
        trades_for_person = {}
        all_trades_for_person = Trade.select_many_where("WHERE accounts_pk = ? AND ticker = ?", (self.pk, ticker))
        for trade_one in all_trades_for_person:
            trades_for_person[trade_one.pk] = {'ticker': trade_one.ticker, 'volume': trade_one.volume, 'price': trade_one.price, 'time': trade_one.time}
        return trades_for_person

    def get_position_for(self, ticker):
        """ return a specific Position object for the user. if the position does not
        exist, return a new Position with zero shares. Returns a Position object """
        position = Position.select_one_where(
            "WHERE ticker = ? AND accounts_pk = ?", (ticker, self.pk))
        if position is None:
            return Position(ticker=ticker, accounts_pk=self.pk, shares=0)
        return position

    def get_trades(self):
        """ return all of the user's trades ordered by time. returns a list of
        Trade objects """
        return Trade.select_many_where("WHERE accounts_pk = ?", (self.pk, ))

    def trades_for(self, ticker):
        """ return all of a user's trades for a given ticker """
        return Trade.select_many_where("WHERE accounts_pk = ? AND ticker = ?", (self.pk, ticker))

    def buy(self, ticker, amount, current_price, total_cost):
        """ make a purchase. raise KeyError for a non-existent stock and
        ValueError for insufficient funds. will create a new Trade and modify
        a Position and alters the user's balance. returns nothing """
        position = self.get_position_for(ticker)
    
        trade = Trade(accounts_pk = self.pk, ticker=ticker, price=current_price, volume = amount)
        self.balance -= total_cost
        position.shares += int(amount)
        position.save()
        trade.save()
        self.save()

    def sell(self, ticker, amount):
        """ make a sale. raise KeyErrror for a non-existent stock and
        ValueError for insufficient shares. will create a new Trade object,
        modify a Position, and alter the self.balance. returns nothing."""
        position = self.get_position_for(ticker)
        
        price = get_price(ticker)[1]
        trade = Trade(accounts_pk = self.pk, ticker=ticker, price=price, volume= -int(amount))
        position.shares -= int(amount)
        self.balance += int(amount) * price
        position.save()
        trade.save()
        self.save()