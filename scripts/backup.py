"""Consistent local backup: briefly stop writers, save DB + sources, resume writers."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def run(*args):
    return subprocess.run(['docker','compose',*args],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout


def main():
    directory=Path('data/backups') / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    directory.mkdir(parents=True,exist_ok=False)
    running=run('ps','--services','--status','running').decode().splitlines()
    writers=[name for name in ('api','worker') if name in running]
    try:
        if writers: run('stop',*writers)
        database=run('exec','-T','postgres','pg_dump','-U','padayon','-d','padayon','-Fc')
        sources=run('run','--rm','--no-deps','--entrypoint','python','api','-c',
            "import sys,tarfile; t=tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz'); t.add('/app/data/uploads',arcname='uploads'); t.close()")
        (directory/'database.dump').write_bytes(database)
        (directory/'sources.tar.gz').write_bytes(sources)
        manifest={name:hashlib.sha256((directory/name).read_bytes()).hexdigest() for name in ('database.dump','sources.tar.gz')}
        (directory/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        print('Backup completed:',directory)
        return directory
    finally:
        if writers: run('start',*writers)


if __name__=='__main__':main()
