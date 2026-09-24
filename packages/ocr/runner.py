"""Bound expensive parsers/OCR in a child process, JSON-only stdout."""
import json
import sys


def main():
    if sys.platform != 'win32':
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (1536 * 1024**2, 1536 * 1024**2))
        resource.setrlimit(resource.RLIMIT_CPU, (110, 110))
    from packages.ocr.errors import ExtractionError
    from packages.ocr.validation import MAX_BYTES, inspect_source
    try:
        data = sys.stdin.buffer.read(MAX_BYTES + 1)
        if sys.argv[1] == 'inspect':
            result = inspect_source(data)
        elif sys.argv[1] == 'extract':
            from packages.ocr.extraction import extract
            from packages.ocr.vision_ocr import recognize
            result = extract(data, ocr=recognize)
        else:
            raise ValueError('Unknown operation')
        print(json.dumps({'result': result}, ensure_ascii=True))
    except ExtractionError as exc:
        print(json.dumps({'error': exc.code, 'detail': exc.detail}))
    except Exception:
        print(json.dumps({'error': 'extraction_failed'}))


if __name__ == '__main__':
    main()
