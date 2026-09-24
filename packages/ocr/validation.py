from io import BytesIO
from PIL import Image
from pypdf import PdfReader
from packages.ocr.errors import ExtractionError

MAX_BYTES = 10 * 1024 * 1024
MAX_PAGES = 20
MAX_PIXELS = 20_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


def inspect_source(data: bytes):
    if not data:
        raise ExtractionError('empty_file', 'File không có dữ liệu.')
    if len(data) > MAX_BYTES:
        raise ExtractionError('file_too_large', 'File vượt quá 10 MiB.')
    if data.startswith(b'%PDF-'):
        try:
            reader = PdfReader(BytesIO(data))
            if reader.is_encrypted:
                raise ExtractionError('encrypted_pdf', 'PDF có mật khẩu không được hỗ trợ.')
            count = len(reader.pages)
            if not 1 <= count <= MAX_PAGES:
                raise ExtractionError('page_limit', f'PDF này có {count} trang; ứng dụng hỗ trợ từ 1 đến {MAX_PAGES} trang. Hãy chia nhỏ PDF rồi tải lại.')
            return {'media_type': 'application/pdf', 'extension': '.pdf', 'page_count': count}
        except ExtractionError:
            raise
        except Exception as exc:
            raise ExtractionError('invalid_pdf', 'Không đọc được cấu trúc PDF.') from exc
    try:
        with Image.open(BytesIO(data)) as image:
            if image.format not in {'PNG', 'JPEG'}:
                raise ExtractionError('unsupported_type', 'Chỉ nhận PNG, JPEG hoặc PDF.')
            if image.width * image.height > MAX_PIXELS or max(image.size) > 12000:
                raise ExtractionError('image_too_large', 'Ảnh vượt giới hạn 20 megapixel hoặc cạnh 12000 px.')
            if getattr(image, 'n_frames', 1) != 1:
                raise ExtractionError('animated_image', 'Chỉ nhận ảnh một khung hình.')
            fmt = image.format
            image.verify()
        # verify alone does not decode JPEG pixels or detect every truncated stream.
        with Image.open(BytesIO(data)) as image:
            image.load()
        return {'media_type': 'image/png' if fmt == 'PNG' else 'image/jpeg',
                'extension': '.png' if fmt == 'PNG' else '.jpg', 'page_count': 1}
    except ExtractionError:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ExtractionError('image_too_large') from exc
    except Exception as exc:
        raise ExtractionError('invalid_image', 'File không phải ảnh PNG/JPEG hợp lệ.') from exc
