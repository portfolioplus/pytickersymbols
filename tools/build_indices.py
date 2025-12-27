#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Build script for GitHub Actions to:
1. Parse Wikipedia tables and create indices_raw JSON files
2. Enrich with stocks.yaml data
3. Generate Python module with indices as dictionaries

Copyright 2019 Slash Gordon
Use of this source code is governed by an MIT-style license that
can be found in the LICENSE file.
"""

import json
import yaml
import logging
import sys
import click
from pathlib import Path
from typing import Dict, List, Any
from wiki_table_parser import WikiTableParser
from config import INDEX_MAPPING

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def parse_wikipedia_tables(config_path: Path, output_dir: Path, skip_existing: bool = True) -> bool:
    """Step 1: Parse Wikipedia tables and create JSON files.
    
    Args:
        config_path: Path to index_sources.yaml
        output_dir: Directory to save parsed JSON files
        skip_existing: If True, skip indices that have already been parsed (default: True)
    """
    logger.info("=" * 80)
    logger.info("STEP 1: Parsing Wikipedia tables")
    logger.info("=" * 80)
    
    output_dir.mkdir(exist_ok=True)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    parser = WikiTableParser(config_path=str(config_path))
    success_count = 0
    fail_count = 0
    
    for index_config in config.get('indices', []):
        index_name = index_config.get('name')
        if not index_name:
            continue
        
        # Find matching filename
        output_filename = None
        for filename, name in INDEX_MAPPING.items():
            if name == index_name:
                output_filename = filename
                break
        
        if not output_filename:
            # Fallback to generated filename
            output_filename = f"{index_name.lower().replace(' ', '_').replace('&', '').replace('__', '_')}.json"
        
        output_path = output_dir / output_filename
        
        # Skip if already parsed (when skip_existing is enabled)
        if skip_existing and output_path.exists():
            logger.info(f"\n⏭️  Skipping {index_name} (already exists: {output_path.name})")
            success_count += 1
            continue
        
        try:
            logger.info(f"\nParsing {index_name}...")
            
            # Pass the entire index_config to parse_table
            data = parser.parse_table(index_config)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'index': index_name,
                    'count': len(data),
                    'companies': data
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"  ✓ Saved {len(data)} companies to {output_path}")
            success_count += 1
            
        except Exception as e:
            logger.error(f"  ✗ Failed to parse {index_name}: {e}")
            fail_count += 1
    
    logger.info(f"\n{'=' * 80}")
    logger.info(f"Wikipedia parsing complete: {success_count} succeeded, {fail_count} failed")
    logger.info(f"{'=' * 80}\n")
    
    return fail_count == 0


def enrich_indices(stocks_yaml_path: Path, indices_raw_dir: Path, indices_dir: Path) -> bool:
    """Step 2: Enrich raw JSON files with stocks.yaml data."""
    logger.info("=" * 80)
    logger.info("STEP 2: Enriching indices with stocks.yaml data")
    logger.info("=" * 80)
    
    from enrich_indices import load_stocks_yaml, process_index
    
    indices_dir.mkdir(exist_ok=True)
    
    # Load stocks.yaml
    logger.info("\nLoading stocks.yaml...")
    stocks_data = load_stocks_yaml(stocks_yaml_path)
    logger.info(f"  Loaded {len(stocks_data['companies'])} companies from stocks.yaml\n")
    
    # Process each JSON file
    success_count = 0
    fail_count = 0
    
    for json_file in sorted(indices_raw_dir.glob('*.json')):
        index_name = INDEX_MAPPING.get(json_file.name, json_file.stem.replace('_', ' ').title())
        
        try:
            process_index(json_file, stocks_data, indices_dir, index_name)
            success_count += 1
        except Exception as e:
            logger.error(f"  ✗ Failed to enrich {index_name}: {e}")
            fail_count += 1
    
    logger.info(f"\n{'=' * 80}")
    logger.info(f"Enrichment complete: {success_count} succeeded, {fail_count} failed")
    logger.info(f"{'=' * 80}\n")
    
    return fail_count == 0


def generate_python_module(indices_dir: Path, output_file: Path) -> bool:
    """Step 3: Generate Python module with indices as dictionaries."""
    logger.info("=" * 80)
    logger.info("STEP 3: Generating Python module")
    logger.info("=" * 80)
    
    indices_data = {}
    
    for yaml_file in sorted(indices_dir.glob('*.yaml')):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            index_name = data.get('name')
            if index_name:
                indices_data[index_name] = data
                logger.info(f"  ✓ Loaded {index_name} ({len(data.get('companies', []))} companies)")
        except Exception as e:
            logger.error(f"  ✗ Failed to load {yaml_file}: {e}")
    
    # Generate Python module
    logger.info(f"\nGenerating Python module: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('"""\n')
        f.write('Auto-generated indices data module.\n')
        f.write('Generated from Wikipedia data enriched with historical stocks.yaml.\n')
        f.write('\n')
        f.write('DO NOT EDIT MANUALLY - This file is auto-generated by build_indices.py\n')
        f.write('"""\n\n')
        
        # Write indices dictionary
        f.write('INDICES = ')
        f.write(repr(indices_data))
        f.write('\n\n')
        
        # Write convenience functions
        f.write('def get_index(name: str):\n')
        f.write('    """Get index data by name."""\n')
        f.write('    return INDICES.get(name)\n\n')
        
        f.write('def get_all_indices():\n')
        f.write('    """Get all available indices."""\n')
        f.write('    return list(INDICES.keys())\n\n')
        
        f.write('def get_companies(index_name: str):\n')
        f.write('    """Get companies for a specific index."""\n')
        f.write('    index_data = INDICES.get(index_name)\n')
        f.write('    return index_data.get("companies", []) if index_data else []\n')
    
    logger.info(f"  ✓ Generated {output_file}")
    logger.info(f"  ✓ Total indices: {len(indices_data)}")
    
    total_companies = sum(len(idx.get('companies', [])) for idx in indices_data.values())
    logger.info(f"  ✓ Total companies: {total_companies}")
    
    logger.info(f"\n{'=' * 80}")
    logger.info("Python module generation complete")
    logger.info(f"{'=' * 80}\n")
    
    return True


@click.command()
@click.option('--force', is_flag=True, help='Force re-parsing of all indices (ignore existing files)')
def main(force):
    """Main build pipeline."""
    project_root = Path(__file__).parent.parent
    
    # Paths
    config_path = project_root / 'tools' / 'index_sources.yaml'
    stocks_yaml_path = project_root / 'stocks.yaml'
    indices_raw_dir = project_root / 'indices_raw'
    indices_dir = project_root / 'indices'
    output_module = project_root / 'src' / 'pytickersymbols' / 'indices_data.py'
    
    logger.info("\\n" + "=" * 80)
    logger.info("PYTICKERSYMBOLS BUILD PIPELINE")
    logger.info("=" * 80)
    logger.info(f"Project root: {project_root}")
    logger.info(f"Config: {config_path}")
    logger.info(f"Output: {output_module}")
    logger.info("=" * 80 + "\\n")
    
    # Create output directory
    output_module.parent.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Parse Wikipedia
    skip_existing = not force
    if not parse_wikipedia_tables(config_path, indices_raw_dir, skip_existing=skip_existing):
        logger.error("❌ Wikipedia parsing failed")
        sys.exit(1)
    
    # Step 2: Enrich with stocks.yaml
    if not enrich_indices(stocks_yaml_path, indices_raw_dir, indices_dir):
        logger.error("❌ Enrichment failed")
        sys.exit(1)
    
    # Step 3: Generate Python module
    if not generate_python_module(indices_dir, output_module):
        logger.error("❌ Python module generation failed")
        sys.exit(1)
    
    logger.info("\\n" + "=" * 80)
    logger.info("✅ BUILD COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Generated: {output_module}")
    logger.info("=" * 80 + "\\n")


if __name__ == '__main__':
    main()
