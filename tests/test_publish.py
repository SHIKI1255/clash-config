import base64
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import build as b
import publish as p

ENV={'GITHUB_REPOSITORY':b.REPOSITORY,'GITHUB_REF':'refs/heads/main',
     'GITHUB_EVENT_NAME':'push','GITHUB_SHA':'a'*40}

class Publication(unittest.TestCase):
    def fixture(self, path):
        files={'override.js':b'fixture', 'guard.yaml':b'{}', 'clash-overlay.zip':b'PK\x03\x04\xff\x00',
               'sources.lock.json':b'{}','source_stats.json':b'{}','THIRD_PARTY.md':b'test',
               'manifest.json':b.json_bytes({'config_sha256':b.digest(b'fixture'),'source_files_sha256':{}})}
        files['SHA256SUMS']=b.checksum_files(files)
        for name,data in files.items(): (path/name).write_bytes(data)
        return files

    def test_hash_corruption_and_extra_file_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp); files=self.fixture(path)
            self.assertEqual(p.verified_files(path),files)
            (path/'clash-overlay.zip').write_bytes(b'bad')
            with self.assertRaises(b.BuildError): p.verified_files(path)
            self.fixture(path); (path/'private.yaml').write_text('do not publish')
            with self.assertRaises(b.BuildError): p.verified_files(path)

    def fake_api(self, *, advance=False):
        calls=[]; reads=0
        def api(path,payload=None,method=None,missing_ok=False):
            nonlocal reads
            calls.append((path,payload,method))
            if path=='git/ref/heads/main':
                reads+=1
                return {'object':{'sha':('b' if advance and reads>1 else 'a')*40}}
            if path=='git/ref/heads/release':
                return None if missing_ok else {'object':{'sha':'c'*40}}
            if path=='git/blobs': return {'sha':'d'*40}
            if path=='git/trees': return {'sha':'e'*40}
            if path=='git/commits': return {'sha':'c'*40}
            if path=='git/refs': return {}
            raise AssertionError(path)
        return api,calls

    def test_binary_zip_published_as_base64_and_readback(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ,ENV):
            path=Path(tmp); files=self.fixture(path); api,calls=self.fake_api()
            with patch('publish.api',side_effect=api): self.assertEqual(p.publish(path)['status'],'published')
            blob=next(payload for target,payload,_ in calls if target=='git/blobs')
            self.assertEqual(base64.b64decode(blob['content']),files['clash-overlay.zip'])
            self.assertEqual(blob['encoding'],'base64')

    def test_concurrent_main_advance_cannot_move_release(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ,ENV):
            path=Path(tmp); self.fixture(path); api,calls=self.fake_api(advance=True)
            with patch('publish.api',side_effect=api):
                with self.assertRaises(b.BuildError): p.publish(path)
            self.assertFalse(any(target.startswith('git/refs') for target,_,_ in calls))

    def test_pr_never_publishes(self):
        with patch.dict(os.environ,ENV|{'GITHUB_EVENT_NAME':'pull_request'}),patch('publish.api') as api:
            with self.assertRaises(b.BuildError): p.publish(Path('unused'))
            api.assert_not_called()

    def test_unregistered_policy_conflict_stops(self):
        _,conflicts,_=b.merge_rules([b.parse_rule('DOMAIN,a.example,DIRECT'),b.parse_rule('DOMAIN,a.example,PROXY')])
        with self.assertRaises(b.BuildError): b.check_conflicts(conflicts,[])

if __name__=='__main__': unittest.main()
