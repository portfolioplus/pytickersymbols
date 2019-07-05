[![Build Status](https://travis-ci.org/portfolioplus/pytickersymbols.svg?branch=master)](https://travis-ci.org/portfolioplus/pytickersymbols)
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

# quick start

Get all countries, indices and industries as follow:
```python
from pytickersymbols import PyTickerSymbols

stock_data = PyTickerSymbols()
countries = stock_data.get_all_countries()
indices = stock_data.get_all_indices()
industries = stock_data.get_all_industries()
```

You can select all stocks of an index as follow:
```python
from pytickersymbols import PyTickerSymbols

stock_data = PyTickerSymbols()
german_stocks = stock_data.get_stocks_by_index('DAX')
uk_stocks = stock_data.get_stocks_by_index('FTSE 100')

```

# issue tracker

[https://github.com/portfolioplus/pytickersymbols/issuese](https://github.com/portfolioplus/pytickersymbols/issues")
