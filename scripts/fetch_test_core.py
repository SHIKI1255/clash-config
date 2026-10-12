"""Fetch the fixed native CI checker and a hash-verified current DNS test database.

Only CI's temporary directory is written. Neither binary nor database is published.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import urllib.request
from build import fetch, require

CORE_URL = 'https://github.com/MetaCubeX/mihomo/releases/download/v1.19.32/mihomo-linux-amd64-v1.19.32.gz'
CORE_SHA = '8451100836c9eda194331c2babfad490b2faf30cebc1a04b0e76fd8ac2d35d10'

def download(url, expected):
    with urllib.request.urlopen(url, timeout=60) as response:
        data=response.read(64*1024*1024+1)
    require(len(data)<=64*1024*1024, 'Native CI download too large')
    require(hashlib.sha256(data).hexdigest()==expected, 'Native CI download hash mismatch')
    return data

def main(output):
    require(not output.exists(), 'CI tools directory must be new')
    release=json.loads(fetch('https://api.github.com/repos/MetaCubeX/meta-rules-dat/releases/tags/latest'))
    asset=next(x for x in release['assets'] if x['name']=='geosite.dat')
    require(asset['browser_download_url']=='https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geosite.dat', 'Unexpected geosite asset')
    require(asset['digest'].startswith('sha256:'), 'Missing database download hash')
    core=gzip.decompress(download(CORE_URL, CORE_SHA))
    data=download(asset['browser_download_url'],asset['digest'].split(':',1)[1])
    output.mkdir(parents=True)
    (output/'mihomo').write_bytes(core); (output/'mihomo').chmod(0o700)
    (output/'geosite.dat').write_bytes(data)
    (output/'test-inputs.json').write_text(json.dumps({'core_version':'1.19.32','core_archive_sha256':CORE_SHA,
        'geosite_sha256':asset['digest'],'geosite_release_id':release['id']},indent=2)+'\n')
    print('Native checker downloaded and hashes verified')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--output',type=Path,required=True)
    main(parser.parse_args().output.resolve())
