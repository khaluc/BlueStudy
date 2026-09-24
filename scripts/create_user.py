"""Local operator provisioning. Token is shown once; only its hash is stored."""
import argparse
import json
from apps.api.config import Settings
from apps.api.services.auth import provision_user
from packages.db.database import build_database


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True)
    args = parser.parse_args()
    if not 1 <= len(args.name.strip()) <= 80:
        parser.error('Name must contain 1–80 characters.')
    engine, sessions = build_database(Settings().database_url)
    with sessions.begin() as db:
        user, token = provision_user(db, args.name.strip())
        result = {'user_id': user.id, 'token': token}
    engine.dispose()
    print(json.dumps(result))


if __name__ == '__main__':
    main()
