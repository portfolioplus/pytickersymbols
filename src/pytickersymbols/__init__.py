#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyTickerSymbols - Access to Google and Yahoo ticker symbols for stock indices.

Copyright 2019 Slash Gordon
Use of this source code is governed by an MIT-style license that
can be found in the LICENSE file.
"""
import json
from weakref import WeakValueDictionary
import itertools
from typing import Any, Dict, Iterable, Iterator, List, Optional
from pytickersymbols.indices_data import INDICES

__version__ = "1.17.7"


class Statics:
    class Indices:
        DE_SDAX = 'SDAX'
        GB_FTSE = 'FTSE 100'
        FI_OMX_25 = 'OMX Helsinki 25'
        EU_50 = 'EURO STOXX 50'
        US_SP_100 = 'S&P 100'
        ES_IBEX_35 = 'IBEX 35'
        US_DOW = 'DOW JONES'
        DE_DAX = 'DAX'
        FR_CAC_60 = 'CAC Mid 60'
        DE_TECDAX = 'TecDAX'
        US_NASDAQ = 'NASDAQ 100'
        CH_20 = 'Switzerland 20'
        FR_CAC_40 = 'CAC_40'
        US_SP_500 = 'S&P 500'
        US_SP_600 = 'S&P 600'
        SE_OMX_30 = 'OMX Stockholm 30'
        BE_20 = 'BEL 20'
        DE_MDAX = 'MDAX'
        NL_AEX = 'AEX'
        JP_NIKKEI_225 = 'NIKKEI 225'

    class Exchanges:
        LONDON = ('LON:')
        FRANKFURT = ('FRA:')
        MOSCOW = ('MCX:')
        NYC = ('NASDAQ:', 'NYSE:', 'OTCMKTS:')


class Singleton(type):
    _instances = WeakValueDictionary()

    @staticmethod
    def create_index(myvars):
        return map(
            lambda x: (
                myvars[x],
                myvars[x].lower().replace(' ', '_').replace('&', ''),
            ),
            filter(lambda x: not x.startswith('_'), myvars),
        )

    @staticmethod
    def create_ex(myvars):
        return map(
            lambda x: (
                myvars[x],
                x.lower(),
            ),
            filter(lambda x: not x.startswith('_'), myvars),
        )

    def __new__(cls, clsname, superclasses, attributedict):

        items = [
            list(Singleton.create_index(vars(Statics.Indices))),
            list(Singleton.create_ex(vars(Statics.Exchanges))),
            ('google', 'yahoo'),
        ]
        items_pro = list(itertools.product(*items))
        for item in items_pro:
            key = f'get_{item[0][1]}_{item[1][1]}_{item[2]}_tickers'

            def instance_method(self, a=item[0][0], b=item[1][0], c=item[2]):
                return attributedict['_get_tickers_by_index'](self, a, b, c)
            attributedict[key] = instance_method
        return type.__new__(cls, clsname, superclasses, attributedict)

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super(Singleton, cls).__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class PyTickerSymbols(metaclass=Singleton):
    def __init__(self) -> None:
        self.__indices: Dict[str, Dict[str, Any]] = INDICES
        # Cached derived data for performance
        self.__all_stocks_list: List[Dict[str, Any]] = []
        self.__symbol_index_yahoo: Dict[str, Dict[str, Any]] = {}
        self.__symbol_index_google: Dict[str, Dict[str, Any]] = {}
        self.__industries_set: set[str] = set()
        self.__countries_set: set[str] = set()
        self.__reindex()

    def load_json(self, path: str) -> None:
        """
        Loads external json stock file
        """
        with open(path) as stocks:
            self.__indices = json.load(stocks)
        self.__reindex()


    def load_yaml(self, path: str) -> None:
        """
        Loads external yaml stock file
        """
        try:
            import yaml
        except ImportError:
            raise ImportError("PyYAML is required to load YAML files. Please install it via 'pip install pyyaml'.")
        with open(path) as stocks:
            self.__indices = yaml.safe_load(stocks)
        self.__reindex()

    def __reindex(self) -> None:
        """
        Recompute cached views and symbol lookups from current indices.
        Improves performance by avoiding repeated scans.
        """
        # Build unique company list across all indices
        companies_dict: Dict[str, Dict[str, Any]] = {}
        industries: set[str] = set()
        countries: set[str] = set()
        yahoo_map: Dict[str, Dict[str, Any]] = {}
        google_map: Dict[str, Dict[str, Any]] = {}

        for index_data in self.__indices.values():
            for company in index_data.get('companies', []) or []:
                name = company.get('name')
                if name and name not in companies_dict:
                    companies_dict[name] = company
                # Collect industries
                for ind in company.get('industries', []) or []:
                    if ind:
                        industries.add(ind)
                # Collect countries
                country = company.get('country')
                if country:
                    countries.add(country)
                # Build symbol maps
                for sym in company.get('symbols', []) or []:
                    y = sym.get('yahoo')
                    if y and y != '-':
                        yahoo_map[y] = company
                    g = sym.get('google')
                    if g and g != '-':
                        google_map[g] = company

        # Stable sorted list of companies by name (case-insensitive)
        self.__all_stocks_list = sorted(
            companies_dict.values(), key=lambda c: (c.get('name') or '').lower()
        )
        self.__symbol_index_yahoo = yahoo_map
        self.__symbol_index_google = google_map
        self.__industries_set = industries
        self.__countries_set = countries

    def get_all_indices(self) -> List[str]:
        """
        Returns all available indices
        :return: list of index names
        """
        return list(self.__indices.keys())

    def iter_all_indices(self) -> Iterator[str]:
        """Generator yielding all available indices"""
        for name in self.__indices.keys():
            yield name

    def get_all_stocks(self) -> List[Dict[str, Any]]:
        """
        Returns all available stocks (unique companies across all indices)
        :return: list of index stock objects
        """
        return list(self.__all_stocks_list)

    def iter_all_stocks(self) -> Iterator[Dict[str, Any]]:
        """Generator yielding all available stocks (unique companies)"""
        for company in self.__all_stocks_list:
            yield company

    def get_stock_name_by_yahoo_symbol(self, symbol: str) -> Optional[str]:
        """
        Returns stock name by yahoo symbol
        :return: stock name or None if symbol is not present
        """
        stock = self.get_stock_by_yahoo_symbol(symbol)
        return stock['name'] if stock else None

    def get_stock_name_by_google_symbol(self, symbol: str) -> Optional[str]:
        """
        Returns stock name by google symbol
        :return: stock name or None if symbol is not present
        """
        stock = self.get_stock_by_google_symbol(symbol)
        return stock['name'] if stock else None

    def get_stock_by_yahoo_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Returns stock by yahoo symbol
        :return: stock or None if symbol is not present
        """
        return self.__get_stock_by_symbol(symbol, 'yahoo')

    def get_stock_by_google_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Returns stock by google symbol
        :return: stock or None if symbol is not present
        """
        return self.__get_stock_by_symbol(symbol, 'google')

    def __get_stock_by_symbol(self, symbol: str, symbol_type: str) -> Optional[Dict[str, Any]]:
        """
        Returns stock name by symbol
        :return: stock name or None if symbol is not present
        """
        if symbol_type == 'yahoo':
            return self.__symbol_index_yahoo.get(symbol)
        if symbol_type == 'google':
            return self.__symbol_index_google.get(symbol)
        return None

    def get_all_industries(self) -> List[str]:
        """
        Returns all available industries
        :return: list of industries
        """
        return list(self.__industries_set)

    def iter_all_industries(self) -> Iterator[str]:
        """Generator yielding all available industries"""
        for industry in self.__industries_set:
            yield industry

    def get_all_countries(self) -> List[str]:
        """
        Returns all available countries
        :return: list of country names
        """
        return list(self.__countries_set)

    def iter_all_countries(self) -> Iterator[str]:
        """Generator yielding all available countries"""
        for country in self.__countries_set:
            yield country

    def get_stocks_by_index(self, index: Optional[str]) -> Iterator[Dict[str, Any]]:
        """
        Returns a list with stocks who belongs to given index.
        :param index: name of index
        :return: list of stocks
        """
        if not isinstance(index, str):
            return iter([])
        index_data = self.__indices.get(index)
        if index_data:
            return iter(index_data.get('companies', []))
        return iter([])

    def _get_tickers_by_index(self, index: str, exchanges: Iterable[str], tickertype: str) -> List[str]:
        stocks = self.get_stocks_by_index(index)
        result = []
        for stock in stocks:
            for symbol in stock.get('symbols', []):
                google_symbol = symbol.get('google', '')
                for exchange in exchanges:
                    if google_symbol.startswith(exchange):
                        ticker = symbol.get(tickertype)
                        if ticker:
                            result.append(ticker)
        return result

    def _iter_tickers_by_index(self, index: str, exchanges: Iterable[str], tickertype: str) -> Iterator[str]:
        """Generator yielding tickers for given index and exchanges"""
        stocks = self.get_stocks_by_index(index)
        for stock in stocks:
            for symbol in stock.get('symbols', []):
                google_symbol = symbol.get('google', '')
                for exchange in exchanges:
                    if google_symbol.startswith(exchange):
                        ticker = symbol.get(tickertype)
                        if ticker:
                            yield ticker

    def get_yahoo_ticker_symbols_by_index(self, index: Optional[str]) -> List[List[str]]:
        """
        Returns a list with yahoo ticker symbols who belongs to given index.
        :param index: name of index
        :return: list of yahoo ticker symbols
        """
        my_items = self.get_stocks_by_index(index)
        return self.__filter_data(my_items, False, True)

    def iter_yahoo_ticker_symbols_by_index(self, index: Optional[str]) -> Iterator[List[str]]:
        """Generator yielding yahoo ticker symbols for given index"""
        my_items = self.get_stocks_by_index(index)
        return self.__filter_data_iter(my_items, False, True)

    def get_google_ticker_symbols_by_index(self, index: Optional[str]) -> List[List[str]]:
        """
        Returns a list with google ticker symbols who belongs to given index.
        :param index: name of index
        :return: list of google ticker symbols
        """
        my_items = self.get_stocks_by_index(index)
        return self.__filter_data(my_items, True, False)

    def iter_google_ticker_symbols_by_index(self, index: Optional[str]) -> Iterator[List[str]]:
        """Generator yielding google ticker symbols for given index"""
        my_items = self.get_stocks_by_index(index)
        return self.__filter_data_iter(my_items, True, False)

    def get_stocks_by_industry(self, industry: Optional[str]) -> Iterator[Dict[str, Any]]:
        """
        Returns a list with stocks who belongs to given industry.
        :param industry: name of industry
        :return: list of stocks
        """
        if not isinstance(industry, str):
            return iter([])
        
        seen = set()
        industry_lower = industry.lower()
        for index_data in self.__indices.values():
            for company in index_data.get('companies', []):
                company_name = company.get('name')
                if company_name not in seen and industry_lower in [ind.lower() for ind in company.get('industries', [])]:
                    seen.add(company_name)
                    yield company

    def iter_stocks_by_industry(self, industry: Optional[str]) -> Iterator[Dict[str, Any]]:
        """Generator yielding stocks for given industry"""
        return self.get_stocks_by_industry(industry)

    def get_stocks_by_country(self, country: Optional[str]) -> Iterator[Dict[str, Any]]:
        """
        Returns a list with stocks who belongs to given country.
        :param country: name of country
        :return: list of stocks
        """
        if not isinstance(country, str):
            return iter([])
        
        seen = set()
        country_lower = country.lower()
        for index_data in self.__indices.values():
            for company in index_data.get('companies', []):
                company_name = company.get('name')
                if company_name not in seen and company.get('country', '').lower() == country_lower:
                    seen.add(company_name)
                    yield company

    def iter_stocks_by_country(self, country: Optional[str]) -> Iterator[Dict[str, Any]]:
        """Generator yielding stocks for given country"""
        return self.get_stocks_by_country(country)

    def index_to_yahoo_symbol(self, index_name: str) -> Optional[str]:
        """
        Returns the yahoo symbol for index name.
        :param index_name: name of index
        :return: yahoo symbol
        """
        index_data = self.__indices.get(index_name)
        return index_data.get('yahoo') if index_data else None

    @staticmethod
    def __filter_data(stocks: Iterable[Dict[str, Any]], google: bool, yahoo: bool) -> List[List[str]]:
        ticker_list: List[List[str]] = []
        stocks_list = list(stocks)  # Convert iterator to list so it can be reused
        for stock in stocks_list:
            sub_list: List[str] = []
            for symbol in stock.get('symbols', []):
                if google and 'google' in symbol and symbol.get('google') and symbol['google'] != '-':
                    sub_list.append(symbol['google'])
                if yahoo and 'yahoo' in symbol and symbol.get('yahoo') and symbol['yahoo'] != '-':
                    sub_list.append(symbol['yahoo'])
            ticker_list.append(sub_list)
        return ticker_list

    @staticmethod
    def __filter_data_iter(stocks: Iterable[Dict[str, Any]], google: bool, yahoo: bool) -> Iterator[List[str]]:
        """Generator version of __filter_data"""
        for stock in stocks:
            sub_list: List[str] = []
            for symbol in stock.get('symbols', []):
                if google and 'google' in symbol and symbol.get('google') and symbol['google'] != '-':
                    sub_list.append(symbol['google'])
                if yahoo and 'yahoo' in symbol and symbol.get('yahoo') and symbol['yahoo'] != '-':
                    sub_list.append(symbol['yahoo'])
            yield sub_list
