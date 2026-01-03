#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyTest benchmarks using pytest-benchmark.
These tests record performance and will appear in pytest-benchmark output.
"""
import json
import pytest

from pytickersymbols import PyTickerSymbols


def _pick_known_symbol(s: PyTickerSymbols):
    indices = s.get_all_indices()
    index = 'DAX' if 'DAX' in indices else (indices[0] if indices else None)
    if not index:
        return None
    for company in s.get_stocks_by_index(index):
        for sym in company.get('symbols', []) or []:
            y = sym.get('yahoo')
            if y and y != '-':
                return y
    return None


def test_benchmark_cached_lookup(benchmark):
    s = PyTickerSymbols()
    symbol = _pick_known_symbol(s)
    if not symbol:
        pytest.skip('No suitable yahoo symbol found')

    # Measure cached path
    benchmark(lambda: s.get_stock_by_yahoo_symbol(symbol))


def test_benchmark_naive_lookup(benchmark):
    s = PyTickerSymbols()
    symbol = _pick_known_symbol(s)
    if not symbol:
        pytest.skip('No suitable yahoo symbol found')

    def naive():
        for company in s.get_all_stocks():
            for sm in company.get('symbols', []) or []:
                if sm.get('yahoo') == symbol:
                    return company
        return None

    benchmark(naive)


def test_benchmark_after_load_json_reindex(benchmark, tmp_path):
    data = {
        "tiny": {
            "name": "tiny",
            "companies": [
                {
                    "name": "Tiny Co",
                    "symbols": [{"yahoo": "TINY.F", "google": "FRA:TINY"}],
                    "country": "Germany",
                    "industries": ["Software"],
                }
            ],
        }
    }
    p = tmp_path / "tiny.json"
    p.write_text(json.dumps(data))

    s = PyTickerSymbols()
    s.load_json(str(p))

    # Benchmark cached lookups post-reindex
    benchmark(lambda: s.get_stock_by_yahoo_symbol("TINY.F"))
