#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Wikipedia Table Parser
Parses Wikipedia tables based on configuration from index_sources.yaml

Copyright 2019 Slash Gordon
Use of this source code is governed by an MIT-style license that
can be found in the LICENSE file.
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import yaml
import json
import os
import logging
import click

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class WikiTableParser:
    """Parses Wikipedia tables for stock index data"""
    
    def __init__(self, config_path: str = 'index_sources.yaml'):
        """Initialize parser with configuration file"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
    
    def fetch_page(self, url: str) -> BeautifulSoup:
        """Fetch and parse Wikipedia page"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; PyTickerSymbols/1.0; +https://github.com/portfolioplus/pytickersymbols)'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    
    def _extract_language_links(self, soup: BeautifulSoup, url: str) -> Dict[str, str]:
        """Extract language links from Wikipedia page"""
        lang_links = {}
        
        # Modern Wikipedia structure: find language dropdown
        lang_dropdown = soup.find('div', id='p-lang-btn')
        if lang_dropdown:
            # Find all interlanguage links
            for link in lang_dropdown.find_all('a', class_='interlanguage-link-target'):
                href = link.get('href')
                hreflang = link.get('hreflang')
                
                if href and hreflang:
                    # Handle special cases like 'en-simple' -> 'simple'
                    if hreflang == 'en-simple':
                        lang_code = 'simple'
                    elif hreflang == 'nb':  # Norwegian Bokmål
                        lang_code = 'no'
                    elif '-' in hreflang:  # Other variants like 'zh-min-nan'
                        lang_code = hreflang.split('-')[0]
                    else:
                        lang_code = hreflang
                    
                    lang_links[lang_code] = href
        
        # Fallback: check older interwiki format
        if not lang_links:
            interwiki = soup.find('nav', id='p-lang')
            if interwiki:
                for link in interwiki.find_all('a', class_='interlanguage-link-target'):
                    href = link.get('href')
                    hreflang = link.get('hreflang')
                    
                    if href and hreflang:
                        lang_links[hreflang] = href
        
        # Add current page's language
        match = re.match(r'https://([a-z]{2,3})\.wikipedia\.org/', url)
        if match:
            current_lang = match.group(1)
            lang_links[current_lang] = url
        
        logger.debug(f"Found {len(lang_links)} language versions for {url}")
        return lang_links
    
    def _has_isin_data(self, data: List[Dict[str, str]]) -> bool:
        """Check if parsed data contains ISIN information"""
        if not data:
            return False
        # Check if any entry has ISIN field with actual data
        return any('isin' in entry and entry['isin'] for entry in data)
    
    def _merge_data_sources(self, primary: List[Dict[str, str]], secondary: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Merge data from two sources, preferring primary but filling gaps with secondary"""
        if not secondary:
            return primary
        if not primary:
            return secondary
        
        # Create a mapping by name for easier lookup
        secondary_by_name = {entry.get('name', ''): entry for entry in secondary}
        
        merged = []
        for entry in primary:
            name = entry.get('name', '')
            # Start with primary data
            merged_entry = entry.copy()
            
            # Fill in missing fields from secondary if available
            if name in secondary_by_name:
                for key, value in secondary_by_name[name].items():
                    if key not in merged_entry or not merged_entry[key]:
                        merged_entry[key] = value
            
            merged.append(merged_entry)
        
        return merged
    
    def find_table(self, soup: BeautifulSoup, table_title_regex: Optional[str] = None) -> Optional[Any]:
        """Find the appropriate table based on regex pattern or required columns"""
        tables = soup.find_all('table', class_='wikitable')
        
        if table_title_regex:
            pattern = re.compile(table_title_regex, re.IGNORECASE)
            # Look for table with matching caption or preceding header
            for table in tables:
                # Check caption
                caption = table.find('caption')
                if caption and pattern.search(caption.get_text()):
                    return table
                
                # Check preceding headers (h2, h3, etc.)
                prev_elements = table.find_all_previous(['h2', 'h3', 'h4'])
                for header in prev_elements[:3]:  # Check last 3 headers
                    if pattern.search(header.get_text()):
                        return table
        
        # If no regex or no match, return first table with required columns
        for table in tables:
            if self._has_required_columns(table):
                return table
        
        return None
    
    def _has_required_columns(self, table: Any) -> bool:
        """Check if table has basic required columns"""
        headers = self._extract_headers(table)
        # At minimum, we need some identifier (symbol, name, or ISIN)
        has_identifier = any(
            any(keyword.lower() in h.lower() for keyword in ['company', 'name', 'ticker', 'symbol', 'isin'])
            for h in headers
        )
        return has_identifier
    
    def _extract_headers(self, table: Any) -> List[str]:
        """Extract column headers from table"""
        headers = []
        header_row = table.find('tr')
        if header_row:
            for th in header_row.find_all(['th', 'td']):
                headers.append(th.get_text(strip=True))
        return headers
    
    def _find_column_index(self, headers: List[str], column_names: List[str]) -> Optional[int]:
        """Find column index based on priority list of possible names"""
        for name in column_names:
            for idx, header in enumerate(headers):
                if name.lower() in header.lower():
                    return idx
        return None
    
    def _convert_symbol(self, symbol: str, converter_rules: List[Dict[str, str]] = None) -> str:
        """Convert symbol using configured conversion rules"""
        if not converter_rules or not symbol:
            return symbol
        
        for rule in converter_rules:
            pattern = rule.get('pattern')
            format_str = rule.get('format')
            
            if not pattern or not format_str:
                continue
            
            match = re.match(pattern, symbol)
            if match:
                # Replace {1}, {2}, etc. with capture groups
                result = format_str
                for i, group in enumerate(match.groups(), 1):
                    result = result.replace(f'{{{i}}}', group)
                
                logger.debug(f"Converted symbol: {symbol} -> {result}")
                return result
        
        return symbol
    
    def _parse_isins(self, isin_text: str) -> List[str]:
        """Parse ISIN field that may contain multiple ISINs"""
        if not isin_text:
            return []
        
        # ISIN format: 2 letter country code + 9 alphanumeric + 1 check digit = 12 chars
        # Pattern: [A-Z]{2}[A-Z0-9]{9}[0-9]
        isin_pattern = re.compile(r'[A-Z]{2}[A-Z0-9]{9}[0-9]')
        isins = isin_pattern.findall(isin_text)
        
        # Return unique ISINs in order they appear
        seen = set()
        result = []
        for isin in isins:
            if isin not in seen:
                seen.add(isin)
                result.append(isin)
        
        return result
    
    def _extract_company_link(self, cell: Any, base_url: str) -> Optional[str]:
        """Extract Wikipedia article link from a table cell"""
        # Look for first link in the cell
        link = cell.find('a', href=True)
        if link and link.get('href', '').startswith('/wiki/'):
            # Convert to full URL using the base URL's domain
            href = link['href']
            # Only return if it's an article link (not red links or external)
            if not href.startswith('/wiki/File:') and not href.startswith('/wiki/Category:'):
                # Extract domain from base_url (e.g., https://de.wikipedia.org)
                match = re.match(r'(https://[a-z]{2}\.wikipedia\.org)', base_url)
                if match:
                    base_domain = match.group(1)
                else:
                    base_domain = "https://en.wikipedia.org"
                return f"{base_domain}{href}"
        return None
    
    def _extract_company_info(self, link_url: Optional[str], language_fallbacks: List[str] = None, page_lang_links: Dict[str, str] = None) -> Dict[str, str]:
        """Extract additional company information from Wikipedia article with language fallbacks for ISIN"""
        if not link_url:
            return {}
        
        if language_fallbacks is None:
            language_fallbacks = ['en', 'de', 'fr']
        
        if page_lang_links is None:
            page_lang_links = {}
        
        info = {}
        
        def _parse_infobox(url: str) -> Dict[str, str]:
            """Helper to parse infobox from a given URL"""
            result = {}
            try:
                soup = self.fetch_page(url)
                # Find infobox - match any table with 'infobox' in its class list
                infobox = soup.find('table', class_=lambda x: x and 'infobox' in x.split())
                if not infobox:
                    return result
                
                # Parse infobox rows
                for row in infobox.find_all('tr'):
                    th = row.find('th')
                    td = row.find('td')
                    
                    # Handle both English (th/td) and German (td/td with bold first) formats
                    label_elem = None
                    value_elem = None
                    
                    if th and td:
                        # English format: <th>label</th><td>value</td>
                        label_elem = th
                        value_elem = td
                    else:
                        # German format: <td style="font-weight:bold;">label</td><td>value</td>
                        tds = row.find_all('td')
                        if len(tds) >= 2:
                            label_elem = tds[0]
                            value_elem = tds[1]
                    
                    if label_elem and value_elem:
                        label = label_elem.get_text(strip=True).lower()
                        # Use separator to preserve spacing between elements
                        value = value_elem.get_text(separator=' ', strip=True)
                        
                        # Clean up value
                        value = re.sub(r'\[.*?\]', '', value)  # Remove references
                        value = re.sub(r'\s+', ' ', value).strip()  # Normalize whitespace
                        
                        # Map common infobox fields
                        field_mapping = {
                            'type': 'company_type',
                            'traded as': 'traded_as',
                            'isin': 'isin',
                            'industry': 'industry',
                            'founded': 'founded',
                            'founder': 'founder',
                            'headquarters': 'headquarters',
                            'key people': 'key_people',
                            'products': 'products',
                            'revenue': 'revenue',
                            'operating income': 'operating_income',
                            'net income': 'net_income',
                            'total assets': 'total_assets',
                            'total equity': 'total_equity',
                            'number of employees': 'employees',
                            'website': 'website',
                        }
                        
                        for key, field_name in field_mapping.items():
                            if key in label:
                                # Special handling for ISIN - split multiple ISINs
                                if field_name == 'isin':
                                    isins = self._parse_isins(value)
                                    if len(isins) > 1:
                                        result[field_name] = isins
                                    elif len(isins) == 1:
                                        result[field_name] = isins[0]
                                # Special handling for website - remove spaces around dots
                                elif field_name == 'website':
                                    result[field_name] = re.sub(r'\s*\.\s*', '.', value)
                                else:
                                    result[field_name] = value
                                break
                
                logger.debug(f"Extracted info from {url}: {len(result)} fields")
            except Exception as e:
                logger.warning(f"Could not extract company info from {url}: {e}")
            
            return result
        
        # Try primary URL and extract language links
        soup = self.fetch_page(link_url)
        company_lang_links = self._extract_language_links(soup, link_url)
        
        # Parse infobox from primary URL
        info = _parse_infobox(link_url)
        
        # If ISIN is found, return immediately
        if 'isin' in info and info['isin']:
            return info
        
        # Otherwise, try language fallbacks for ISIN using actual language links
        logger.debug(f"No ISIN in primary article, trying language fallbacks for: {link_url}")
        
        for lang_code in language_fallbacks:
            try:
                # Use the extracted language links from the company article
                if lang_code not in company_lang_links:
                    logger.debug(f"No {lang_code.upper()} version available for {link_url}")
                    continue
                
                alt_url = company_lang_links[lang_code]
                
                # Skip if it's the same as primary URL
                if alt_url == link_url:
                    continue
                
                logger.debug(f"Trying {lang_code.upper()} article: {alt_url}")
                alt_info = _parse_infobox(alt_url)
                
                # If ISIN is found in this language version, merge and return
                if 'isin' in alt_info and alt_info['isin']:
                    logger.debug(f"✓ ISIN found in {lang_code.upper()} article")
                    # Merge: prefer primary for other fields, but use ISIN from alt
                    for key, value in alt_info.items():
                        if key not in info or not info[key]:
                            info[key] = value
                    return info
                    
            except Exception as e:
                logger.debug(f"Could not parse {lang_code.upper()} article: {e}")
                continue
        
        return info
    
    def _parse_list_format(self, soup: BeautifulSoup, url: str, 
                          extract_company_info: bool,
                          language_fallbacks: List[str] = None,
                          symbol_converter: List[Dict[str, str]] = None,
                          heading_pattern: str = 'Components') -> tuple[List[Dict[str, str]], Dict[str, str]]:
        """Parse Nikkei 225 style list format: Company Name (TYO: XXXX)"""
        page_lang_links = self._extract_language_links(soup, url)
        results = []
        
        # Pattern to match: Company Name (TYO: 1234) or Company Name (TYO: 1234)(extra text)
        pattern = re.compile(r'^(.+?)\s*\(TYO:\s*(\d+)\)')
        
        # Get all list items - try multiple selectors
        items = []
        
        # Find the heading matching the pattern
        components_heading = None
        for heading in soup.find_all(['h2', 'h3']):
            heading_text = heading.get_text(strip=True)
            if heading_pattern in heading_text:
                components_heading = heading
                logger.debug(f"Found Components heading: {heading_text}")
                break
        
        if not components_heading:
            logger.warning(f"Could not find '{heading_pattern}' heading")
            return results, page_lang_links
        
        logger.debug(f"Components heading tag: {components_heading.name}, parent: {components_heading.parent.name if components_heading.parent else 'None'}")
        
        # Parse all subsections under Components using find_all_next
        # Find all h3 headers after the Components heading until next h2
        found_h3 = False
        for elem in components_heading.find_all_next():
            # Stop at next h2
            if elem.name == 'h2':
                logger.debug(f"Reached next h2 section: {elem.get_text(strip=True)[:50]}")
                break
            
            # Check if this is a subsection heading (h3)
            if elem.name == 'h3':
                found_h3 = True
                sector = elem.get_text(strip=True)
                # Remove [edit] links from sector names
                sector = re.sub(r'\\[edit\\]', '', sector).strip()
                logger.debug(f"Found h3 sector heading: {sector}")
                
                # Find list items - try find_next_sibling first, then find_next
                ul = elem.find_next_sibling('ul')
                if not ul:
                    # Try find_next if sibling doesn't work
                    ul = elem.find_next('ul')
                    if ul:
                        logger.debug(f"  Found ul using find_next (not sibling)")
                
                if ul:
                    lis = ul.find_all('li', recursive=False)
                    logger.debug(f"  Found {len(lis)} list items under {sector}")
                    if lis:
                        logger.debug(f"    First item text: {lis[0].get_text()[:80]}")
                    for li in lis:
                        items.append((li, sector))
                else:
                    logger.debug(f"  No ul found for {sector}")
        
        if not found_h3:
            logger.warning("No h3 headings found after Components heading")
        
        logger.info(f"Found {len(items)} total list items")
        
        # Parse each item
        for li, sector in items:
            text = li.get_text()
            match = pattern.search(text)
            if match:
                company_name = match.group(1).strip()
                ticker = match.group(2).strip()
                
                # Extract company link
                link = li.find('a', href=True)
                company_link = None
                if link and link.get('href', '').startswith('/wiki/'):
                    href = link['href']
                    if not href.startswith('/wiki/File:') and not href.startswith('/wiki/Category:'):
                        match_domain = re.match(r'(https://[a-z]{2}\.wikipedia\.org)', url)
                        base_domain = match_domain.group(1) if match_domain else "https://en.wikipedia.org"
                        company_link = f"{base_domain}{href}"
                
                entry = {
                    'name': company_name,
                    'symbol': ticker,
                    'sector': sector
                }
                
                # Apply symbol conversion
                entry['symbol'] = self._convert_symbol(entry['symbol'], symbol_converter)
                
                if company_link:
                    entry['wikipedia_url'] = company_link
                    
                    # Extract additional company info if enabled
                    if extract_company_info:
                        company_info = self._extract_company_info(company_link, language_fallbacks, page_lang_links)
                        entry.update(company_info)
                
                results.append(entry)
        
        return results, page_lang_links
    
    def _parse_table_from_url(self, url: str, table_title_regex: Optional[str], 
                              columns_config: Dict, extract_company_info: bool,
                              language_fallbacks: List[str] = None,
                              symbol_converter: List[Dict[str, str]] = None,
                              parse_format: str = 'table') -> tuple[List[Dict[str, str]], Dict[str, str]]:
        """Helper method to parse table from a specific URL"""
        # Fetch page
        soup = self.fetch_page(url)
        
        # Extract language links from the page
        page_lang_links = self._extract_language_links(soup, url)
        
        # Handle list format (e.g., Nikkei 225)
        if parse_format == 'list':
            heading_pattern = columns_config.get('heading_pattern', 'Components')
            return self._parse_list_format(soup, url, extract_company_info, 
                                          language_fallbacks, symbol_converter, heading_pattern)
        
        # Find table
        table = self.find_table(soup, table_title_regex)
        
        if not table:
            return [], page_lang_links
        
        # Extract headers
        headers = self._extract_headers(table)
        
        # Map columns
        column_indices = {}
        
        for field, possible_names in columns_config.items():
            idx = self._find_column_index(headers, possible_names)
            if idx is not None:
                column_indices[field] = idx
        
        # Check if we found any columns
        if not column_indices:
            logger.warning(f"No matching columns found in table. Headers: {headers}")
            return [], page_lang_links
        
        # Parse rows
        results = []
        rows = table.find_all('tr')[1:]  # Skip header row
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < max(column_indices.values()) + 1:
                continue
            
            entry = {}
            company_link = None
            
            for field, idx in column_indices.items():
                cell = cells[idx]
                
                # Extract company article link from name field
                if field == 'name' and company_link is None:
                    company_link = self._extract_company_link(cell, url)
                    if company_link:
                        entry['wikipedia_url'] = company_link
                
                # Extract text, clean up references and notes
                text = cell.get_text(strip=True)
                text = re.sub(r'\[.*?\]', '', text)  # Remove references
                text = re.sub(r'\s+', ' ', text).strip()  # Normalize whitespace
                
                if text:
                    # Apply symbol conversion if this is a symbol field
                    if field == 'symbol':
                        text = self._convert_symbol(text, symbol_converter)
                    entry[field] = text
            
            # Extract additional company info if enabled
            if extract_company_info and company_link:
                company_info = self._extract_company_info(company_link, language_fallbacks, page_lang_links)
                entry.update(company_info)
            
            # Only add entries that have at least one field
            if entry:
                results.append(entry)
        
        return results, page_lang_links
    
    def parse_table(self, index_config: Dict) -> List[Dict[str, str]]:
        """Parse table for a specific index configuration"""
        source = index_config['source']
        
        if source['type'] != 'wikipedia':
            raise ValueError(f"Unsupported source type: {source['type']}")
        
        # Get configuration
        primary_url = source['url']
        table_title_regex = source.get('table_title_regex')
        columns_config = source.get('columns', {})
        extract_company_info = source.get('extract_company_info', False)
        parse_format = source.get('format', 'table')  # 'table' or 'list'
        
        # Get list of language codes to try for company info extraction
        language_fallbacks = source.get('language_fallbacks', ['en', 'de', 'fr'])
        
        # Get symbol converter rules
        symbol_converter = source.get('symbol_converter', [])
        
        # Parse from primary URL
        logger.info(f"Parsing from primary URL: {primary_url}")
        results, _ = self._parse_table_from_url(primary_url, table_title_regex, 
                                                columns_config, extract_company_info,
                                                language_fallbacks, symbol_converter, parse_format)
        
        if not results:
            raise ValueError(f"Could not find data for {index_config['name']}")
        
        return results
    
    def parse_index(self, index_name: str) -> List[Dict[str, str]]:
        """Parse data for a specific index by name"""
        for index_config in self.config['indices']:
            if index_config['name'] == index_name:
                return self.parse_table(index_config)
        
        raise ValueError(f"Index '{index_name}' not found in configuration")
    
    def parse_all_indices(self) -> Dict[str, List[Dict[str, str]]]:
        """Parse data for all configured indices"""
        results = {}
        for index_config in self.config['indices']:
            index_name = index_config['name']
            logger.info(f"Parsing {index_name}...")
            try:
                results[index_name] = self.parse_table(index_config)
                logger.info(f"  Found {len(results[index_name])} entries")
            except Exception as e:
                logger.error(f"  Error: {e}")
                results[index_name] = []
        
        return results
    
    def write_to_json(self, index_name: str, data: List[Dict[str, str]], output_dir: str = '../indices_raw'):
        """Write parsed data to JSON file"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Create safe filename
        filename = index_name.replace(' ', '_').replace('/', '_').lower()
        output_path = os.path.join(output_dir, f'{filename}.json')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'index': index_name,
                'count': len(data),
                'companies': data
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"  Written to {output_path}")
    
    def write_all_to_json(self, data: Dict[str, List[Dict[str, str]]], output_dir: str = '../indices_raw'):
        """Write all parsed indices to JSON files"""
        for index_name, entries in data.items():
            self.write_to_json(index_name, entries, output_dir)


@click.command()
@click.argument('index_name', required=False)
@click.option(
    '-o', '--output-dir',
    default='../indices_raw',
    show_default=True,
    help='Output directory for JSON files'
)
@click.option(
    '-v', '--verbose',
    is_flag=True,
    help='Enable verbose logging'
)
def main(index_name, output_dir, verbose):
    """Parse Wikipedia tables for stock index data.
    
    INDEX_NAME: Specific index to parse (optional, parses all if not provided)
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.realpath(__file__))
    os.chdir(script_dir)
    
    parser = WikiTableParser()
    
    if index_name:
        # Parse specific index
        logger.info(f"Parsing {index_name}...")
        data = parser.parse_index(index_name)
        logger.info(f"\n{index_name} data:")
        for entry in data:
            logger.info(entry)
        
        # Write to JSON
        parser.write_to_json(index_name, data, output_dir)
    else:
        # Parse all indices
        data = parser.parse_all_indices()
        
        # Write all to JSON
        logger.info("\nWriting JSON files...")
        parser.write_all_to_json(data, output_dir)
        
        logger.info("\nSummary:")
        for idx_name, entries in data.items():
            logger.info(f"{idx_name}: {len(entries)} entries")


if __name__ == '__main__':
    main()
