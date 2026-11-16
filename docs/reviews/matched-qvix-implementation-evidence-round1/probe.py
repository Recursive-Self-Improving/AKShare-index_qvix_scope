"""Offline review probes; writes only beneath its own evidence directory."""
import copy
import json
import re
import runpy
import shutil
from pathlib import Path

import pytest

from app.chart import build
from app.core import QVIX_FEEDS, dump, load_manifest
from app.fetch import group_worker, promote, recover_group, state_after
from app.verify import verify

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).resolve().parent
helpers = runpy.run_path(str(ROOT / 'tests/test_contracts.py'))

# Native v4 completion is the immutable origin: remove required snapshot times
# there, rather than merely changing a manifest copy against its unchanged hash.
root = EVIDENCE / 'native-missing-times'
root.mkdir()
directory = helpers['group_fixture'](root)
mp = pytest.MonkeyPatch()
try:
    helpers['install_http'](mp, helpers['source']([('2024/1/2', [1, 2, 0, 1])]))
    group_worker(directory)
finally:
    mp.undo()
feed = 'qvix_50etf'
record = directory / feed / 'result.json'
result = json.loads(record.read_text())
for key in ('successful_at', 'finished_at'):
    del result[key]
dump(record, result)
recovered = recover_group(root, directory)
print('missing_times_recovery:', recovered[feed]['status'],
      {k: k in recovered[feed] for k in ('attempted_at', 'successful_at', 'finished_at')})
manifest = helpers['empty_manifest']()
for member, value in recovered.items():
    manifest['feeds'][member] = state_after({}, value)
promote(root, manifest)
print('missing_times_promotion: ACCEPTED')
try:
    build(root, root / 'report.html')
except KeyError as error:
    print('missing_times_chart:', type(error).__name__, str(error))

# Hidden ancestor, without altering the actual paragraph, payload or arrays.
original = (ROOT / 'report.html').read_text()
identity = 'qvix-status-sh000300-qvix_300index'
pattern = rf'<p class="quality" id="{identity}">.*?</p>'
modified, count = re.subn(pattern, lambda m: '<div hidden>' + m[0] + '</div>', original)
assert count == 1
report = EVIDENCE / 'hidden-ancestor.html'
report.write_text(modified)
verify(ROOT / 'data', report)
print('hidden_ancestor_verification: ACCEPTED')

# A second native refresh with failed shared load preserves only each feed's
# complete own prior; subsequent fresh blank evidence replaces all old closes.
transition_root = EVIDENCE / 'native-transitions'
transition_root.mkdir()
prior = None
for name, records, failure in [
    ('populated', [('2024/1/2', [1, 2, 0, 1])], False),
    ('failed', None, True),
    ('blank', [('2024/1/2', [''] * 4)], False),
    ('corrected', [('2024/1/2', [2, 3, 1, 2])], False),
]:
    stage = transition_root / name
    stage.mkdir()
    member_dir = helpers['group_fixture'](stage)
    mp = pytest.MonkeyPatch()
    try:
        helpers['install_http'](mp, helpers['source'](records) if records else None, failure=failure)
        group_worker(member_dir)
    finally:
        mp.undo()
    results = recover_group(stage, member_dir)
    states = {f: state_after(prior[f] if prior else {}, results[f]) for f in QVIX_FEEDS}
    if failure:
        assert all(states[f]['snapshot'] == prior[f]['snapshot'] and states[f]['stale_reuse']
                   for f in QVIX_FEEDS)
    else:
        assert all(states[f]['snapshot'] == results[f] and not states[f]['stale_reuse'] for f in QVIX_FEEDS)
        if name == 'blank':
            assert all(states[f]['snapshot']['accounting']['full']['close_range'] is None for f in QVIX_FEEDS)
    print('native_transition:', name, {f: (s['attempt']['status'], s['stale_reuse']) for f, s in states.items()})
    prior = copy.deepcopy(states)

migration = load_manifest(ROOT / 'data')
assert migration['schema'] == 'qvix-comparison-v4'
print('probe_complete')
shutil.rmtree(root)
shutil.rmtree(transition_root)
report.unlink()
