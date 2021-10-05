![Release Build](https://github.com/portfolioplus/pytickersymbols/workflows/Release%20Build/badge.svg)
![PyPI - Downloads](https://img.shields.io/pypi/dm/pytickersymbols?style=plastic)
[![Coverage Status](https://coveralls.io/repos/github/portfolioplus/pytickersymbols/badge.svg?branch=master)](https://coveralls.io/github/portfolioplus/pytickersymbols?branch=master)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/1385a87f773d47bc84336275a0182619)](https://www.codacy.com/gh/portfolioplus/pytickersymbols/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=portfolioplus/pytickersymbols&amp;utm_campaign=Badge_Grade)

# pytickersymbols

pytickersymbols provides access to google and yahoo ticker symbols for all stocks of the following indices:

- [x] AEX
- [x] BEL 20
- [x] CAC 40
- [x] DAX
- [x] DOW JONES
- [x] FTSE 100
- [x] IBEX 35
- [x] MDAX
- [x] NASDAQ 100
- [x] OMX Helsinki 15
- [x] OMX Helsinki 25
- [x] OMX Stockholm 30
- [x] S&P 100
- [x] S&P 500
- [x] SDAX
- [x] SMI
- [x] TECDAX
- [x] MOEX
## install


```shell
pip install pytickersymbols
```

## quick start

Get all countries, indices and industries as follows:

```python
from pytickersymbols import PyTickerSymbols

stock_data = PyTickerSymbols()
countries = stock_data.get_all_countries()
indices = stock_data.get_all_indices()
industries = stock_data.get_all_industries()
```

You can select all stocks of an index as follows:

```python
from pytickersymbols import PyTickerSymbols

stock_data = PyTickerSymbols()
german_stocks = stock_data.get_stocks_by_index('DAX')
uk_stocks = stock_data.get_stocks_by_index('FTSE 100')

print(list(uk_stocks))

```

If you are only interested in ticker symbols, then you should have a look at the following lines:

```python
from pytickersymbols import PyTickerSymbols

stock_data = PyTickerSymbols()
# the naming conversation is get_{index_name}_{exchange_city}_{yahoo or google}_tickers
dax_google = stock_data.get_dax_frankfurt_google_tickers()
dax_yahoo = stock_data.get_dax_frankfurt_yahoo_tickers()
sp100_yahoo = stock_data.get_sp_100_nyc_yahoo_tickers()
sp500_google = stock_data.get_sp_500_nyc_google_tickers()
dow_yahoo = stock_data.get_dow_jones_nyc_yahoo_tickers()
# there are too many combination. Here is a complete list of all getters
all_ticker_getter_names = list(filter(
   lambda x: (
         x.endswith('_google_tickers') or x.endswith('_yahoo_tickers')
   ),
   dir(stock_data),
))
print(all_ticker_getter_names)
```

## issue tracker

https://github.com/portfolioplus/pytickersymbols/issues

