#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sync canonical company names back into stocks.yaml for clearer git diffs.

- Reads indices/*.yaml to build canonical names per company (ISIN > Wikipedia URL)
- Updates stocks.yaml companies:
  - If canonical name differs, set `name` to canonical
  - Append previous name to `akas` (if not already present)
- Optional: update indices membership (disabled by default to keep scope tight)

Usage:
  python tools/sync_canonical_to_stocks.py --stocks stocks.yaml --indices-dir indices --dry-run
  python tools/sync_canonical_to_stocks.py --stocks stocks.yaml --indices-dir indices

Copyright 2019 Slash Gordon
Use of this source code is governed by an MIT-style license that
can be found in the LICENSE file.
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List
from urllib.parse import unquote
import re

import yaml

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def canonical_key_from_company(company: Dict[str, Any]) -> str | None:
    # Prefer first ISIN
    isins: List[str] = company.get('isins') or []
    if isinstance(isins, list) and isins:
        first = isins[0]
        if first:
            return f"isin:{first}"
    # Fallback: Wikipedia URL in metadata or top-level
    metadata = company.get('metadata') or {}
    wiki = metadata.get('wikipedia_url') or company.get('wikipedia_url')
    if wiki:
        return f"wiki:{wiki.strip()}"
    return None


def wiki_title_from_company(company: Dict[str, Any]) -> str | None:
    metadata = company.get('metadata') or {}
    url = metadata.get('wikipedia_url') or company.get('wikipedia_url')
    if not url:
        return None
    try:
        slug = url.split('/wiki/', 1)[1] if '/wiki/' in url else url.rsplit('/', 1)[-1]
        slug = unquote(slug)
        title = slug.replace('_', ' ').strip()
        return re.sub(r"\s*\((?:company|Unternehmen)\)\s*$", "", title, flags=re.IGNORECASE)
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
    for data in files.values():
        for company in data.get('companies', []) or []:
            key = canonical_key_from_company(company)
            if not key:
                continue
            cand = wiki_title_from_company(company) or (company.get('name') or '').strip()
            if not cand:
                continue
            bucket = name_counts.setdefault(key, {})
            bucket[cand] = bucket.get(cand, 0) + 1
    canonical_name: Dict[str, str] = {}
    for key, counts in name_counts.items():
        items = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0].lower()))
        canonical_name[key] = items[0][0]
    return canonical_name


def load_stocks(stocks_path: Path) -> Dict[str, Any]:
    with stocks_path.open('r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def print_name_changes(stocks: Dict[str, Any], canonical_name: Dict[str, str]) -> None:
    companies = stocks.get('companies', []) or []
    pending: List[str] = []
    for c in companies:
        key = canonical_key_from_company(c)
        if not key:
            continue
        target = canonical_name.get(key)
        current = (c.get('name') or '').strip()
        if target and current and current != target:
            pending.append(f"  - {current} -> {target}")
    if pending:
        logger.info("Preview changes to stocks.yaml:")
        for line in pending:
            logger.info(line)
    else:
        logger.info("No name changes required.")


def apply_name_changes(stocks: Dict[str, Any], canonical_name: Dict[str, str]) -> int:
    companies = stocks.get('companies', []) or []
    changed = 0
    for c in companies:
        key = canonical_key_from_company(c)
        if not key:
            continue
        target = canonical_name.get(key)
        current = (c.get('name') or '').strip()
        if target and current and current != target:
            # Append current to akas if not present
            akas = c.get('akas')
            if akas is None:
                akas = []
            if current not in akas:
                akas.append(current)
            c['akas'] = akas
            # Set canonical name
            c['name'] = target
            changed += 1
    return changed


def write_stocks(stocks_path: Path, data: Dict[str, Any]) -> None:
    with stocks_path.open('w', encoding='utf-8') as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def sync_canonical_names_to_stocks(stocks_path: Path, indices_dir: Path, dry_run: bool = False) -> bool:
    """
    Public API used by build pipeline to sync canonical names into stocks.yaml.

    Returns True on success.
    """
    if not stocks_path.exists():
        logger.error(f"stocks.yaml not found: {stocks_path}")
        return False
    if not indices_dir.exists():
        logger.error(f"indices directory not found: {indices_dir}")
        return False

    indices_files = load_indices(indices_dir)
    canonical_name = build_canonical_names(indices_files)
    stocks = load_stocks(stocks_path)

    if dry_run:
        print_name_changes(stocks, canonical_name)
        return True

    changed = apply_name_changes(stocks, canonical_name)
    write_stocks(stocks_path, stocks)
    logger.info(f"stocks.yaml updated: {changed} companies renamed")
    return True


def main():
    parser = argparse.ArgumentParser(description='Sync canonical names back into stocks.yaml')
    parser.add_argument('--stocks', type=Path, default=Path(__file__).parent.parent / 'stocks.yaml', help='Path to stocks.yaml')
    parser.add_argument('--indices-dir', type=Path, default=Path(__file__).parent.parent / 'indices', help='Path to indices YAML directory')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing files')
    args = parser.parse_args()

    stocks_path = args.stocks
    indices_dir = args.indices_dir

    if not stocks_path.exists():
        logger.error(f"stocks.yaml not found: {stocks_path}")
        raise SystemExit(1)
    if not indices_dir.exists():
        logger.error(f"indices directory not found: {indices_dir}")
        raise SystemExit(1)

    ok = sync_canonical_names_to_stocks(stocks_path, indices_dir, dry_run=args.dry_run)
    if not ok:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
