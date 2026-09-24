import json
import subprocess
import sys
from packages.ocr.errors import ExtractionError


def run_parser(data: bytes, mode: str):
    if mode not in {'inspect', 'extract'}:
        raise ValueError('Unknown operation')
    try:
        result = subprocess.run([sys.executable, '-m', 'packages.ocr.runner', mode],
                                input=data, capture_output=True, timeout=20 if mode == 'inspect' else 120)
    except subprocess.TimeoutExpired as exc:
        raise ExtractionError('extraction_timeout') from exc
    if result.returncode:
        raise ExtractionError('parser_failed')
    try:
        body = json.loads(result.stdout)
        if 'error' in body:
            raise ExtractionError(body['error'], body.get('detail'))
        return body['result']
    except (ValueError, KeyError) as exc:
        raise ExtractionError('parser_failed') from exc
