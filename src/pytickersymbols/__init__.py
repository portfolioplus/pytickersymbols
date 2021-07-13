#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" pytickersymbols
  Copyright 2019 Slash Gordon
  Use of this source code is governed by an MIT-style license that
  can be found in the LICENSE file.
"""
import os
import json
import yaml
from weakref import WeakValueDictionary

__version__ = "1.7.7"


class Singleton(type):
    _instances = WeakValueDictionary()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super(Singleton, cls).__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class PyTickerSymbols(metaclass=Singleton):
    def __init__(self, stocks_path=''):
        self.__stocks = None
        if not stocks_path:
            json_path = os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                'data',
                'stocks.json',
            )
            with open(json_path, errors='replace') as stocks:
                self.__stocks = json.load(stocks)
        else:
            if stocks_path.lower().endswith(
                '.yaml'
            ) or stocks_path.lower().endswith('.yml'):
                self.load_yaml(stocks_path)
            elif stocks_path.lower().endswith('.json'):
                self.load_json(stocks_path)
            else:
                raise NotImplementedError(
                    f'File {stocks_path} is not supported.'
                    'File should be end with yaml, yml or json.'
                )

    def load_json(self, path):
        """
        Loads external json stock file
        """
        with open(path) as stocks:
            self.__stocks = json.load(stocks)

    def load_yaml(self, path):
        """
        Loads external yaml stock file
        """
        with open(path) as stocks:
            self.__stocks = yaml.safe_load(stocks)

    def get_all_indices(self):
        """
        Returns all available indices
        :return: list of index names
        """
        return self.__get_sub_items('indices')

    def get_all_stocks(self):
        """
        Returns all available stocks
        :return: list of index stock objects
        """
        return self.__stocks['companies']

    def get_stock_name_by_yahoo_symbol(self, symbol):
        """
        Returns stock name by yahoo symbol
        :return: stock name or None if symbol is not present
        """
        stock = self.get_stock_by_yahoo_symbol(symbol)
        return stock['name'] if stock else None

    def get_stock_name_by_google_symbol(self, symbol):
        """
        Returns stock name by google symbol
        :return: stock name or None if symbol is not present
        """
        stock = self.get_stock_by_google_symbol(symbol)
        return stock['name'] if stock else None

    def get_stock_by_yahoo_symbol(self, symbol):
        """
        Returns stock by yahoo symbol
        :return: stock or None if symbol is not present
        """
        return self.__get_stock_by_symbol(symbol, 'yahoo')

    def get_stock_by_google_symbol(self, symbol):
        """
        Returns stock by google symbol
        :return: stock or None if symbol is not present
        """
        return self.__get_stock_by_symbol(symbol, 'google')

    def __get_stock_by_symbol(self, symbol, symbol_type):
        """
        Returns stock name by symbol
        :return: stock name or None if symbol is not present
        """
        return next(
            filter(
                lambda x, sym=symbol: sym
                in map(
                    lambda y, sym_type=symbol_type: y[sym_type], x['symbols']
                ),
                self.get_all_stocks(),
            ),
            None
        )

    def get_all_industries(self):
        """
        Returns all available industries
        :return: list of industries
        """
        return self.__get_sub_items('industries')

    def get_all_countries(self):
        """
        Returns all available countries
        :return: list of country names
        """
        countries = list(
            set(
                map(lambda stock: stock['country'], self.__stocks['companies'])
            )
        )
        return countries

    def get_stocks_by_index(self, index):
        """
        Returns a list with stocks who belongs to given index.
        :param index: name of index
        :return: list of stocks
        """
        return self.__get_items('indices', index)

    def get_yahoo_ticker_symbols_by_index(self, index):
        """
        Returns a list with yahoo ticker symbols who belongs to given index.
        :param index: name of index
        :return: list of yahoo ticker symbols
        """
        my_items = self.__get_items('indices', index)
        return self.__filter_data(my_items, False, True)

    def get_google_ticker_symbols_by_index(self, index):
        """
        Returns a list with google ticker symbols who belongs to given index.
        :param index: name of index
        :return: list of google ticker symbols
        """
        my_items = self.__get_items('indices', index)
        return self.__filter_data(my_items, True, False)

    def get_stocks_by_industry(self, industry):
        """
        Returns a list with stocks who belongs to given index.
        :param industry: name of index
        :return: list of stocks
        """
        return self.__get_items('industries', industry)

    def get_stocks_by_country(self, country):
        """
        Returns a list with stocks who belongs to given country.
        :param country: name of country
        :return: list of stocks
        """
        return filter(
            lambda stock: isinstance(country, str)
            and stock['country'].lower() == country.lower(),
            self.__stocks['companies'],
        )

    def index_to_yahoo_symbol(self, index_name):
        """
        Returns the yahoo symbol for index name.
        :param country: name of index
        :return: yahoo symbol
        """
        yahoo_symbol = None
        for index_item in self.__stocks['indices']:
            if index_item['name'] == index_name:
                yahoo_symbol = index_item['yahoo']
                break
        return yahoo_symbol

    def __get_items(self, key, val):
        stocks = filter(
            lambda item: len(
                list(
                    filter(
                        lambda sub_item: isinstance(val, str)
                        and val.lower() == sub_item.lower(),
                        item[key],
                    )
                )
            )
            > 0,
            self.__stocks['companies'],
        )
        return stocks

    def __get_sub_items(self, key):
        sub_items = list(
            set(
                [
                    item
                    for stock in self.__stocks['companies']
                    for item in stock[key]
                ]
            )
        )
        return sub_items

    @staticmethod
    def __filter_data(stocks, google, yahoo):
        ticker_list = []
        for stock in stocks:
            sub_list = []
            for symbol in stock['symbols']:
                if google and 'google' in symbol and symbol['google'] != '-':
                    sub_list.append(symbol['google'])
                if yahoo and 'yahoo' in symbol and symbol['yahoo'] != '-':
                    sub_list.append(symbol['yahoo'])
            ticker_list.append(sub_list)
        return ticker_list


class Statics:
    class Indices:
        DE_SDAX = 'SDAX'
        RU_MOEX = 'MOEX'
        GB_FTSE = 'FTSE 100'
        FI_OMX_25 = 'OMX Helsinki 25'
        EU_50 = 'EURO STOXX 50'
        US_SP_100 = 'S&P 100'
        ES_IBEX_35 = 'IBEX 35'
        US_DOW = 'DOW JONES'
        DE_DAX = 'DAX'
        FR_CAC_60 = 'CAC Mid 60'
        DE_TECDAX = 'TECDAX'
        US_NASDAQ = 'NASDAQ 100'
        CH_20 = 'Switzerland 20'
        FR_CAC_40 = 'CAC 40'
        US_SP_500 = 'S&P 500'
        SE_OMX_30 = 'OMX Stockholm 30'
        BE_20 = 'BEL 20'
        DE_MDAX = 'MDAX'
        NL_AEX = 'AEX'
