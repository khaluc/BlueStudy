"""Generate synthetic printed notes, not student data. No AI image generation."""
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfWriter, PdfReader
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject


def text_pdf():
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject({NameObject('/Type'): NameObject('/Font'),
                             NameObject('/Subtype'): NameObject('/Type1'),
                             NameObject('/BaseFont'): NameObject('/Helvetica')})
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({
        NameObject('/F1'): writer._add_object(font)})})
    stream = DecodedStreamObject()
    stream.set_data(b'BT /F1 18 Tf 50 720 Td (English notes: since and for.) Tj 0 -32 Td (Since 2020. For two years.) Tj ET')
    page[NameObject('/Contents')] = writer._add_object(stream)
    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def blank_pdf(count=1, encrypted=False):
    writer = PdfWriter()
    for _ in range(count):
        writer.add_blank_page(width=612, height=792)
    if encrypted:
        writer.encrypt('test-password', algorithm='RC4-128')
    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def sample_files():
    fonts = [Path('C:/Windows/Fonts/arial.ttf'), Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
    font_path = next((str(path) for path in fonts if path.exists()), None)
    font = ImageFont.truetype(font_path, 48) if font_path else ImageFont.load_default(size=48)
    image = Image.new('RGB', (1800, 900), 'white')
    draw = ImageDraw.Draw(image)
    for index, line in enumerate(['BlueStudy - Ghi chú tiếng Anh lớp 9',
                                 'Since: từ một mốc thời gian.',
                                 'For: trong một khoảng thời gian.',
                                 'I have lived here since 2020.',
                                 'I have studied English for two years.']):
        draw.text((70, 70 + index * 125), line, font=font, fill='black')
    files = {}
    for name, fmt in [('sample_note_image.png', 'PNG'), ('sample_note_image.jpg', 'JPEG'),
                      ('sample_scan.pdf', 'PDF')]:
        out = BytesIO()
        image.save(out, format=fmt)
        files[name] = out.getvalue()
    files['sample_note.pdf'] = text_pdf()
    writer = PdfWriter()
    writer.append(PdfReader(BytesIO(files['sample_note.pdf'])))
    writer.append(PdfReader(BytesIO(files['sample_scan.pdf'])))
    out = BytesIO()
    writer.write(out)
    files['sample_mixed.pdf'] = out.getvalue()
    return files


if __name__ == '__main__':
    root = Path('data/samples')
    root.mkdir(parents=True, exist_ok=True)
    for name, content in sample_files().items():
        (root / name).write_bytes(content)
        print(name)
