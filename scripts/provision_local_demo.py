"""Host-only helper; store a local user's token without printing the secret."""
import json
import subprocess
from pathlib import Path


def main():
    path = Path('data/local-demo.json')
    if path.exists():
        raise SystemExit('data/local-demo.json already exists; re-use that token.')
    result = subprocess.run(['docker', 'compose', 'exec', '-T', 'api', 'python', '-m',
                             'scripts.create_user', '--name', 'BlueStudy Local Demo'],
                            check=True, capture_output=True, text=True, encoding='utf-8')
    credentials = json.loads(result.stdout)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(credentials, indent=2), encoding='utf-8')
    print('Created local demo credentials at data/local-demo.json (gitignored).')


if __name__ == '__main__':
    main()
