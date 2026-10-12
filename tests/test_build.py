import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build as b


class Rules(unittest.TestCase):
    def test_native_regex_kept(self):
        rules, _ = b.parse_source({'id': 'openai', 'format': 'v2fly', 'policy': 'PROXY'},
                                 b'regexp:^chatgpt-async-\\S+-\\d+\\.azure\\.com$\n')
        self.assertEqual(rules[0].kind, 'DOMAIN-REGEX')
        self.assertEqual(b.route(rules, domain='chatgpt-async-east-1.azure.com')['policy'], 'PROXY')

    def test_unknown_syntax_stops(self):
        for line in ['USER-AGENT,Clash,DIRECT', 'UNKNOWN,test,PROXY', 'DOMAIN,x.com,GLOBAL', 'IP-CIDR,1.2.3.4/24,DIRECT']:
            with self.subTest(line=line), self.assertRaises(b.BuildError): b.parse_rule(line)

    def test_unknown_v2fly_stops(self):
        for line in [b'include:unknown\n', b'example.org @unexpected\n']:
            with self.assertRaises(b.BuildError): b.parse_source({'id':'test','format':'v2fly','policy':'PROXY'},line)

    def test_ads_not_added(self):
        r, s = b.parse_source({'id':'test','format':'v2fly','policy':'PROXY'},b'example.org\nad.example @ads\n')
        self.assertEqual(len(r),1); self.assertEqual(len(s['skipped']),1)

    def test_duplicates_and_conflicts(self):
        inputs=[b.parse_rule('DOMAIN,a.com,PROXY',source='a'),b.parse_rule('DOMAIN,a.com,PROXY',source='b'),b.parse_rule('DOMAIN,a.com,DIRECT',source='c')]
        rules, conflicts, n = b.merge_rules(inputs)
        self.assertEqual(n,1); self.assertEqual(len(rules),2)
        self.assertEqual(b.route(rules,domain='a.com')['policy'],'PROXY')
        with self.assertRaises(b.BuildError): b.check_conflicts(conflicts,[])
        b.check_conflicts(conflicts,conflicts)

    def test_no_suffix_subsumption_dedup(self):
        r,_,n=b.merge_rules([b.parse_rule('DOMAIN-SUFFIX,a.com,PROXY'),b.parse_rule('DOMAIN,x.a.com,PROXY')])
        self.assertEqual(len(r),2); self.assertEqual(n,0)

    def test_expected_rule_catches_broad_same_policy(self):
        actual=b.route([b.parse_rule('DOMAIN-SUFFIX,workos.com,PROXY')],domain='cdn.workos.com')
        with self.assertRaises(b.BuildError):b.check_case_result({'name':'endpoint','policy':'PROXY','expected_rule':'DOMAIN,cdn.workos.com,PROXY'},actual)

    def test_changed_precedence_stops(self):
        r=[b.parse_rule('DOMAIN-SUFFIX,microsoft.com,DIRECT'),b.parse_rule('DOMAIN,copilot.microsoft.com,PROXY')]
        with self.assertRaises(b.BuildError):b.check_cases(r,[{'name':'copilot','input':{'domain':'copilot.microsoft.com'},'policy':'PROXY'}])

    def test_dns_unknown_does_not_claim_proxy(self):
        self.assertEqual(b.route([b.parse_rule('GEOIP,CN,DIRECT'),b.parse_rule('MATCH,PROXY')],domain='unknown.example')['policy'],'UNRESOLVED')

    def test_process_selector(self):
        r=[b.parse_rule('PROCESS-NAME,GameViewer.exe,DIRECT'),b.parse_rule('MATCH,PROXY')]
        self.assertEqual(b.route(r,process='GameViewer.exe')['policy'],'DIRECT')
        self.assertEqual(b.route(r,process='Other.exe')['policy'],'PROXY')

    def test_quantity_change_stops(self):
        conf=b.load_config(b.ROOT)
        for count in [1,151]:
            with self.assertRaises(b.BuildError):b.check_limits({'a':{'raw_count':count,'retained_count':count}}, {'a':{'raw_count':100,'retained_count':100}},conf['limits'])

    def test_same_count_replacement_stops(self):
        limits=b.load_config(b.ROOT)['limits']
        with self.assertRaises(b.BuildError):b.check_limits({'a':{'raw_count':1,'retained_count':1,'rules':['new']}},{'a':{'raw_count':1,'retained_count':1,'rules':['old']}},limits)

    def test_download_failure_stops(self):
        with patch('urllib.request.urlopen',side_effect=OSError('offline')),self.assertRaises(b.BuildError):b.fetch('https://openai.com/chatgpt-voice.json')

    def test_private_source_url_rejected(self):
        for url in ['https://example.com/token','https://raw.githubusercontent.com/a?token=secret','http://openai.com/voice']:
            with self.assertRaises(b.BuildError):b.fetch(url)

    def test_zip_reproducible(self):
        a=b.deterministic_zip({'rules/a.list':b'DOMAIN,a.com\n','guard.yaml':b'{}'})
        self.assertEqual(a,b.deterministic_zip({'guard.yaml':b'{}','rules/a.list':b'DOMAIN,a.com\n'}))
        with zipfile.ZipFile(io.BytesIO(a)) as z:self.assertIsNone(z.testzip())

    def test_replay_tamper_rejected(self):
        conf={'sources':[{'id':'x'}],'repositories':{}}
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'snapshots').mkdir();(p/'snapshots/x.txt').write_bytes(b'tampered')
            (p/'sources.lock.json').write_text(json.dumps({'schema_version':1,'files':{'snapshots/x.txt':{'sha256':b.digest(b'original')}}}))
            with self.assertRaises(b.BuildError):b.replay(conf,p)

    def test_node_adapter_and_failure_guards(self):
        r=subprocess.run(['node',str(b.ROOT/'tests/test_adapter.js')],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)


if __name__=='__main__':unittest.main()
