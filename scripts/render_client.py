"""Local template adapter; shared resources are data, never executable code."""
import json,re
from shared_data import require,json_bytes,records,digest,deterministic_zip

def render(root,client,payload,contract):
    data=payload["platforms"][client]
    require(data['providers']==contract['providers'], 'Provider/order contract changed; update local overlay deliberately')
    require(data['guard']==json.loads((root/'config/bootstrap.json').read_text(encoding='utf-8')), 'Local guard contract changed')
    require(set(data['rules'])=={d['id'] for d in data['providers']}|{'apple_domains','proxy_domains','china_domains'},'Resource inventory changed')
    template=(root/'config/override.js').read_text(encoding='utf-8')
    for marker in ('__PROVIDERS_JSON__','__BASELINE_JSON__'): require(template.count(marker)==1,'Invalid adapter marker')
    files={'rules/'+name+'.list':text.encode() for name,text in data['rules'].items()}
    files['override.js']=template.replace('__PROVIDERS_JSON__',json.dumps(data['providers'])).replace(
        '__BASELINE_JSON__',json.dumps(data['guard']['rules'][:-1])).encode()
    files['guard.yaml']=json_bytes(data['guard'])
    return files

def bundle_clash(root, files, metadata):
    bundle={'guard.yaml':files['guard.yaml'],'override.js':files['override.js'],
            'INSTALL.md':files['INSTALL.md'],'THIRD_PARTY.md':files['THIRD_PARTY.md'],
            'LICENSE':(root/'LICENSE').read_bytes()}
    bundle.update({p:d for p,d in files.items() if p.startswith('licenses/')})
    bundle.update({'ruleset/personal-clash/'+p.removeprefix('rules/'):d for p,d in files.items() if p.startswith('rules/')})
    bundle['bundle-manifest.json']=json_bytes({'schema_version':1,'shared_version':metadata['shared_version'],
        'repository':'SHIKI1255/clash-config','providers':metadata['providers'],
        'files':{p:digest(d) for p,d in bundle.items()}})
    return deterministic_zip(bundle)
