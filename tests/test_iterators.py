#!/usr/bin/env python
# -*- coding: utf-8 -*-
import itertools
from typing import List

import pytest

from pytickersymbols import PyTickerSymbols


def test_iter_all_indices_consistency():
    s = PyTickerSymbols()
    iter_indices = list(s.iter_all_indices())
    list_indices = s.get_all_indices()
    assert set(iter_indices) == set(list_indices)
    assert len(iter_indices) == len(list_indices)


def test_iter_all_stocks_consistency():
    s = PyTickerSymbols()
    names_iter = sorted([c.get('name') for c in s.iter_all_stocks() if c.get('name')])
    names_list = sorted([c.get('name') for c in s.get_all_stocks() if c.get('name')])
    assert names_iter == names_list


def test_iter_all_industries_consistency():
    s = PyTickerSymbols()
    iter_inds = set(s.iter_all_industries())
    list_inds = set(s.get_all_industries())
    assert iter_inds == list_inds


def test_iter_all_countries_consistency():
    s = PyTickerSymbols()
    iter_countries = set(s.iter_all_countries())
    list_countries = set(s.get_all_countries())
    assert iter_countries == list_countries


def _first_available_index(s: PyTickerSymbols) -> str | None:
    indices = s.get_all_indices()
    if not indices:
        return None
    # Prefer DAX if present for stable expectations
    return 'DAX' if 'DAX' in indices else indices[0]


def test_iter_yahoo_tickers_by_index_consistency():
    s = PyTickerSymbols()
    index = _first_available_index(s)
    if not index:
        pytest.skip('No indices available')
    list_tickers_nested: List[List[str]] = s.get_yahoo_ticker_symbols_by_index(index)
    iter_tickers_nested: List[List[str]] = list(s.iter_yahoo_ticker_symbols_by_index(index))
    assert len(list_tickers_nested) == len(iter_tickers_nested)
    # Flatten for robust comparison
    list_flat = list(itertools.chain.from_iterable(list_tickers_nested))
    iter_flat = list(itertools.chain.from_iterable(iter_tickers_nested))
    assert sorted(list_flat) == sorted(iter_flat)


def test_iter_google_tickers_by_index_consistency():
    s = PyTickerSymbols()
    index = _first_available_index(s)
    if not index:
        pytest.skip('No indices available')
    list_tickers_nested: List[List[str]] = s.get_google_ticker_symbols_by_index(index)
    iter_tickers_nested: List[List[str]] = list(s.iter_google_ticker_symbols_by_index(index))
    assert len(list_tickers_nested) == len(iter_tickers_nested)
    list_flat = list(itertools.chain.from_iterable(list_tickers_nested))
    iter_flat = list(itertools.chain.from_iterable(iter_tickers_nested))
    assert sorted(list_flat) == sorted(iter_flat)


def test_iter_vs_list_exchange_filtered_tickers():
    s = PyTickerSymbols()
    index = _first_available_index(s)
    if not index:
        pytest.skip('No indices available')
    exchanges = ('FRA:', 'NASDAQ:', 'NYSE:', 'OTCMKTS:')
    for tickertype in ('yahoo', 'google'):
        list_res = s._get_tickers_by_index(index, exchanges, tickertype)
        iter_res = list(s._iter_tickers_by_index(index, exchanges, tickertype))
        assert sorted(list_res) == sorted(iter_res)
