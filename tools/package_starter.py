#!/usr/bin/env python3
"""Build or verify a deterministic, self-contained starter ZIP. No remote writes."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import stat
import zipfile
from validate_plan import ROOT, files, validate_package, read

def verify(archive):
    with zipfile.ZipFile(archive) as z:
        names=z.namelist()
        if len(names)!=len(set(names)):raise ValueError('Duplicate ZIP members')
        if any(PurePosixPath(n).is_absolute() or '..' in PurePosixPath(n).parts for n in names):raise ValueError('Unsafe ZIP member')
        manifests=[n for n in names if n.count('/')==1 and n.endswith('/MANIFEST.json')]
        if len(manifests)!=1:raise ValueError('Expected one root manifest')
        prefix=manifests[0].split('/')[0]+'/'
        manifest=json.loads(z.read(manifests[0]))
        expected={prefix+f['path'] for f in manifest['files']}|{manifests[0]}
        if set(names)!=expected:raise ValueError('ZIP membership differs from manifest')
        for f in manifest['files']:
            b=z.read(prefix+f['path'])
            if len(b)!=f['bytes'] or hashlib.sha256(b).hexdigest()!=f['sha256']:raise ValueError('Digest mismatch: '+f['path'])
    return {'status':'archive_verified','files':len(names),'sha256':hashlib.sha256(Path(archive).read_bytes()).hexdigest()}

def build(root,output):
    errors=validate_package(root)
    if errors:raise ValueError('Package invalid: '+json.dumps(errors,ensure_ascii=False))
    data=read(root,'coordination/tasks.json');name='menubar-agent-starter-v'+data['schema_version']
    manifest={'package':name,'created_on':data['created_on'],'status':'offline_planning_not_deployed','self_excluded':True,'files':[]}
    for p in files(root):
        rel=p.relative_to(root).as_posix()
        if rel=='MANIFEST.json':continue
        if p.is_symlink():raise ValueError('Symlink not included: '+rel)
        b=p.read_bytes();manifest['files'].append({'path':rel,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
    (root/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    output.parent.mkdir(parents=True,exist_ok=True)
    date=tuple(map(int,data['created_on'].split('-')))+(0,0,0)
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in files(root):
            rel=p.relative_to(root).as_posix();info=zipfile.ZipInfo(name+'/'+rel,date_time=date)
            info.create_system=3;info.external_attr=((stat.S_IFREG | (p.stat().st_mode & 0o777))<<16)
            info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    return verify(output)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT)
    mode=parser.add_mutually_exclusive_group(required=True);mode.add_argument('--output',type=Path);mode.add_argument('--verify',type=Path)
    args=parser.parse_args()
    try:result=verify(args.verify) if args.verify else build(args.root,args.output)
    except (ValueError,OSError,KeyError,zipfile.BadZipFile) as e:
        print(json.dumps({'status':'invalid','error':str(e)},ensure_ascii=False));return 1
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0

if __name__=='__main__':raise SystemExit(main())
