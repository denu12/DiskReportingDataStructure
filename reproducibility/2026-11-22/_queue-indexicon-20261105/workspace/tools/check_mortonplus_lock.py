"""Check that the validated 2D MortonPlus release is unchanged."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
lock=json.loads((root/'config/mortonplus-2d-lock.json').read_text())
actual=hashlib.sha256((root/lock['file']).read_bytes()).hexdigest()
if actual!=lock['sha256']:
    raise SystemExit('Frozen 2D MortonPlus changed; version and validate a new release explicitly.')
print('Frozen 2D MortonPlus verified: '+lock['version'])
