"""Resolve versioned campaign definitions through theater membership."""
import json
from pathlib import Path


def theater_manifests(base):
    base = Path(base)
    for path in sorted((base/'theaters').glob('*/theater.json')):
        yield path, json.loads(path.read_text(encoding='utf-8-sig'))


def campaign_directory(base, name):
    base = Path(base)
    if Path(name).name != name or name in ['', '.', '..']:
        raise ValueError('Invalid campaign ID')
    matches = [path.parent/'campaigns'/name for path, spec in theater_manifests(base)
               if name in spec['campaigns']]
    if len(matches) > 1:
        raise ValueError('Campaign belongs to multiple theaters: '+name)
    if not matches:
        raise ValueError('Unknown active campaign: '+name)
    return matches[0]
