"""Restore into a unique temporary DB, verify source hashes, then remove only that DB."""
import argparse
import hashlib
import json
import re
import subprocess
import tarfile
from pathlib import Path
from uuid import uuid4


def command(*args,input=None):
    return subprocess.run(['docker','compose','exec','-T','postgres',*args],input=input,
        check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout


def main(directory=None):
    if directory is None:
        parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path);directory=parser.parse_args().directory
    manifest=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
    for name in ('database.dump','sources.tar.gz'):
        if hashlib.sha256((directory/name).read_bytes()).hexdigest()!=manifest[name]:
            raise SystemExit('Backup checksum mismatch')
    database='padayon_restore_'+uuid4().hex
    assert re.fullmatch(r'padayon_restore_[0-9a-f]{32}',database)
    created=False
    try:
        command('createdb','-U','padayon',database);created=True
        command('pg_restore','-U','padayon','-d',database,'--exit-on-error',input=(directory/'database.dump').read_bytes())
        data=command('psql','-U','padayon','-d',database,'-At','-c',
            "SELECT source_key || '|' || sha256 FROM documents").decode().splitlines()
        with tarfile.open(directory/'sources.tar.gz','r:gz') as archive:
            for row in data:
                name,expected=row.split('|')
                member=archive.extractfile('uploads/'+name)
                if member is None or hashlib.sha256(member.read()).hexdigest()!=expected:
                    raise SystemExit('Restored source checksum mismatch')
        version=command('psql','-U','padayon','-d',database,'-At','-c','SELECT version_num FROM alembic_version').decode().strip()
        print('Restore verified:',len(data),'source documents; schema',version)
    finally:
        if created: command('dropdb','-U','padayon',database)


if __name__=='__main__':main()
