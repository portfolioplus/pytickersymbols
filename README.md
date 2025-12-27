![Release Build](https://github.com/portfolioplus/pytickersymbols/workflows/Release%20Build/badge.svg)
![PyPI - Downloads](https://img.shields.io/pypi/dm/pytickersymbols?style=plastic)
[![Coverage Status](https://coveralls.io/repos/github/portfolioplus/pytickersymbols/badge.svg?branch=master)](https://coveralls.io/github/portfolioplus/pytickersymbols?branch=master)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/1385a87f773d47bc84336275a0182619)](https://www.codacy.com/gh/portfolioplus/pytickersymbols/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=portfolioplus/pytickersymbols&amp;utm_campaign=Badge_Grade)

# pytickersymbols

pytickersymbols provides access to google and yahoo ticker symbols for all stocks of the following indices:

- [x] AEX
- [x] BEL 20
- [x] CAC 40
- [x] CAC MID 60
- [x] DAX
- [x] DOW JONES
- [x] EURO STOXX 50
- [x] FTSE 100
- [x] IBEX 35
- [x] MDAX
- [x] NASDAQ 100
- [x] OMX Helsinki 25
- [x] OMX Stockholm 30
- [x] S&P 100
- [x] S&P 500
- [x] S&P 600
- [x] SDAX
- [x] Switzerland 20
- [x] TECDAX
## install

```shell
pip3 install pytickersymbols
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

## Development

### Setting up the development environment

This project uses Poetry for dependency management. To set up your development environment:

```shell
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Clone the repository
git clone https://github.com/portfolioplus/pytickersymbols.git
cd pytickersymbols

# Install dependencies (including dev dependencies)
poetry install

# Activate the virtual environment
poetry shell
```

### Development Tools

The `tools/` directory contains scripts for managing stock index data:

- **sync_indices.py**: Split/merge stock data between monolithic and per-index formats
- **wiki_table_parser.py**: Parse Wikipedia tables for stock index data
- **yaml2data.py**: Convert YAML data to Python data module

See [tools/README.md](tools/README.md) for detailed usage instructions.

### Running Tests

```shell
poetry run pytest
```

### Adding a New Index

To add a new stock index to the library:

1. **Add the index to configuration**  
   Edit [tools/index_sources.yaml](tools/index_sources.yaml) and add a new entry:

   ```yaml
   - name: NIKKEI 225
     source:
       type: wikipedia
       url: https://en.wikipedia.org/wiki/Nikkei_225
       table_title_regex: "Components"
       extract_company_info: true
       language_fallbacks: ["ja", "en"]
       columns:
         name: ["Company", "Name"]
         symbol: ["Ticker", "Symbol"]
         isin: ["ISIN"]
         sector: ["Sector", "Industry"]
       symbol_converter:
         - pattern: "^(.+)$"
           format: "{1}.T"  # Add .T suffix for Tokyo Stock Exchange
     match:
       by: symbol
   ```

   **Configuration options:**
   - `name`: Display name (must match stocks.yaml if merging with historical data)
   - `url`: Wikipedia page URL containing the index constituents table
   - `table_title_regex`: (Optional) Regex to match the table title
   - `extract_company_info`: Set to `true` to fetch additional details from company Wikipedia pages
   - `language_fallbacks`: List of Wikipedia language codes to try for ISIN lookup
   - `symbol_converter`: Rules to convert Wikipedia symbols to Yahoo Finance format
   - `columns`: Map Wikipedia table headers to data fields
   - `match.by`: Field to use for matching with historical data (`symbol`, `isin`, or `name`)

2. **Run the build pipeline**  
   This will parse Wikipedia, enrich the data, and generate the Python module:

   ```shell
   cd tools
   python build_indices.py
   ```

   This creates:
   - `indices_raw/<index_name>.json` - Raw parsed data from Wikipedia
   - `indices/<index_name>.yaml` - Enriched data merged with historical records
   - Updates `src/pytickersymbols/indices_data.py` - Generated Python module

3. **Test the new index**  
   Verify the index is accessible:

   ```python
   from pytickersymbols import PyTickerSymbols
   
   stock_data = PyTickerSymbols()
   nikkei_stocks = stock_data.get_stocks_by_index('NIKKEI 225')
   print(list(nikkei_stocks))
   ```

4. **Run tests**  
   Ensure everything works:

   ```shell
   poetry run pytest
   ```

5. **Update the index list**  
   Add a checkbox entry to the supported indices list at the top of this README.

**Note:** The build pipeline automatically runs weekly via GitHub Actions to keep index data up to date.

## issue tracker

https://github.com/portfolioplus/pytickersymbols/issues

