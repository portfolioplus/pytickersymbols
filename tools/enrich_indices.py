#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Enrich indices_raw JSON files with data from stocks.yaml and create YAML files in indices directory.

Copyright 2019 Slash Gordon
Use of this source code is governed by an MIT-style license that
can be found in the LICENSE file.
"""

import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any
from config import INDEX_MAPPING

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def load_stocks_yaml(yaml_path: Path) -> Dict[str, Any]:
    """Load stocks.yaml and create lookup dictionaries."""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # Create lookup by symbol, name, and ISIN
    companies = {}
    symbol_lookup = {}
    name_lookup = {}
    isin_lookup = {}
    
    for company in data.get('companies', []):
        company_name = company.get('name')
        symbol = company.get('symbol')
        isins = company.get('isins', [])
        
        if company_name:
            companies[company_name] = company
            name_lookup[company_name.lower()] = company
        
        if symbol:
            symbol_lookup[symbol] = company
            
        for isin in isins:
            isin_lookup[isin] = company
    
    return {
        'companies': companies,
        'symbol_lookup': symbol_lookup,
        'name_lookup': name_lookup,
        'isin_lookup': isin_lookup,
        'indices': {idx['name']: idx for idx in data.get('indices', [])}
    }


def normalize_name(name: str) -> str:
    """Normalize company name for matching."""
    # Remove common suffixes
    suffixes = [' AG', ' SE', ' N.V.', ' plc', ' Inc.', ' Corp.', ' Corporation', 
                ' Limited', ' Ltd.', ' GmbH', ' S.A.', ' NV', ' Oyj']
    normalized = name
    for suffix in suffixes:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)]
    return normalized.strip().lower()


def find_company_match(raw_company: Dict[str, Any], stocks_data: Dict) -> Dict[str, Any]:
    """Find matching company in stocks.yaml."""
    # Try exact name match first
    name = raw_company.get('name', '')
    if not name:
        return None
    
    # Exact match
    if name in stocks_data['companies']:
        return stocks_data['companies'][name]
    
    # Lowercase match
    name_lower = name.lower()
    if name_lower in stocks_data['name_lookup']:
        return stocks_data['name_lookup'][name_lower]
    
    # Try symbol match
    symbol = raw_company.get('symbol', '')
    if symbol:
        # Remove exchange suffix (.DE, .AS, etc.)
        base_symbol = symbol.split('.')[0]
        if base_symbol in stocks_data['symbol_lookup']:
            return stocks_data['symbol_lookup'][base_symbol]
    
    # Try ISIN match
    isin = raw_company.get('isin')
    if isin:
        # Handle both single ISIN and list of ISINs
        isins = isin if isinstance(isin, list) else [isin]
        for i in isins:
            if i in stocks_data['isin_lookup']:
                return stocks_data['isin_lookup'][i]
    
    # Try normalized name match
    normalized = normalize_name(name)
    for company_name, company_data in stocks_data['companies'].items():
        if normalize_name(company_name) == normalized:
            return company_data
    
    return None


def enrich_company(raw_company: Dict[str, Any], stocks_company: Dict[str, Any], 
                   index_name: str) -> Dict[str, Any]:
    """Enrich raw company data with stocks.yaml data."""
    enriched = {}
    
    # Use name from raw data (more up-to-date)
    enriched['name'] = raw_company.get('name', stocks_company.get('name'))
    
    # Symbol - prefer raw data
    if 'symbol' in raw_company:
        enriched['symbol'] = raw_company['symbol']
    elif 'symbol' in stocks_company:
        enriched['symbol'] = stocks_company['symbol']
    
    # Country
    if 'country' in raw_company:
        enriched['country'] = raw_company['country']
    elif 'country' in stocks_company:
        enriched['country'] = stocks_company['country']
    
    # Industries - merge from both sources
    industries = set()
    if 'industries' in stocks_company:
        industries.update(stocks_company['industries'])
    if 'sector' in raw_company:
        industries.add(raw_company['sector'])
    if 'industry' in raw_company:
        industries.add(raw_company['industry'])
    if industries:
        enriched['industries'] = sorted(list(industries))
    
    # Symbols from stocks.yaml
    if 'symbols' in stocks_company:
        enriched['symbols'] = stocks_company['symbols']
    
    # Metadata - merge from both sources
    metadata = {}
    if 'metadata' in stocks_company:
        metadata.update(stocks_company['metadata'])
    
    # Add new metadata from raw data
    for field in ['founded', 'employees', 'revenue', 'headquarters', 'website']:
        if field in raw_company and raw_company[field]:
            metadata[field] = raw_company[field]
    
    if metadata:
        enriched['metadata'] = metadata
    
    # ISINs - merge from both sources
    isins = set()
    if 'isins' in stocks_company:
        isins.update(stocks_company['isins'])
    if 'isin' in raw_company:
        raw_isin = raw_company['isin']
        if isinstance(raw_isin, list):
            isins.update(raw_isin)
        else:
            isins.add(raw_isin)
    if isins:
        enriched['isins'] = sorted(list(isins))
    
    # Wikipedia URL
    if 'wikipedia_url' in raw_company:
        enriched['wikipedia_url'] = raw_company['wikipedia_url']
    
    # Additional raw data fields
    for field in ['company_type', 'traded_as', 'key_people', 'products', 
                  'operating_income', 'net_income', 'total_assets', 'total_equity', 'founder']:
        if field in raw_company and raw_company[field]:
            if 'metadata' not in enriched:
                enriched['metadata'] = {}
            enriched['metadata'][field] = raw_company[field]
    
    # Akas from stocks.yaml
    if 'akas' in stocks_company:
        enriched['akas'] = stocks_company['akas']
    else:
        enriched['akas'] = []
    
    return enriched


def process_index(json_path: Path, stocks_data: Dict, output_dir: Path, index_name: str):
    """Process a single index JSON file and create enriched YAML."""
    logger.info(f"Processing {index_name}...")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    enriched_companies = []
    matched_count = 0
    new_count = 0
    new_companies = []
    matched_companies = set()
    
    for raw_company in raw_data.get('companies', []):
        stocks_company = find_company_match(raw_company, stocks_data)
        
        if stocks_company:
            matched_count += 1
            matched_companies.add(stocks_company.get('name'))
            enriched = enrich_company(raw_company, stocks_company, index_name)
        else:
            new_count += 1
            new_companies.append(raw_company.get('name', 'Unknown'))
            # Create entry from raw data only
            enriched = {
                'name': raw_company.get('name'),
                'symbol': raw_company.get('symbol'),
                'industries': [raw_company['sector']] if 'sector' in raw_company else [],
                'akas': []
            }
            
            if 'country' in raw_company:
                enriched['country'] = raw_company['country']
            
            if 'isin' in raw_company:
                isin = raw_company['isin']
                enriched['isins'] = isin if isinstance(isin, list) else [isin]
            
            if 'wikipedia_url' in raw_company:
                enriched['wikipedia_url'] = raw_company['wikipedia_url']
            
            # Add metadata
            metadata = {}
            for field in ['founded', 'employees', 'revenue', 'headquarters', 'website',
                         'company_type', 'traded_as', 'industry', 'key_people', 'products',
                         'operating_income', 'net_income', 'total_assets', 'total_equity', 'founder']:
                if field in raw_company and raw_company[field]:
                    metadata[field] = raw_company[field]
            
            if metadata:
                enriched['metadata'] = metadata
        
        enriched_companies.append(enriched)
    
    # Find removed companies (in stocks.yaml but not in raw data)
    removed_companies = []
    for company_name, company_data in stocks_data['companies'].items():
        indices = company_data.get('indices', [])
        if index_name in indices and company_name not in matched_companies:
            removed_companies.append(company_name)
    
    # Create output YAML
    output_data = {
        'name': index_name,
        'companies': enriched_companies
    }
    
    # Add index Yahoo symbol if available
    if index_name in stocks_data['indices']:
        yahoo_symbol = stocks_data['indices'][index_name].get('yahoo')
        if yahoo_symbol:
            output_data['yahoo'] = yahoo_symbol
    
    # Write YAML file
    output_path = output_dir / f"{json_path.stem}.yaml"
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(output_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    logger.info(f"  ✓ {index_name}: {len(enriched_companies)} companies ({matched_count} matched, {new_count} new, {len(removed_companies)} removed)")
    
    if new_companies:
        logger.info(f"    NEW: {', '.join(new_companies)}")
    
    if removed_companies:
        logger.info(f"    REMOVED: {', '.join(removed_companies)}")
    
    logger.info(f"  → {output_path}")


def main():
    """Main function."""
    project_root = Path(__file__).parent.parent
    stocks_yaml_path = project_root / 'stocks.yaml'
    indices_raw_dir = project_root / 'indices_raw'
    indices_dir = project_root / 'indices'
    
    # Create indices directory if it doesn't exist
    indices_dir.mkdir(exist_ok=True)
    
    # Load stocks.yaml
    logger.info("Loading stocks.yaml...")
    stocks_data = load_stocks_yaml(stocks_yaml_path)
    logger.info(f"  Loaded {len(stocks_data['companies'])} companies from stocks.yaml")
    
    # Process each JSON file
    for json_file in sorted(indices_raw_dir.glob('*.json')):
        index_name = INDEX_MAPPING.get(json_file.name, json_file.stem.replace('_', ' ').title())
        process_index(json_file, stocks_data, indices_dir, index_name)
    
    logger.info("\n✓ All indices processed successfully!")


if __name__ == '__main__':
    main()
