import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import build as b
import shared_data as d
import render_client as r


def package():
    payload={'schema_version':1,'categories':{'local_direct':'Local'},'licenses':{},
             'platforms':{c:{} for c in ('shadowrocket','quantumultx','clash')}}
    data=d.json_bytes(payload)
    basis={'schema_version':1,'bundle_sha256':d.digest(data),'source_files_sha256':{},'upstreams':{},'provenance_sha256':'0'*64}
    return {**basis,'shared_version':d.digest(d.json_bytes(basis))},data


class DataTransport(unittest.TestCase):
    def test_schema_hash_version_and_inventory(self):
        m,data=package()
        d.verify(d.json_bytes(m),data)
        for changed in [{**m,'schema_version':999},{**m,'bundle_sha256':'0'*64},{**m,'shared_version':'0'*64}]:
            with self.assertRaises(d.BuildError):d.verify(d.json_bytes(changed),data)
        with self.assertRaises(d.BuildError):d.verify(d.json_bytes(m),data+b' ')

    def test_download_failure_is_not_empty_success(self):
        with patch('urllib.request.urlopen',side_effect=OSError('offline')),self.assertRaises(d.BuildError):
            d.fetch('https://raw.githubusercontent.com/SHIKI1255/shadowrocket-config/release/shared/bundle.json')

    def test_unapproved_or_credential_urls_stop(self):
        for url in ['http://api.github.com/x','https://example.org/file','https://user:password@api.github.com/x','https://api.github.com/x?token=test']:
            with self.assertRaises(d.BuildError):d.fetch(url)

    def test_replay_hash_tampering_stops(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'shared').mkdir();m,data=package()
            (p/'shared/manifest.json').write_bytes(d.json_bytes(m));(p/'shared/bundle.json').write_bytes(data)
            one=d.load(p);self.assertEqual(one[0]['shared_version'],m['shared_version'])
            (p/'shared/bundle.json').write_bytes(data+b' ')
            with self.assertRaises(d.BuildError):d.load(p)

    def test_download_uses_one_immutable_revision(self):
        m,data=package();seen=[]
        def fake(url):
            seen.append(url)
            if '/git/ref/' in url:return d.json_bytes({'object':{'sha':'a'*40}})
            return d.json_bytes(m) if url.endswith('manifest.json') else data
        with patch('shared_data.fetch',side_effect=fake):d.load()
        self.assertEqual(sum('/git/ref/' in s for s in seen),1)
        self.assertTrue(all('/'+'a'*40+'/' in s for s in seen if '/git/ref/' not in s))

    def test_outputs_cannot_replace_previous_success(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'good').write_text('good')
            with self.assertRaises(d.BuildError):d.write_files(b.ROOT,p,{'bad':b'bad'})
            self.assertEqual((p/'good').read_text(),'good')

    def test_zip_is_deterministic(self):
        self.assertEqual(d.deterministic_zip({'a':b'A','b':b'B'}),d.deterministic_zip({'b':b'B','a':b'A'}))

    def test_no_external_code_loader(self):
        text=(b.ROOT/'scripts/shared_data.py').read_text()
        self.assertNotIn('exec(',text);self.assertNotIn('eval(',text)


@unittest.skipUnless(b.CLIENT=='quantumultx','Quantumult X template')
class QuantumultTemplate(unittest.TestCase):
    def data(self):
        return {'local_rules_text':'host, localhost, direct\n','rules_text':'host-suffix, example.com, proxy\ngeoip, cn, direct\n','report':{}}

    def test_sections_rewrite_and_remote_contract(self):
        base=(b.ROOT/'config/base.conf').read_text(encoding='utf-8');files=r.quantumult(base,self.data())
        self.assertIn(b'[mitm]',files['quantumultx.conf']);self.assertEqual(files['rewrite.list'].count(b'url 302'),2)
        self.assertNotIn(b'^https',files['rewrite.list']);self.assertNotIn(b'url 302',files['quantumultx.conf'])
        for changed in [base.replace('[mitm]\n',''),base.replace('[mitm]\n','[mitm]\nhostname = example.com\n'),
                        base.replace('opt-parser=false','opt-parser=true'),base.replace('inserted-resource=false','force-policy=proxy')]:
            with self.assertRaises(d.BuildError):r.quantumult(changed,self.data())

    def test_network_settings_preserved(self):
        base=(b.ROOT/'config/base.conf').read_text(encoding='utf-8');text=r.quantumult(base,self.data())['quantumultx.conf'].decode()
        for section in ['general','dns','policy','server_remote','server_local']:
            extract=lambda t:t.split('['+section+']\n')[1].split('\n[')[0]
            self.assertEqual(extract(base),extract(text))
        self.assertIn('fallback_udp_policy = reject',text)


@unittest.skipUnless(b.CLIENT=='clash','Clash adapter')
class ClashAdapter(unittest.TestCase):
    def test_adapter_and_guards(self):
        result=subprocess.run(['node',str(b.ROOT/'tests/test_adapter.js')],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_fetch_core_platform_selection(self):
        import fetch_test_core as ftc
        def fake_release(tag='v1.19.34', *, draft=False, prerelease=False, digest_prefix='sha256:'):
            return {'tag_name': tag, 'draft': draft, 'prerelease': prerelease, 'assets': [
                {'name': f'mihomo-{slug}-{tag}.gz',
                 'browser_download_url': f'https://github.com/MetaCubeX/mihomo/releases/download/{tag}/mihomo-{slug}-{tag}.gz',
                 'digest': digest_prefix + ('a' * 64)}
                for slug in ('linux-amd64', 'darwin-arm64')]}
        for os_name, arch, slug in (('linux', 'x86_64', 'linux-amd64'), ('darwin', 'arm64', 'darwin-arm64')):
            ver, url, sha = ftc.select_core_asset(fake_release('v1.19.34'), os_name, arch)
            self.assertEqual(ver, '1.19.34')
            self.assertTrue(url.endswith(f'/mihomo-{slug}-v1.19.34.gz'))
            self.assertEqual(sha, 'a' * 64)
        self.assertEqual(ftc.select_core_asset(fake_release('v1.19.33'), 'darwin', 'arm64')[0], '1.19.33')
        for bad in (
            fake_release('v1.19.32'),
            fake_release('v1.19.35-alpha'),
            fake_release('v1.19.34', prerelease=True),
            fake_release('v1.19.34', draft=True),
            fake_release('v1.19.34', digest_prefix=''),
        ):
            with self.assertRaises(d.BuildError):
                ftc.select_core_asset(bad, 'darwin', 'arm64')
        with self.assertRaises(d.BuildError):
            ftc.select_core_asset(fake_release('v1.19.34'), 'win32', 'x86_64')
