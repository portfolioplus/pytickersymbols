# PyTickerSymbols Tools

Development tools for building and managing stock index data.

## Build Pipeline

The automated pipeline consists of three steps:

1. **Parse Wikipedia** - Extract index data from Wikipedia tables
2. **Enrich** - Merge with `stocks.yaml` historical data
3. **Generate** - Create `src/pytickersymbols/indices_data.py`

### Running the Build

```bash
cd tools
python build_indices.py
```

### GitHub Actions

Automated builds run:
- On push to main/master
- Weekly on Sundays at 2 AM UTC
- Manually via workflow dispatch

## Configuration

### index_sources.yaml

Single source of truth for all indices.

**Adding a new index:**

```yaml
- name: My Index
  source:
    type: wikipedia
    url: https://en.wikipedia.org/wiki/My_Index
    table_title_regex: "Components"
    extract_company_info: true
    language_fallbacks: ["de", "fr"]
    symbol_converter:
      - pattern: "^(.+?)(?:\\.XX)?$"
        format: "{1}.XX"
    columns:
      name: ["Company", "Name"]
      symbol: ["Ticker", "Symbol"]
      isin: ["ISIN"]
      sector: ["Sector"]
  match:
    by: symbol
```

**Symbol converters** - Convert Wikipedia symbols to Yahoo Finance format:

```yaml
symbol_converter:
  - pattern: "Euronext Brussels:(.+)"
    format: "{1}.BR"
  - pattern: "^(.+?)(?:\\.DE)?$"  # Strip existing suffix
    format: "{1}.DE"
```

**Language fallbacks** - Try multiple Wikipedia languages for ISIN detection:

```yaml
language_fallbacks: ["de", "fr", "es"]
```

## Scripts

### build_indices.py
Main build orchestrator. Runs all three pipeline steps.

### wiki_table_parser.py
Parses Wikipedia tables, extracts company data, follows language links for ISINs.

### enrich_indices.py
Merges Wikipedia data with stocks.yaml, logs new/removed companies.

### config.py
Loads global configuration from index_sources.yaml.

### enrich_with_yfinance.py
Optional: enriches data with Yahoo Finance API (not used in main pipeline).

## Build Artifacts

**Not committed to git:**
- `indices_raw/` - Raw JSON from Wikipedia
- `indices/` - Enriched YAML files

**Committed:**
- `src/pytickersymbols/indices_data.py` - Generated Python module

## Dependencies

```bash
pip install beautifulsoup4 requests pyyaml click
```
