from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/companion'))
import backup_control as ctl
from backup_service import Store

with TemporaryDirectory() as folder:
    root = Path(folder)
    store = Store(root)
    ctl.ROOT = root
    ctl.ensure = lambda: None
    ctl.request = lambda path, payload: {'records': store.merge(payload['records'])}
    original = dict(id='101', title='Original', hidden=True, updatedAt=1)
    store.merge([original])
    incoming = root / 'import.json'
    incoming.write_text(json.dumps({'schemaVersion': 1, 'hiddenIds': ['202']}))
    ctl.restore(incoming)
    assert {r['id'] for r in store.records.values() if r['hidden']} == {'101', '202'}
    ctl.restore(incoming, replace=True)
    assert {r['id'] for r in store.records.values() if r['hidden']} == {'202'}
    store.merge([original])
    assert not store.records['101']['hidden']
    backup = next((root / 'restore-backups').glob('*.json'))
    assert {r['id'] for r in json.loads(backup.read_text())['wallpapers']} == {'101', '202'}
    incoming.write_text('{')
    before = dict(store.records)
    try:
        ctl.restore(incoming, replace=True)
    except ValueError:
        pass
    else:
        raise AssertionError('Malformed list accepted')
    assert store.records == before
    incoming.write_text(json.dumps({'schemaVersion': 1, 'hiddenIds': []}))
    ctl.restore(incoming, replace=True)
    assert not any(r['hidden'] for r in store.records.values())
print('PASS: explicit merge/replacement, pre-restore backup, stale-cache protection, validation before writes')
