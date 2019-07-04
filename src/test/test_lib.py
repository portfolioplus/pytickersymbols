#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" pystockdata

 Copyright 2019 Christoph Dieck

 Use of this source code is governed by a GNU General Public License v3 or later that can be
 found in the LICENSE file.
"""
import unittest

from pystockdata import PyStockData


class TestLib(unittest.TestCase):

    def test_index(self):
        """
        Test index getter
        :return:
        """
        stock_data = PyStockData()
        assert stock_data
        indices = stock_data.get_all_indices()
        assert indices
        assert 'DAX' in indices
        assert 'SDAX' in indices
        assert 'MDAX' in indices
        # duplicates are not allowed
        for index in indices:
            assert len([index_tmp for index_tmp in indices if index_tmp == index]) == 1

    def test_country(self):
        """
        Test country getter
        :return:
        """
        stock_data = PyStockData()
        assert stock_data
        countries = stock_data.get_all_countries()
        assert countries
        assert 'Germany' in countries
        assert 'Netherlands' in countries
        assert 'Sweden' in countries
        # duplicates are not allowed
        for country in countries:
            assert len([country_tmp for country_tmp in countries if country_tmp == country]) == 1

    def test_industry(self):
        """
        Test industry getter
        :return:
        """
        stock_data = PyStockData()
        assert stock_data
        industries = stock_data.get_all_industries()
        assert industries
        assert 'Computer Hardware' in industries
        assert 'Gold' in industries
        assert 'Banking Services' in industries
        # duplicates are not allowed
        for industry in industries:
            assert len([tmp_item for tmp_item in industries if tmp_item == industry]) == 1

    def test_stocks_by_index(self):
        """
        Tests stock getter
        :return:
        """
        stock_data = PyStockData()
        assert stock_data
        stocks = stock_data.get_stocks_by_index('DAX')
        assert stocks
        assert len(stocks) == 30
        for stock in stocks:
            is_in_dax = False
            for index in stock['indices']:
                if 'DAX' in index:
                    is_in_dax = True
            assert is_in_dax

    def test_stocks_by_country(self):
        """
        Tests stock getter by country
        :return:
        """
        stock_data = PyStockData()
        assert stock_data
        stocks = stock_data.get_stocks_by_country('Israel')
        assert stocks
        assert len(stocks) >= 1
        for stock in stocks:
            is_in_israel = False
            if 'Israel' == stock['country']:
                is_in_israel = True
            assert is_in_israel

    def test_stocks_by_industry(self):
        """
        Tests stock getter by industry
        :return:
        """
        stock_data = PyStockData()
        assert stock_data
        stocks = stock_data.get_stocks_by_industry('Basic Materials')
        assert stocks
        for stock in stocks:
            is_in_basic = False
            for industry in stock['industries']:
                if 'Basic Materials' in industry:
                    is_in_basic = True
            assert is_in_basic


if __name__ == '__main__':
    unittest.main()
