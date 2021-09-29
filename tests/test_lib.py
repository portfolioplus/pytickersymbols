#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" pytickersymbols
  Copyright 2019 Slash Gordon
  Use of this source code is governed by an MIT-style license that
  can be found in the LICENSE file.
"""
import os
import unittest
import yfinance as yf
from functools import reduce

from pytickersymbols import PyTickerSymbols
import tempfile
import json
import yaml
import pytest
from collections import Counter
import pycountry

_test_json = b'''{
   "indices": [
      {
         "name": "test",
         "yahoo": "test"
      }
   ],
   "companies": [
      {
         "id": 1,
         "name": "adidas AG",
         "symbol": "ADS",
         "country": "Germany",
         "indices": [
            "test"
         ],
         "industries": [
            "Footwear"
         ],
         "symbols": [
            {
               "yahoo": "ADS.F",
               "google": "FRA:ADS"
            }
         ],
         "metadata": {
            "founded": 1949,
            "employees": 57016
         }
      }
    ]
}
'''


class TestLib(unittest.TestCase):
    def test_singleton(self):
        """
        Test singleton pattern
        :return:
        """
        self.assertTrue(PyTickerSymbols() is PyTickerSymbols())

    def tearDown(self):
        p = PyTickerSymbols()
        del p

    def test_load_json(self):
        with pytest.raises(NotImplementedError):
            PyTickerSymbols(stocks_path='test.dat')
        with tempfile.NamedTemporaryFile(suffix='.json') as temp:
            temp.write(_test_json)
            temp.flush()
            stocks = PyTickerSymbols(stocks_path=temp.name)
            indices = stocks.get_all_indices()
            self.assertEqual(len(indices), 1)
            self.assertIn('test', indices)
            stocks = list(stocks.get_stocks_by_index('test'))
            self.assertEqual(len(stocks), 1)
            self.assertIn('name', stocks[0])
            self.assertEqual('adidas AG', stocks[0].get('name', None))

    def test_load_yaml(self):
        for sufix_test in ['.yaml', '.yml']:
            with tempfile.NamedTemporaryFile(suffix=sufix_test) as temp:
                temp.write(
                    str.encode(
                        yaml.dump(json.loads(_test_json.decode('utf-8')))
                    )
                )
                temp.flush()
                stocks = PyTickerSymbols(stocks_path=temp.name)
                indices = stocks.get_all_indices()
                self.assertEqual(len(indices), 1)
                self.assertIn('test', indices)
                stocks = list(stocks.get_stocks_by_index('test'))
                self.assertEqual(len(stocks), 1)
                self.assertIn('name', stocks[0])
                self.assertEqual('adidas AG', stocks[0].get('name', None))

    def test_index(self):
        """
        Test index getter
        :return:
        """
        stock_data = PyTickerSymbols()
        self.assertIsNotNone(stock_data)
        indices = stock_data.get_all_indices()
        self.assertIsNotNone(indices)
        self.assertIn('DAX', indices)
        self.assertIn('SDAX', indices)
        self.assertIn('MDAX', indices)
        # duplicates are not allowed
        for index in indices:
            lenl = len([tmp for tmp in indices if tmp == index])
            self.assertEqual(lenl, 1)

    def test_all_stocks(self):
        """
        Test stocks getter
        :return:
        """
        stock_data = PyTickerSymbols()
        self.assertIsNotNone(stock_data)
        stocks = stock_data.get_all_stocks()
        self.assertTrue(len(stocks) > 900)

    def test_encoding(self):
        """
        Test country getter
        :return:
        """
        stock_data = PyTickerSymbols()
        self.assertIsNotNone(stock_data)
        stocks = list(stock_data.get_all_stocks())
        names_with_unicode_count = sum(
            [
                any(
                    word in item['name']
                    for word in ['ö', 'ä', 'ü', 'é', 'è', 'ë']
                )
                for item in stocks
            ]
        )
        self.assertTrue(
            names_with_unicode_count >= 20, names_with_unicode_count
        )

    def test_country(self):
        """
        Test country getter
        :return:
        """
        stock_data = PyTickerSymbols()
        self.assertIsNotNone(stock_data)
        countries = list(stock_data.get_all_countries())
        self.assertIsNotNone(countries)
        self.assertIn("Germany", countries)
        self.assertIn("Netherlands", countries)
        self.assertIn("Sweden", countries)
        # duplicates are not allowed
        for country in countries:
            lenl = len([tmp for tmp in countries if tmp == country])
            self.assertEqual(lenl, 1)

    def test_industry(self):
        """
        Test industry getter
        :return:
        """
        stock_data = PyTickerSymbols()
        self.assertIsNotNone(stock_data)
        industries = list(stock_data.get_all_industries())
        self.assertIsNotNone(industries)
        self.assertIn("Computer Hardware", industries)
        self.assertIn("Gold", industries)
        self.assertIn("Banking Services", industries)
        # duplicates are not allowed
        for industry in industries:
            lenl = len([tmp for tmp in industries if tmp == industry])
            self.assertEqual(lenl, 1)

    def test_stocks_by_index(self):
        """
        Tests stock getter
        :return:
        """
        stock_data = PyTickerSymbols()
        self.assertIsNotNone(stock_data)
        stocks = list(stock_data.get_stocks_by_index(None))
        self.assertEqual(len(stocks), 0)
        stocks = list(stock_data.get_stocks_by_index(False))
        self.assertEqual(len(stocks), 0)
        stocks = list(stock_data.get_stocks_by_index(True))
        self.assertEqual(len(stocks), 0)
        stocks = list(stock_data.get_stocks_by_index(22))
        self.assertEqual(len(stocks), 0)
        for ind, ctx in [('DAX', 40), ('CAC 40', 40), ('DOW JONES', 30)]:
            stocks = list(stock_data.get_stocks_by_index(ind))
            self.assertIsNotNone(stocks)
            self.assertEqual(len(stocks), ctx)
            for stock in stocks:
                is_in = False
                for index in stock["indices"]:
                    if ind in index:
                        is_in = True
                self.assertTrue(is_in)
        # test NASDAQ 100
        stocks_nasdaq = list(stock_data.get_stocks_by_index('NASDAQ 100'))
        stocks_nasdaq_symbol = [
            sym['yahoo'] for stock in stocks_nasdaq for sym in stock['symbols']
        ]
        symbols_nasdaq = list(
            stock_data.get_yahoo_ticker_symbols_by_index('NASDAQ 100')
        )
        symbols_nasdaq = reduce(lambda x, y: x + y, symbols_nasdaq)
        self.assertEqual(len(stocks_nasdaq_symbol), len(symbols_nasdaq))
        self.assertIn('GOOGL', symbols_nasdaq)
        self.assertIn('GOOG', symbols_nasdaq)
        y_ticker = yf.Ticker('GOOG')
        data = y_ticker.history(period='4d')
        self.assertIsNotNone(data)
        y_ticker = yf.Ticker('GOOGL')
        data = y_ticker.history(period='4d')
        self.assertIsNotNone(data)

    def test_stocks_by_country(self):
        """
        Tests stock getter by country
        :return:
        """
        stock_data = PyTickerSymbols()
        self.assertIsNotNone(stock_data)
        stocks = list(stock_data.get_stocks_by_country(None))
        self.assertEqual(len(stocks), 0)
        stocks = list(stock_data.get_stocks_by_country(False))
        self.assertEqual(len(stocks), 0)
        stocks = list(stock_data.get_stocks_by_country(True))
        self.assertEqual(len(stocks), 0)
        stocks = list(stock_data.get_stocks_by_country(22))
        self.assertEqual(len(stocks), 0)
        stocks = list(stock_data.get_stocks_by_country("Israel"))
        self.assertIsNotNone(stocks)
        self.assertTrue(len(stocks) >= 1)
        for stock in stocks:
            is_in_israel = False
            if "Israel" == stock["country"]:
                is_in_israel = True
            self.assertTrue(is_in_israel)

    def test_stocks_by_industry(self):
        """
        Tests stock getter by industry
        :return:
        """
        stock_data = PyTickerSymbols()
        self.assertIsNotNone(stock_data)
        stocks = list(stock_data.get_stocks_by_industry(None))
        self.assertEqual(len(stocks), 0)
        stocks = list(stock_data.get_stocks_by_industry(False))
        self.assertEqual(len(stocks), 0)
        stocks = list(stock_data.get_stocks_by_industry(True))
        self.assertEqual(len(stocks), 0)
        stocks = list(stock_data.get_stocks_by_industry(22))
        self.assertEqual(len(stocks), 0)
        stocks = list(stock_data.get_stocks_by_industry("Basic Materials"))
        self.assertIsNotNone(stocks)
        for stock in stocks:
            is_in_basic = False
            for industry in stock["industries"]:
                if "Basic Materials" in industry:
                    is_in_basic = True
            self.assertTrue(is_in_basic)

    def test_stock_by_yahoo_symbol(self):
        """
        Tests stock getter by industry
        :return:
        """
        stock_data = PyTickerSymbols()
        self.assertIsNotNone(stock_data)
        ads = stock_data.get_stock_by_yahoo_symbol('ADS.F')
        self.assertIsNotNone(ads)
        self.assertEqual('adidas AG', ads['name'])
        unknown = stock_data.get_stock_by_yahoo_symbol('ADSdadsas.F')
        self.assertIsNone(unknown)

    def test_stock_name_by_yahoo_symbol(self):
        """
        Tests stock getter by industry
        :return:
        """
        stock_data = PyTickerSymbols()
        self.assertIsNotNone(stock_data)
        ads = stock_data.get_stock_name_by_yahoo_symbol('ADS.F')
        self.assertIsNotNone(ads)
        self.assertEqual('adidas AG', ads)
        unknown = stock_data.get_stock_by_yahoo_symbol('ADSdadsas.F')
        self.assertIsNone(unknown)

    def test_stock_by_google_symbol(self):
        """
        Tests stock getter by industry
        :return:
        """
        stock_data = PyTickerSymbols()
        self.assertIsNotNone(stock_data)
        ads = stock_data.get_stock_by_google_symbol('FRA:ADS')
        self.assertIsNotNone(ads)
        self.assertEqual('adidas AG', ads['name'])
        unknown = stock_data.get_stock_by_google_symbol('ADSdadsas.F')
        self.assertIsNone(unknown)

    def test_stock_name_by_google_symbol(self):
        """
        Tests stock getter by industry
        :return:
        """
        stock_data = PyTickerSymbols()
        self.assertIsNotNone(stock_data)
        ads = stock_data.get_stock_name_by_google_symbol('FRA:ADS')
        self.assertIsNotNone(ads)
        self.assertEqual('adidas AG', ads)
        unknown = stock_data.get_stock_by_google_symbol('ADSdadsas.F')
        self.assertIsNone(unknown)

    def test_tickers_by_index(self):
        """
        Tests tickers getter by index
        :return:
        """
        stock_data = PyTickerSymbols()
        self.assertIsNotNone(stock_data)
        google_tickers = stock_data.get_google_ticker_symbols_by_index(None)
        self.assertEqual(len(google_tickers), 0)
        google_tickers = stock_data.get_google_ticker_symbols_by_index(False)
        self.assertEqual(len(google_tickers), 0)
        google_tickers = stock_data.get_google_ticker_symbols_by_index(True)
        self.assertEqual(len(google_tickers), 0)
        google_tickers = stock_data.get_google_ticker_symbols_by_index(22)
        self.assertEqual(len(google_tickers), 0)
        google_tickers = stock_data.get_google_ticker_symbols_by_index("DAX")
        self.assertIsNotNone(google_tickers)
        yahoo_tickers = stock_data.get_yahoo_ticker_symbols_by_index(None)
        self.assertEqual(len(yahoo_tickers), 0)
        yahoo_tickers = stock_data.get_yahoo_ticker_symbols_by_index(False)
        self.assertEqual(len(yahoo_tickers), 0)
        yahoo_tickers = stock_data.get_yahoo_ticker_symbols_by_index(True)
        self.assertEqual(len(yahoo_tickers), 0)
        yahoo_tickers = stock_data.get_yahoo_ticker_symbols_by_index(22)
        self.assertEqual(len(yahoo_tickers), 0)
        yahoo_tickers = stock_data.get_yahoo_ticker_symbols_by_index("DAX")
        self.assertIsNotNone(yahoo_tickers)
        test_list = [google_tickers, yahoo_tickers]
        for test_item in test_list:
            self.assertEqual(len(test_item), 40)
            for tickers in test_item:
                self.assertTrue(len(tickers) >= 1, tickers)

    def test_tickers_valid(self):
        """
        Test if each ticker symbol works with yfiance
        """
        stock_data = PyTickerSymbols()
        self.assertIsNotNone(stock_data)
        y_tickers = stock_data.get_yahoo_ticker_symbols_by_index("DAX")
        for tickers in y_tickers:
            for ticker in tickers:
                y_ticker = yf.Ticker(ticker)
                data = y_ticker.history(period='4d')
                self.assertIsNotNone(data)
                self.assertIn("Close", data)

    def test_index_to_yahoo(self):
        stock_data = PyTickerSymbols()
        self.assertIsNotNone(stock_data)
        self.assertEqual('^GDAXI', stock_data.index_to_yahoo_symbol('DAX'))
        self.assertEqual('^SDAXI', stock_data.index_to_yahoo_symbol('SDAX'))
        self.assertEqual('^MDAXI', stock_data.index_to_yahoo_symbol('MDAX'))
        swi = stock_data.index_to_yahoo_symbol('Switzerland 20')
        self.assertEqual('^SSMI', swi)

    def test_unique_ticker_symbols(self):
        stock_data = PyTickerSymbols()
        ctx = Counter(
            [
                sym['yahoo']
                for stock in stock_data.get_all_stocks()
                for sym in stock['symbols']
            ]
        )
        msg = 'The following symbols appear several times:\n'
        msg += '\n'.join(
            map(lambda y: y[0], filter(lambda x: x[1] > 1, ctx.items()))
        )
        self.assertFalse(any(map(lambda x: x > 1, ctx.values())), msg)

    def test_valid_country_name(self):
        stock_data = PyTickerSymbols()
        countries = stock_data.get_all_countries()
        empty_names = list(filter(lambda x: not x, countries))
        empty_country_stocks = ', '.join(
            list(
                map(
                    lambda x: x['name'],
                    stock_data.get_stocks_by_country(''),
                )
            )
        )
        self.assertEqual(
            len(empty_names),
            0,
            'The following stocks have an empty country string: '
            + empty_country_stocks,
        )

        valid_countires = list(
            map(
                lambda x: x.name,
                pycountry.countries,
            )
        )
        wrong_country_name = list(
            filter(
                lambda x: x['country'] not in valid_countires,
                stock_data.get_all_stocks(),
            ),
        )
        wrong_country_name_stocks = ', '.join(
            list(
                map(
                    lambda x: x['name'] + '(' + x['country'] + ')',
                    wrong_country_name,
                )
            )
        )
        self.assertEqual(
            len(wrong_country_name),
            0,
            'The following stocks have an empty country string:'
            + wrong_country_name_stocks,
        )


if __name__ == "__main__":
    unittest.main()
