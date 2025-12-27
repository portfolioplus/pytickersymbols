#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Global configuration for pytickersymbols tools.
Loads index configuration from index_sources.yaml.

Copyright 2019 Slash Gordon
Use of this source code is governed by an MIT-style license that
can be found in the LICENSE file.
"""

import yaml
from pathlib import Path
from typing import Dict

def load_index_mapping() -> Dict[str, str]:
    """
    Load index mapping from index_sources.yaml.
    Returns a dict mapping filename to display name.
    """
    config_path = Path(__file__).parent / 'index_sources.yaml'
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Build mapping from index names
    index_mapping = {}
    for index in config.get('indices', []):
        name = index.get('name')
        if name:
            # Convert display name to filename format
            filename = name.lower().replace(' ', '_').replace('&', '').strip()
            filename = filename.replace('__', '_')  # Remove double underscores
            index_mapping[f"{filename}.json"] = name
    
    return index_mapping


# Load the mapping when module is imported
INDEX_MAPPING = load_index_mapping()

# Reverse mapping for convenience
DISPLAY_NAME_TO_FILE = {v: k for k, v in INDEX_MAPPING.items()}
