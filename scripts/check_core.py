"""Isolated native parser/cache checks using synthetic DIRECT-only fixtures.

No real nodes, traffic interception, system proxy changes or existing cache writes.
Python standard library. Node.js and a separately supplied Mihomo binary required.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request

from build import require, records


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def run(binary: Path, release: Path, geodata: Path, output: Path):
    require(not output.exists(), 'Native test directory must be new')
    output.mkdir(parents=True)
    shutil.copy2(geodata, output/'geosite.dat')
    for name in ('Country.mmdb', 'ASN.mmdb'):
        source = geodata.parent/name
        require(source.is_file(), 'Native fixture requires explicit ' + name)
        shutil.copy2(source, output/name)
    shutil.copytree(release/'rules', output/'ruleset/personal-clash')
    fixture = {'proxies': [], 'proxy-groups': [{'name': 'Fixture', 'type': 'select', 'proxies': ['DIRECT']}],
               'rules': ['MATCH,DIRECT'], 'ipv6': False}
    js = "const fs=require('fs'),vm=require('vm');const x=JSON.parse(fs.readFileSync(0,'utf8'));const c={config:x.config};vm.createContext(c);vm.runInContext(x.code+';result=main(config,\"Fixture\")',c,{timeout:2000});process.stdout.write(JSON.stringify(c.result));"
    result = subprocess.run(['node', '-e', js], input=json.dumps({'config': fixture, 'code': (release/'override.js').read_text(encoding='utf-8')}),
                            capture_output=True, text=True, encoding='utf-8', check=True)
    config = json.loads(result.stdout)
    port = free_port()
    config.update({'external-controller': f'127.0.0.1:{port}', 'secret': 'isolated-test-only',
                   'mode': 'rule', 'log-level': 'info', 'geo-auto-update': False,
                   'mixed-port': 0, 'port': 0, 'socks-port': 0, 'redir-port': 0, 'tproxy-port': 0,
                   'tun': {'enable': False}})
    config['dns']['listen'] = ''
    # Always fail downloads locally. Cached files must still parse, including empty
    # resources after cross-source dedup. No connection to production proxy groups.
    for provider in config['rule-providers'].values():
        provider['url'] = 'http://127.0.0.1:9/unavailable'
    config_path = output/'fixture.json'
    config_path.write_text(json.dumps(config, ensure_ascii=False), encoding='utf-8')
    checked = subprocess.run([str(binary), '-t', '-d', str(output), '-f', str(config_path)], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
    (output/'syntax.log').write_text(checked.stdout+checked.stderr, encoding='utf-8')
    require(checked.returncode == 0, 'Native fixture syntax failed; see isolated log')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def api(path, method='GET'):
        request = urllib.request.Request(f'http://127.0.0.1:{port}'+path, method=method,
                                         headers={'Authorization': 'Bearer isolated-test-only'})
        with opener.open(request, timeout=4) as response:
            data = response.read()
            return json.loads(data) if data else None
    with (output/'runtime.log').open('w', encoding='utf-8') as log:
        process = subprocess.Popen([str(binary), '-d', str(output), '-f', str(config_path)], stdout=log, stderr=log)
        try:
            expected = {'shiki_'+name: count for name,count in json.loads((release/'manifest.json').read_text())['providers'].items()}
            actual = {}
            deadline = time.monotonic()+25
            while time.monotonic() < deadline:
                require(process.poll() is None, 'Native fixture exited unexpectedly')
                try:
                    actual = {k: v['ruleCount'] for k,v in api('/providers/rules')['providers'].items()}
                    if actual == expected: break
                except (OSError, KeyError): pass
                time.sleep(.2)
            require(actual == expected, f'Native parser silently skipped/failed rules: {actual} != {expected}')
            for provider in ['shiki_personal_direct']:
                try: api('/providers/rules/'+provider, 'PUT')
                except urllib.error.HTTPError: pass
            after = {k: v['ruleCount'] for k,v in api('/providers/rules')['providers'].items()}
            require(after == expected, 'Download failure lost valid cached rules')
            # Delete no user caches: a new intentionally absent test path is passed
            # through the native API config reload using this isolated process only.
            missing = json.loads(json.dumps(config))
            victim = 'shiki_personal_direct'
            missing['rule-providers'][victim]['path'] = './never-created.list'
            missing['rule-providers'][victim]['url'] += '/fresh'
            fresh = output/'missing-cache.json'
            fresh.write_text(json.dumps(missing), encoding='utf-8')
            request = urllib.request.Request(f'http://127.0.0.1:{port}/configs?force=true',
                data=json.dumps({'path': str(fresh)}).encode(), method='PUT',
                headers={'Authorization': 'Bearer isolated-test-only', 'Content-Type': 'application/json'})
            with opener.open(request, timeout=15) as response: response.read()
            missing_count = api('/providers/rules')['providers'][victim]['ruleCount']
            require(missing_count == 0, 'Unexpected first-download failure behavior')
            report = {'native_rules': sum(expected.values()), 'providers': len(expected),
                      'all_cached_rules_parsed': True, 'failed_download_retains_cache': True,
                      'no_cache_failed_download_rule_count': missing_count,
                      'no_cache_is_not_accepted_installation': True, 'no_real_nodes_or_interception': True}
        finally:
            process.terminate()
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=5)
    (output/'native-validation.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['binary','release','geodata','output']: parser.add_argument('--'+name, type=Path, required=True)
    args=parser.parse_args()
    print(json.dumps(run(args.binary.resolve(), args.release.resolve(), args.geodata.resolve(), args.output.resolve())))
