# database/tv_search.py

from openalgo.database.symbol import SymToken


def search_symbols(symbol,exchange):
    return SymToken.query.filter(SymToken.symbol == symbol,SymToken.exchange == exchange).all()
