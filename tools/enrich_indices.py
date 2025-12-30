#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enrich indices_raw JSON files with data from stocks.yaml
and generate YAML files in the indices directory.

Copyright 2019 Slash Gordon
Use of this source code is governed by an MIT-style license that
can be found in the LICENSE file.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from config import INDEX_MAPPING

# ------------------------------------------------------------------------------
# logging
# ------------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------------------

def normalize_list(value) -> List[Any]:
    if not value:
        return []
    return value if isinstance(value, list) else [value]


def merge_fields(target: dict, source: dict, fields: list[str]) -> None:
    for field in fields:
        value = source.get(field)
        if value:
            target[field] = value


def normalize_name(name: str) -> str:
    suffixes = [
        " AG", " SE", " N.V.", " plc", " Inc.", " Corp.", " Corporation",
        " Limited", " Ltd.", " GmbH", " S.A.", " NV", " Oyj",
    ]
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
    return name.strip().lower()


def strip_parenthetical_disambiguation(name: Optional[str]) -> Optional[str]:
    if not name:
        return name
    # Remove trailing qualifiers like '(company)' or '(Unternehmen)'
    return re.sub(r"\s*\((?:company|Unternehmen)\)\s*$", "", name, flags=re.IGNORECASE)


# ------------------------------------------------------------------------------
# country & exchange logic
# ------------------------------------------------------------------------------

COUNTRY_PATTERNS = {
    "u.s.": "United States",
    "usa": "United States",
    "united states": "United States",
    "germany": "Germany",
    "france": "France",
    "uk": "United Kingdom",
    "united kingdom": "United Kingdom",
    "netherlands": "Netherlands",
    "belgium": "Belgium",
    "spain": "Spain",
    "switzerland": "Switzerland",
    "sweden": "Sweden",
    "finland": "Finland",
    "australia": "Australia",
    "japan": "Japan",
}

EXCHANGE_MAP = {
    "Germany": [
        ("{s}.DE", "ETR:{s}", "EUR"),
        ("{s}.F", "FRA:{s}", "EUR"),
    ],
    "United States": [
        ("{s}", "NASDAQ:{s}", "USD"),
    ],
    "France": [
        ("{s}.PA", "EPA:{s}", "EUR"),
    ],
    "United Kingdom": [
        ("{s}.L", "LON:{s}", "GBP"),
    ],
    "Netherlands": [
        ("{s}.AS", "AMS:{s}", "EUR"),
    ],
    "Belgium": [
        ("{s}.BR", "EBR:{s}", "EUR"),
    ],
    "Spain": [
        ("{s}.MC", "BME:{s}", "EUR"),
    ],
    "Switzerland": [
        ("{s}.SW", "SWX:{s}", "CHF"),
    ],
    "Sweden": [
        ("{s}.ST", "STO:{s}", "SEK"),
    ],
    "Finland": [
        ("{s}.HE", "HEL:{s}", "EUR"),
    ],
    "Australia": [
        ("{s}.AX", "ASX:{s}", "AUD"),
    ],
    "Japan": [
        ("{s}.T", "TYO:{s}", "JPY"),
    ],
}


def infer_country_from_metadata(metadata: dict) -> Optional[str]:
    hq = metadata.get("headquarters", "")
    if not hq:
        return None

    hq_lower = hq.lower()
    for pattern, country in COUNTRY_PATTERNS.items():
        if pattern in hq_lower:
            return country
    return None


def build_symbols(symbol: str, country: str) -> List[Dict[str, str]]:
    # Use base ticker without any existing suffix, e.g. "SLR.MC" -> "SLR"
    base = (symbol or '').split('.')[0]
    entries = EXCHANGE_MAP.get(country)
    if not entries:
        return [{"yahoo": symbol, "google": symbol, "currency": "USD"}]

    return [
        {
            "yahoo": y.format(s=base),
            "google": g.format(s=base),
            "currency": c,
        }
        for y, g, c in entries
    ]


# ------------------------------------------------------------------------------
# data models
# ------------------------------------------------------------------------------

@dataclass
class Company:
    name: str
    symbol: Optional[str] = None
    country: Optional[str] = None
    industries: List[str] = field(default_factory=list)
    symbols: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    isins: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            k: v
            for k, v in {
                "name": self.name,
                "symbol": self.symbol,
                "country": self.country,
                "industries": self.industries or None,
                "symbols": self.symbols or None,
                "metadata": self.metadata or None,
                "isins": self.isins or None,
            }.items()
            if v is not None
        }


@dataclass
class Index:
    name: str
    companies: List[Company]
    yahoo: Optional[str] = None

    def to_dict(self) -> dict:
        data = {
            "name": self.name,
            "companies": [c.to_dict() for c in self.companies],
        }
        if self.yahoo:
            data["yahoo"] = self.yahoo
        return data


# ------------------------------------------------------------------------------
# stocks.yaml loading & lookup
# ------------------------------------------------------------------------------

def load_stocks_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    companies = data.get("companies", [])

    lookup = {
        "companies": {},
        "name": {},
        "symbol": {},
        "isin": {},
        "indices": {i["name"]: i for i in data.get("indices", [])},
    }

    for company in companies:
        name = company.get("name")
        symbol = company.get("symbol")

        if name:
            lookup["companies"][name] = company
            lookup["name"][name.lower()] = company

        if symbol:
            lookup["symbol"][symbol] = company

        for isin in company.get("isins", []):
            lookup["isin"][isin] = company

    return lookup


# ------------------------------------------------------------------------------
# matching & enrichment
# ------------------------------------------------------------------------------

def find_company_match(raw: dict, lookup: dict) -> Optional[dict]:
    """
    Match priority:
    1) Exact ISIN match (strongest)
    2) Exact name match (case-insensitive)
    3) Symbol match WITH country alignment (avoid cross-country collisions)
    4) Fallback: normalized name match (only if unique)
    """
    # 1) ISIN strict match
    for isin in normalize_list(raw.get("isin")):
        if isin and isin in lookup["isin"]:
            return lookup["isin"][isin]

    # 2) Name exact (case-insensitive)
    name = (raw.get("name") or "").strip()
    if name:
        lower = name.lower()
        if name in lookup["companies"]:
            return lookup["companies"][name]
        if lower in lookup["name"]:
            return lookup["name"][lower]

    # 3) Symbol + country alignment
    raw_symbol = (raw.get("symbol") or "")
    base = raw_symbol.split(".")[0]
    raw_country = (raw.get("country") or "").strip()
    if base and base in lookup["symbol"]:
        candidate = lookup["symbol"][base]
        cand_country = (candidate.get("country") or "").strip()
        # If both sides have country, require equality
        if raw_country and cand_country and raw_country != cand_country:
            candidate = None
        if candidate:
            return candidate

    # 4) Fallback: normalized name (last resort)
    norm = normalize_name(name)
    if norm and norm in lookup["name"]:
        return lookup["name"][norm]

    return None


def enrich_company(raw: dict, stock: Optional[dict]) -> Company:
    stock = stock or {}

    name = strip_parenthetical_disambiguation(raw.get("name") or stock.get("name"))
    symbol = raw.get("symbol") or stock.get("symbol")
    country = raw.get("country") or stock.get("country")

    industries = set(stock.get("industries", []))
    industries.update(filter(None, [raw.get("sector"), raw.get("industry")]))

    metadata = dict(stock.get("metadata", {}))
    merge_fields(
        metadata,
        raw,
        [
            "founded", "employees", "revenue", "headquarters", "website",
            "company_type", "traded_as", "key_people", "products",
            "operating_income", "net_income", "total_assets",
            "total_equity", "founder", "wikipedia_url",
        ],
    )

    if not country:
        country = infer_country_from_metadata(metadata)

    symbols = (
        stock.get("symbols")
        or (build_symbols(symbol, country) if symbol and country else [])
    )
    # Drop any symbols explicitly marked to be skipped
    symbols = [s for s in symbols if not s.get("skip")]

    isins = set(stock.get("isins", []))
    isins.update(normalize_list(raw.get("isin")))

    return Company(
        name=name,
        symbol=symbol,
        country=country,
        industries=sorted(industries),
        symbols=symbols,
        metadata=metadata,
        isins=sorted(isins),
    )


# ------------------------------------------------------------------------------
# processing
# ------------------------------------------------------------------------------

def process_index(
    json_path: Path,
    lookup: dict,
    output_dir: Path,
    index_name: str,
):
    logger.info("Processing %s...", index_name)

    with json_path.open(encoding="utf-8") as f:
        raw_data = json.load(f)

    companies: list[Company] = []
    matched_names: set[str] = set()

    for raw in raw_data.get("companies", []):
        stock = find_company_match(raw, lookup)
        if stock:
            matched_names.add(stock.get("name"))
        companies.append(enrich_company(raw, stock))

    removed = [
        name
        for name, company in lookup["companies"].items()
        if index_name in company.get("indices", [])
        and name not in matched_names
    ]

    index = Index(
        name=index_name,
        companies=companies,
        yahoo=lookup["indices"].get(index_name, {}).get("yahoo"),
    )

    output_path = output_dir / f"{json_path.stem}.yaml"
    with output_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            index.to_dict(),
            f,
            allow_unicode=True,
            sort_keys=False,
        )

    logger.info(
        "  ✓ %s: %d companies (%d removed)",
        index_name,
        len(companies),
        len(removed),
    )


# ------------------------------------------------------------------------------
# main
# ------------------------------------------------------------------------------

def main():
    root = Path(__file__).parent.parent
    stocks_yaml = root / "stocks.yaml"
    raw_dir = root / "indices_raw"
    out_dir = root / "indices"

    out_dir.mkdir(exist_ok=True)

    logger.info("Loading stocks.yaml...")
    lookup = load_stocks_yaml(stocks_yaml)
    logger.info("Loaded %d companies", len(lookup["companies"]))

    for json_file in sorted(raw_dir.glob("*.json")):
        index_name = INDEX_MAPPING.get(
            json_file.name,
            json_file.stem.replace("_", " ").title(),
        )
        process_index(json_file, lookup, out_dir, index_name)

    logger.info("✓ All indices processed successfully!")


if __name__ == "__main__":
    main()
