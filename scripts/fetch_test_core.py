"""Fetch the latest stable Mihomo checker (>=1.19.33) and hash-verified DNS test databases.

Only CI's temporary directory is written. Neither binary nor database is published.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import platform
import re
import sys
import urllib.request
from build import fetch, require
from public_http import request_bytes

MIN_CORE_VERSION = (1, 19, 33)
CORE_RELEASE_API = 'https://api.github.com/repos/MetaCubeX/mihomo/releases/latest'
PLATFORM_SLUGS = {
    ('linux', 'x86_64'): 'linux-amd64',
    ('darwin', 'arm64'): 'darwin-arm64',
}


def parse_core_version(tag: str) -> tuple[int, int, int]:
    match = re.fullmatch(r'v(\d+)\.(\d+)\.(\d+)', tag or '')
    require(match is not None, f'Unexpected non-stable Mihomo tag: {tag!r}')
    return tuple(int(part) for part in match.groups())


def select_core_asset(release: dict, system: str | None = None, machine: str | None = None) -> tuple[str, str, str]:
    require(isinstance(release, dict) and not release.get('draft') and not release.get('prerelease'),
            'Mihomo release must be a published stable release')
    tag = release.get('tag_name', '')
    version = parse_core_version(tag)
    require(version >= MIN_CORE_VERSION,
            f'Mihomo version {tag} is below minimum {MIN_CORE_VERSION[0]}.{MIN_CORE_VERSION[1]}.{MIN_CORE_VERSION[2]}')
    os_name = (sys.platform if system is None else system).lower()
    if os_name.startswith('linux'):
        os_name = 'linux'
    arch = (platform.machine() if machine is None else machine).lower()
    arch = {'amd64': 'x86_64', 'aarch64': 'arm64'}.get(arch, arch)
    slug = PLATFORM_SLUGS.get((os_name, arch))
    require(slug is not None, f'Unsupported native checker platform: {os_name}/{arch}')
    name = f'mihomo-{slug}-{tag}.gz'
    asset = next((x for x in release.get('assets', []) if x.get('name') == name), None)
    require(asset is not None, f'Missing Mihomo asset: {name}')
    expected_url = f'https://github.com/MetaCubeX/mihomo/releases/download/{tag}/{name}'
    require(asset.get('browser_download_url') == expected_url, 'Unexpected Mihomo asset URL')
    digest_value = asset.get('digest', '')
    require(isinstance(digest_value, str) and re.fullmatch(r'sha256:[0-9a-f]{64}', digest_value),
            'Missing or invalid Mihomo download hash')
    return tag.lstrip('v'), expected_url, digest_value.split(':', 1)[1]


def download(url, expected):
    data = request_bytes(urllib.request.Request(url), limit=64*1024*1024, timeout=60)
    require(len(data)<=64*1024*1024, 'Native CI download too large')
    require(hashlib.sha256(data).hexdigest()==expected, 'Native CI download hash mismatch')
    return data


def main(output):
    require(not output.exists(), 'CI tools directory must be new')
    core_release = json.loads(fetch(CORE_RELEASE_API))
    core_version, core_url, core_sha = select_core_asset(core_release)
    release = json.loads(fetch('https://api.github.com/repos/MetaCubeX/meta-rules-dat/releases/tags/latest'))
    core = gzip.decompress(download(core_url, core_sha))
    databases = {}
    hashes = {}
    for target, name in [('geosite.dat','geosite.dat'),('Country.mmdb','geoip.metadb'),('ASN.mmdb','GeoLite2-ASN.mmdb')]:
        asset = next(x for x in release['assets'] if x['name']==name)
        require(asset['browser_download_url']=='https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/'+name, 'Unexpected database asset')
        require(asset['digest'].startswith('sha256:'), 'Missing database download hash')
        databases[target] = download(asset['browser_download_url'], asset['digest'].split(':',1)[1])
        hashes[target] = asset['digest']
    output.mkdir(parents=True)
    (output/'mihomo').write_bytes(core); (output/'mihomo').chmod(0o700)
    for name, data in databases.items(): (output/name).write_bytes(data)
    min_ver = '.'.join(map(str, MIN_CORE_VERSION))
    (output/'test-inputs.json').write_text(json.dumps({
        'core_version': core_version, 'min_core_version': min_ver, 'core_url': core_url,
        'core_archive_sha256': core_sha, 'core_release_id': core_release.get('id'),
        'database_sha256': hashes, 'database_release_id': release['id']}, indent=2)+'\n')
    print(f'Native checker Mihomo v{core_version} downloaded and hashes verified')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--output',type=Path,required=True)
    main(parser.parse_args().output.resolve())
