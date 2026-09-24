import csv
from io import BytesIO, StringIO
import os
import subprocess
from PIL import ImageOps
from packages.ocr.errors import ExtractionError


def recognize(image):
    image = ImageOps.exif_transpose(image)
    if image.mode in ('RGBA', 'LA') or 'transparency' in image.info:
        rgba = image.convert('RGBA')
        from PIL import Image
        background = Image.new('RGBA', rgba.size, 'white')
        image = Image.alpha_composite(background, rgba).convert('RGB')
    else:
        image = image.convert('RGB')
    image.thumbnail((3500, 3500))
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    try:
        result = subprocess.run(
            ['tesseract', 'stdin', 'stdout', '-l', 'vie+eng', '--psm', '3', 'tsv'],
            input=buffer.getvalue(), capture_output=True, timeout=30,
            env={**os.environ, 'OMP_THREAD_LIMIT': '2'},
        )
    except FileNotFoundError as exc:
        raise ExtractionError('ocr_unavailable') from exc
    except subprocess.TimeoutExpired as exc:
        raise ExtractionError('ocr_timeout') from exc
    if result.returncode:
        raise ExtractionError('ocr_failed')
    lines, confidences, low_words = {}, [], []
    for row in csv.DictReader(StringIO(result.stdout.decode('utf-8')), delimiter='\t'):
        word = (row.get('text') or '').strip()
        if not word:
            continue
        key = (row['block_num'], row['par_num'], row['line_num'])
        lines.setdefault(key, []).append(word)
        confidence = float(row['conf'])
        if confidence >= 0:
            confidences.append(confidence)
            if confidence < 60 and len(low_words) < 100:
                low_words.append({'text': word, 'confidence': round(confidence, 1)})
    text = '\n'.join(' '.join(words) for words in lines.values())
    return {'text': text, 'confidence': round(sum(confidences) / len(confidences), 1) if confidences else None,
            'low_confidence_words': low_words, 'method': 'ocr',
            'warnings': ['review_ocr'] + (['low_confidence'] if low_words else [])}
