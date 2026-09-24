from io import BytesIO
import math
import unicodedata
from PIL import Image
import pypdfium2 as pdfium
from packages.ocr.errors import ExtractionError
from packages.ocr.validation import inspect_source
from packages.ocr.tesseract_ocr import recognize


def normalize(text):
    text = unicodedata.normalize('NFC', text).replace('\r\n', '\n').replace('\r', '\n')
    return ''.join(c for c in text if c in '\n\t' or unicodedata.category(c) != 'Cc').strip()


def extract(data: bytes, ocr=recognize):
    meta = inspect_source(data)
    pages = []
    if meta['media_type'] != 'application/pdf':
        with Image.open(BytesIO(data)) as image:
            pages.append({'page': 1, **ocr(image)})
    else:
        with pdfium.PdfDocument(data) as pdf:
            for index in range(len(pdf)):
                page = pdf[index]
                try:
                    textpage = page.get_textpage()
                    try:
                        if textpage.count_chars() > 20000:
                            raise ExtractionError('text_limit')
                        text = normalize(textpage.get_text_range())
                    finally:
                        textpage.close()
                    if text.strip():
                        result = {'text': text, 'method': 'pdf_text', 'confidence': None,
                                  'low_confidence_words': [], 'warnings': ['review_text_layer']}
                    else:
                        width, height = page.get_size()
                        if not all(math.isfinite(v) and 0 < v <= 14400 for v in (width, height)):
                            raise ExtractionError('page_dimensions')
                        scale = min(2.5, math.sqrt(10_000_000 / (width * height)))
                        bitmap = page.render(scale=scale)
                        try:
                            result = ocr(bitmap.to_pil())
                        finally:
                            bitmap.close()
                    pages.append({'page': index + 1, **result})
                finally:
                    page.close()
    for page in pages:
        page['text'] = normalize(page['text'])
        if len(page['text']) > 20000:
            raise ExtractionError('text_limit')
        if not page['text']:
            page['warnings'].append('empty_page')
    text = '\n\n'.join(page['text'] for page in pages).strip()
    if len(text) > 100000:
        raise ExtractionError('text_limit')
    return {'pages': pages, 'text': text, 'page_count': len(pages)}
