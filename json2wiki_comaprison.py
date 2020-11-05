import pandas as pd
import pytickersymbols as pts
from enum import Enum, unique, auto


@unique
class StockMarketIndex(Enum):
    NO_AFFILIATION = auto()
    S_P_500 = auto()
    NASDAQ100 = auto()
    DJI = auto()


class WikiScanner:
    @classmethod
    def get_index_tickers(cls, index: StockMarketIndex, data_source: str = 'wiki') -> dict:
        """
        get NASDAQ100 tickers, based on https://en.wikipedia.org/wiki/NASDAQ-100.
        get S&P500 tickers, based  on http://en.wikipedia.org/wiki/List_of_S%26P_500_companies.

        :param StockMarketIndex index: which index ticker to pull
        :param str data_source: the data source to use to get data. Currently supported: pytickersymbols package
        ('pyticker'), wikipedia ('wiki)
        :return: dictionary of tickers as keys and company names as values
        :rtype:  dict
        """
        supported_data_sources = ('pyticker', 'wiki')
        if data_source not in supported_data_sources:
            raise ValueError("'" + str(data_source) + "' is an unexpected data source")
        supported_indices = (StockMarketIndex.NASDAQ100, StockMarketIndex.S_P_500, StockMarketIndex.DJI)
        if index not in supported_indices:
            raise RuntimeError("This index not yet implemented")
        tickers = {}
        if 'wiki' == data_source:
            try:
                if StockMarketIndex.NASDAQ100 == index:
                    response = pd.read_html('https://en.wikipedia.org/wiki/NASDAQ-100')
                    tickers = response[3]
                    tickers = {stock['Ticker']: stock['Company'] for idx, stock in tickers.iterrows()}
                if StockMarketIndex.S_P_500 == index:
                    response = pd.read_html('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
                    tickers = response[0]
                    tickers = {stock['Symbol']: stock['Security'] for idx, stock in tickers.iterrows()}
                if StockMarketIndex.DJI == index:
                    response = pd.read_html('https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average')
                    tickers = response[1]
                    tickers = {stock['Symbol'].split()[-1]: stock['Company'] for idx, stock in tickers.iterrows()}
            except Exception:
                raise RuntimeError('unexpected http response format. Wiki page layout may have changed, '
                                   'try another data source.')
        if 'pyticker' == data_source:
            if StockMarketIndex.NASDAQ100 == index:
                response = list(pts.PyTickerSymbols().get_stocks_by_index('NASDAQ 100'))
            if StockMarketIndex.S_P_500 == index:
                response = list(pts.PyTickerSymbols().get_stocks_by_index('S&P 500'))
            if StockMarketIndex.DJI == index:
                response = list(pts.PyTickerSymbols().get_stocks_by_index('DOW JONES'))
            tickers = {stock['symbol']: stock['name'] for stock in response}

        return tickers


if __name__ == '__main__':
    try:
        nasdaq = WikiScanner.get_index_tickers(StockMarketIndex.NASDAQ100, data_source='invalid')
    except ValueError as e:
        print(e)
    nasdaq100_wiki = WikiScanner.get_index_tickers(StockMarketIndex.NASDAQ100, data_source='wiki')
    nasdaq100_pytickersymbols = WikiScanner.get_index_tickers(StockMarketIndex.NASDAQ100, data_source='pyticker')

    surplus_tickers = []
    for ticker in nasdaq100_pytickersymbols:
        if ticker not in nasdaq100_wiki:
            surplus_tickers.append(ticker)
    missing_tickers = []
    for ticker in nasdaq100_wiki:
        if ticker not in nasdaq100_pytickersymbols:
            missing_tickers.append(ticker)
    print('surplus nasdaq100 tickers:')
    print(surplus_tickers)
    print('missing nasdaq100 tickers:')
    print(missing_tickers)

    snoopy_wiki = WikiScanner.get_index_tickers(StockMarketIndex.S_P_500, data_source='wiki')
    snoopy_pytickersymbols = WikiScanner.get_index_tickers(StockMarketIndex.S_P_500, data_source='pyticker')
    surplus_tickers = []
    for ticker in snoopy_pytickersymbols:
        if ticker not in snoopy_wiki:
            surplus_tickers.append(ticker)
    missing_tickers = []
    for ticker in snoopy_wiki:
        if ticker not in snoopy_pytickersymbols:
            missing_tickers.append(ticker)
    print('surplus snoopy tickers:')
    print(surplus_tickers)
    print('missing snoopy tickers:')
    print(missing_tickers)

    dji_wiki = WikiScanner.get_index_tickers(StockMarketIndex.DJI, data_source='wiki')
    dji_pytickersymbols = WikiScanner.get_index_tickers(StockMarketIndex.DJI, data_source='pyticker')
    surplus_tickers = []
    for ticker in dji_pytickersymbols:
        if ticker not in dji_wiki:
            surplus_tickers.append(ticker)
    missing_tickers = []
    for ticker in dji_wiki:
        if ticker not in dji_pytickersymbols:
            missing_tickers.append(ticker)
    print('surplus DJI tickers:')
    print(surplus_tickers)
    print('missing DJI tickers:')
    print(missing_tickers)
    pass
