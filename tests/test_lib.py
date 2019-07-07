#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" pytickersymbols

 Copyright 2019 Christoph Dieck

 Use of this source code is governed by a GNU General Public License v3 or later that can be
 found in the LICENSE file.
"""
import unittest
import pandas_datareader as pdr

from pytickersymbols import PyTickerSymbols


class TestLib(unittest.TestCase):

    def test_index(self):
        """
        Test index getter
        :return:
        """
        stock_data = PyTickerSymbols()
        assert stock_data
        indices = stock_data.get_all_indices()
        assert indices
        assert "DAX" in indices
        assert "SDAX" in indices
        assert "MDAX" in indices
        # duplicates are not allowed
        for index in indices:
            assert len([index_tmp for index_tmp in indices if index_tmp == index]) == 1

    def test_country(self):
        """
        Test country getter
        :return:
        """
        stock_data = PyTickerSymbols()
        assert stock_data
        countries = stock_data.get_all_countries()
        assert countries
        assert "Germany" in countries
        assert "Netherlands" in countries
        assert "Sweden" in countries
        # duplicates are not allowed
        for country in countries:
            assert (
                len(
                    [country_tmp for country_tmp in countries if country_tmp == country]
                )
                == 1
            )

    def test_industry(self):
        """
        Test industry getter
        :return:
        """
        stock_data = PyTickerSymbols()
        assert stock_data
        industries = stock_data.get_all_industries()
        assert industries
        assert "Computer Hardware" in industries
        assert "Gold" in industries
        assert "Banking Services" in industries
        # duplicates are not allowed
        for industry in industries:
            assert (
                len([tmp_item for tmp_item in industries if tmp_item == industry]) == 1
            )

    def test_stocks_by_index(self):
        """
        Tests stock getter
        :return:
        """
        stock_data = PyTickerSymbols()
        assert stock_data
        stocks = stock_data.get_stocks_by_index(None)
        assert len(stocks) == 0
        stocks = stock_data.get_stocks_by_index(False)
        assert len(stocks) == 0
        stocks = stock_data.get_stocks_by_index(True)
        assert len(stocks) == 0
        stocks = stock_data.get_stocks_by_index(22)
        assert len(stocks) == 0
        stocks = stock_data.get_stocks_by_index("DAX")
        assert stocks
        assert len(stocks) == 30
        for stock in stocks:
            is_in_dax = False
            for index in stock["indices"]:
                if "DAX" in index:
                    is_in_dax = True
            assert is_in_dax

    def test_stocks_by_country(self):
        """
        Tests stock getter by country
        :return:
        """
        stock_data = PyTickerSymbols()
        assert stock_data
        stocks = stock_data.get_stocks_by_country(None)
        assert len(stocks) == 0
        stocks = stock_data.get_stocks_by_country(False)
        assert len(stocks) == 0
        stocks = stock_data.get_stocks_by_country(True)
        assert len(stocks) == 0
        stocks = stock_data.get_stocks_by_country(22)
        assert len(stocks) == 0
        stocks = stock_data.get_stocks_by_country("Israel")
        assert stocks
        assert len(stocks) >= 1
        for stock in stocks:
            is_in_israel = False
            if "Israel" == stock["country"]:
                is_in_israel = True
            assert is_in_israel

    def test_stocks_by_industry(self):
        """
        Tests stock getter by industry
        :return:
        """
        stock_data = PyTickerSymbols()
        assert stock_data
        stocks = stock_data.get_stocks_by_industry(None)
        assert len(stocks) == 0
        stocks = stock_data.get_stocks_by_industry(False)
        assert len(stocks) == 0
        stocks = stock_data.get_stocks_by_industry(True)
        assert len(stocks) == 0
        stocks = stock_data.get_stocks_by_industry(22)
        assert len(stocks) == 0
        stocks = stock_data.get_stocks_by_industry("Basic Materials")
        assert stocks
        for stock in stocks:
            is_in_basic = False
            for industry in stock["industries"]:
                if "Basic Materials" in industry:
                    is_in_basic = True
            assert is_in_basic

    def test_tickers_by_index(self):
        """
        Tests tickers getter by index
        :return:
        """
        stock_data = PyTickerSymbols()
        assert stock_data
        google_tickers = stock_data.get_google_ticker_symbols_by_index(None)
        assert len(google_tickers) == 0
        google_tickers = stock_data.get_google_ticker_symbols_by_index(False)
        assert len(google_tickers) == 0
        google_tickers = stock_data.get_google_ticker_symbols_by_index(True)
        assert len(google_tickers) == 0
        google_tickers = stock_data.get_google_ticker_symbols_by_index(22)
        assert len(google_tickers) == 0
        google_tickers = stock_data.get_google_ticker_symbols_by_index("DAX")
        assert google_tickers
        yahoo_tickers = stock_data.get_yahoo_ticker_symbols_by_index(None)
        assert len(yahoo_tickers) == 0
        yahoo_tickers = stock_data.get_yahoo_ticker_symbols_by_index(False)
        assert len(yahoo_tickers) == 0
        yahoo_tickers = stock_data.get_yahoo_ticker_symbols_by_index(True)
        assert len(yahoo_tickers) == 0
        yahoo_tickers = stock_data.get_yahoo_ticker_symbols_by_index(22)
        assert len(yahoo_tickers) == 0
        yahoo_tickers = stock_data.get_yahoo_ticker_symbols_by_index("DAX")
        assert yahoo_tickers
        test_list = [google_tickers, yahoo_tickers]
        for test_item in test_list:
            assert len(test_item) == 30
            for tickers in test_item:
                assert len(tickers) == 2

    def test_tickers_valid(self):
        """
        Test if each ticker symbol works with pandas datareader
        """
        stock_data = PyTickerSymbols()
        assert stock_data
        y_tickers = stock_data.get_yahoo_ticker_symbols_by_index("DAX")
        for tickers in y_tickers:
            for ticker in tickers:
                yahoo = pdr.get_data_yahoo(
                    ticker, "2019-07-01", "2019-07-05", interval="d"
                )
                assert yahoo is not None
                assert "Close" in yahoo
                assert len(yahoo["Close"]) > 0
    
    def test_index_to_yahoo(self):
        stock_data = PyTickerSymbols()
        assert stock_data
        assert '^GDAXI' == stock_data.index_to_yahoo_symbol('DAX')
        assert '^SDAXI' ==  stock_data.index_to_yahoo_symbol('SDAX')
        assert '^MDAXI' == stock_data.index_to_yahoo_symbol('MDAX')
        assert '^SSMI' == stock_data.index_to_yahoo_symbol('Switzerland 20')

if __name__ == "__main__":
    unittest.main()
