#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Enrich company data with Yahoo Finance information
Reads JSON files from indices_raw and enriches them with additional data

Copyright 2019 Slash Gordon
Use of this source code is governed by an MIT-style license that
can be found in the LICENSE file.
"""

import json
import os
import logging
import time
from typing import Dict, List, Optional
import click

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("ERROR: yfinance not available. Install with: pip install yfinance")
    exit(1)

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class YFinanceEnricher:
    """Enriches company data using Yahoo Finance API"""
    
    def __init__(self, delay: float = 0.1):
        """
        Initialize enricher
        
        Args:
            delay: Delay in seconds between API calls to avoid rate limiting
        """
        self.delay = delay
        self._cache = {}
        self.stats = {
            'total': 0,
            'enriched': 0,
            'failed': 0,
            'cached': 0
        }
    
    def get_company_info(self, symbol: str) -> Dict:
        """
        Fetch company information from Yahoo Finance
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with company information
        """
        # Check cache
        if symbol in self._cache:
            self.stats['cached'] += 1
            return self._cache[symbol]
        
        # Rate limiting
        time.sleep(self.delay)
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
 
            # Extract relevant fields
            enriched = {}
            
            # Always use longName as name (overwrite existing)
            if info.get('longName'):
                enriched['name'] = info['longName']
            
            # Basic info
            if info.get('country'):
                enriched['country'] = info['country']
            
            if info.get('isin'):
                enriched['isin'] = info['isin']
            
            if info.get('sector'):
                enriched['sector'] = info['sector']
            
            if info.get('industry'):
                enriched['industry'] = info['industry']
            
            # Additional details
            if info.get('website'):
                enriched['website'] = info['website']
            
            if info.get('fullTimeEmployees'):
                enriched['employees'] = info['fullTimeEmployees']
            
            if info.get('marketCap'):
                enriched['market_cap'] = info['marketCap']
            
            if info.get('exchange'):
                enriched['exchange'] = info['exchange']
            
            if info.get('currency'):
                enriched['currency'] = info['currency']
            
            # Cache result
            self._cache[symbol] = enriched
            
            if enriched:
                self.stats['enriched'] += 1
                logger.debug(f"  ✓ {symbol}: {list(enriched.keys())}")
            else:
                self.stats['failed'] += 1
                logger.debug(f"  ✗ {symbol}: No data available")
            
            return enriched
            
        except Exception as e:
            logger.debug(f"  ✗ {symbol}: {str(e)}")
            self.stats['failed'] += 1
            # Cache empty result to avoid retrying
            self._cache[symbol] = {}
            return {}
    
    def enrich_company(self, company: Dict, overwrite: bool = False) -> Dict:
        """
        Enrich a single company entry
        
        Args:
            company: Company dictionary with at least 'symbol' field
            overwrite: If True, overwrite existing fields
            
        Returns:
            Enriched company dictionary
        """
        symbol = company.get('symbol')
        if not symbol:
            logger.warning(f"  Company {company.get('name', 'Unknown')} has no symbol")
            return company
        
        self.stats['total'] += 1
        
        # Get enrichment data
        enriched_data = self.get_company_info(symbol)
        
        # Merge data (don't overwrite existing fields unless specified)
        for key, value in enriched_data.items():
            # Always overwrite name field (from longName)
            if key == 'name' or overwrite or key not in company or not company.get(key):
                company[key] = value
        
        return company
    
    def enrich_index(self, index_data: Dict, overwrite: bool = False) -> Dict:
        """
        Enrich all companies in an index
        
        Args:
            index_data: Index data dictionary with 'companies' list
            overwrite: If True, overwrite existing fields
            
        Returns:
            Enriched index data
        """
        companies = index_data.get('companies', [])
        
        logger.info(f"Enriching {len(companies)} companies...")
        
        for i, company in enumerate(companies, 1):
            if i % 10 == 0:
                logger.info(f"  Progress: {i}/{len(companies)}")
            
            self.enrich_company(company, overwrite=overwrite)
        
        return index_data
    
    def process_file(self, input_path: str, output_path: Optional[str] = None, 
                     overwrite: bool = False) -> None:
        """
        Process a single JSON file
        
        Args:
            input_path: Path to input JSON file
            output_path: Path to output JSON file (if None, overwrites input)
            overwrite: If True, overwrite existing fields
        """
        logger.info(f"\nProcessing {os.path.basename(input_path)}...")
        
        # Read input file
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Enrich data
        enriched_data = self.enrich_index(data, overwrite=overwrite)
        
        # Write output file
        output_path = output_path or input_path
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(enriched_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"  Written to {output_path}")
    
    def process_directory(self, input_dir: str, output_dir: Optional[str] = None,
                          overwrite: bool = False, pattern: str = "*.json") -> None:
        """
        Process all JSON files in a directory
        
        Args:
            input_dir: Path to input directory
            output_dir: Path to output directory (if None, overwrites input files)
            overwrite: If True, overwrite existing fields
            pattern: File pattern to match (default: *.json)
        """
        if not os.path.exists(input_dir):
            logger.error(f"Input directory does not exist: {input_dir}")
            return
        
        # Create output directory if needed
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Find all JSON files
        import glob
        files = glob.glob(os.path.join(input_dir, pattern))
        
        if not files:
            logger.warning(f"No files found matching {pattern} in {input_dir}")
            return
        
        logger.info(f"Found {len(files)} files to process")
        
        # Process each file
        for input_path in sorted(files):
            output_path = None
            if output_dir:
                filename = os.path.basename(input_path)
                output_path = os.path.join(output_dir, filename)
            
            try:
                self.process_file(input_path, output_path, overwrite)
            except Exception as e:
                logger.error(f"  Error processing {input_path}: {e}")
        
        # Print statistics
        self.print_stats()
    
    def print_stats(self) -> None:
        """Print enrichment statistics"""
        logger.info("\n" + "="*50)
        logger.info("Enrichment Statistics:")
        logger.info(f"  Total companies processed: {self.stats['total']}")
        logger.info(f"  Successfully enriched: {self.stats['enriched']}")
        logger.info(f"  Failed to enrich: {self.stats['failed']}")
        logger.info(f"  Cache hits: {self.stats['cached']}")
        if self.stats['total'] > 0:
            success_rate = (self.stats['enriched'] / self.stats['total']) * 100
            logger.info(f"  Success rate: {success_rate:.1f}%")
        logger.info("="*50)


@click.command()
@click.argument(
    'input',
    type=click.Path(exists=True),
    default='../indices_raw'
)
@click.option(
    '-o', '--output',
    type=click.Path(),
    default='../indices_enriched',
    show_default=True,
    help='Output file or directory'
)
@click.option(
    '--overwrite',
    is_flag=True,
    help='Overwrite existing fields in the data'
)
@click.option(
    '--delay',
    type=float,
    default=0.1,
    show_default=True,
    help='Delay between API calls in seconds'
)
@click.option(
    '-v', '--verbose',
    is_flag=True,
    help='Enable verbose logging'
)
def main(input, output, overwrite, delay, verbose):
    """Enrich company data with Yahoo Finance information.
    
    INPUT: JSON file or directory to enrich (default: ../indices_raw)
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.realpath(__file__))
    os.chdir(script_dir)
    
    # Initialize enricher
    enricher = YFinanceEnricher(delay=delay)
    
    # Process input
    if os.path.isfile(input):
        # Single file
        enricher.process_file(input, output, overwrite=overwrite)
    elif os.path.isdir(input):
        # Directory
        enricher.process_directory(input, output, overwrite=overwrite)
    else:
        logger.error(f"Input does not exist: {input}")
        raise click.Abort()


if __name__ == '__main__':
    main()
