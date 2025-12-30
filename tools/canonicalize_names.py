#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Canonicalize company display names across indices YAMLs.

Strategy:
- Canonical key: first ISIN, else Wikipedia URL; else skip
- Preferred name: Wikipedia page title when present; otherwise most frequent existing name
- Applies changes in-place to indices/*.yaml

Usage:
  python tools/canonicalize_names.py --indices-dir indices --dry-run
  python tools/canonicalize_names.py --indices-dir indices

Copyright 2019 Slash Gordon
Use of this source code is governed by an MIT-style license that
can be found in the LICENSE file.
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Dict, Any
from urllib.parse import unquote

import yaml

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def canonical_company_key(company: Dict[str, Any]) -> str | None:
    isins = company.get('isins') or []
    if isinstance(isins, list) and len(isins) > 0 and isins[0]:
        return f"isin:{isins[0]}"
    metadata = company.get('metadata') or {}
    wiki = metadata.get('wikipedia_url') or company.get('wikipedia_url')
    if wiki:
        return f"wiki:{wiki.strip()}"
    return None


def wiki_title(company: Dict[str, Any]) -> str | None:
    metadata = company.get('metadata') or {}
    url = metadata.get('wikipedia_url') or company.get('wikipedia_url')
    if not url:
        return None
    try:
        slug = url.split('/wiki/', 1)[1] if '/wiki/' in url else url.rsplit('/', 1)[-1]
        slug = unquote(slug)
        return slug.replace('_', ' ').strip()
    except Exception:
        return None


def load_indices(indices_dir: Path) -> Dict[Path, Dict[str, Any]]:
    files = {}
    for yf in sorted(indices_dir.glob('*.yaml')):
        try:
            with yf.open('r', encoding='utf-8') as f:
                files[yf] = yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to read {yf}: {e}")
    return files


def build_canonical_names(files: Dict[Path, Dict[str, Any]]) -> Dict[str, str]:
    name_counts: Dict[str, Dict[str, int]] = {}
    # Count candidates per canonical key
    for data in files.values():
        for company in data.get('companies', []) or []:
            key = canonical_company_key(company)
            if not key:
                continue
            cand = wiki_title(company) or (company.get('name') or '').strip()
            if not cand:
                continue
            bucket = name_counts.setdefault(key, {})
            bucket[cand] = bucket.get(cand, 0) + 1
    # Choose most frequent (tie: lexical)
    canonical_name: Dict[str, str] = {}
    for key, counts in name_counts.items():
        items = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0].lower()))
        canonical_name[key] = items[0][0]
    return canonical_name


def apply_canonical_names(files: Dict[Path, Dict[str, Any]], canonical_name: Dict[str, str]) -> int:
    changed_files = 0
    for yf, data in files.items():
        changed = False
        companies = data.get('companies', []) or []
        for company in companies:
            key = canonical_company_key(company)
            if not key:
                continue
            new_name = canonical_name.get(key)
            current = (company.get('name') or '').strip()
            if new_name and current != new_name:
                company['name'] = new_name
                changed = True
        if changed:
            try:
                with yf.open('w', encoding='utf-8') as f:
                    yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
                logger.info(f"Updated names in {yf.name}")
                changed_files += 1
            except Exception as e:
                logger.error(f"Failed to write {yf}: {e}")
    return changed_files


def print_diff(files: Dict[Path, Dict[str, Any]], canonical_name: Dict[str, str]) -> None:
    for yf, data in files.items():
        companies = data.get('companies', []) or []
        out_lines = []
        for company in companies:
            key = canonical_company_key(company)
            if not key:
                continue
            new_name = canonical_name.get(key)
            current = (company.get('name') or '').strip()
            if new_name and current != new_name:
                out_lines.append(f"  - {current} -> {new_name}")
        if out_lines:
            logger.info(f"Preview {yf.name}:")
            for line in out_lines:
                logger.info(line)


def main():
    parser = argparse.ArgumentParser(description='Canonicalize company names across indices')
    parser.add_argument('--indices-dir', type=Path, default=Path(__file__).parent.parent / 'indices', help='Path to indices YAML directory')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing files')
    args = parser.parse_args()

    indices_dir = args.indices_dir
    if not indices_dir.exists():
        logger.error(f"Directory not found: {indices_dir}")
        raise SystemExit(1)

    logger.info("Loading indices from %s", indices_dir)
    files = load_indices(indices_dir)
    if not files:
        logger.info("No YAML files found")
        raise SystemExit(0)

    canonical_name = build_canonical_names(files)

    if args.dry_run:
        logger.info("Dry-run mode: showing changes only")
        print_diff(files, canonical_name)
        raise SystemExit(0)

    changed = apply_canonical_names(files, canonical_name)
    logger.info("Canonicalization complete: %d files updated", changed)


if __name__ == '__main__':
    main()
