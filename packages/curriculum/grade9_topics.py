"""Topic titles checked against HEID; keyword suggestions are not teacher approval."""
import re

SOURCE = 'https://heid.vn/chinh-phuc-tu-vung-tieng-anh-lop-9-theo-chu-de-da-dang/'
_TOPICS = [
    ('Cộng đồng địa phương', 'community,local community,volunteer'),
    ('Cuộc sống thành thị', 'city,urban,traffic'),
    ('Sống khỏe ở tuổi thiếu niên', 'healthy,exercise,sleep'),
    ('Nhớ về quá khứ', 'heritage,monument,ancient'),
    ('Những trải nghiệm của chúng ta', 'experience,adventure,memorable'),
    ('Lối sống Việt Nam xưa và nay', 'lifestyle,tradition,then and now'),
    ('Kỳ quan thiên nhiên thế giới', 'wonder,cave,waterfall'),
    ('Du lịch', 'tourism,tourist,hotel'),
    ('Tiếng Anh trên thế giới', 'accent,englishes,native speaker'),
    ('Hành tinh Trái Đất', 'planet,earth,ecosystem'),
    ('Thiết bị điện tử', 'device,smartphone,electronic'),
    ('Lựa chọn nghề nghiệp', 'career,occupation,profession'),
]
TOPICS = [dict(id=f'gs9-u{i}', unit=i, title=title, book='Tiếng Anh 9 Global Success',
               source_url=SOURCE, source_status='topic_titles_checked', keywords=words.split(','))
          for i, (title, words) in enumerate(_TOPICS, 1)]


def suggest(text):
    matches = []
    for topic in TOPICS:
        evidence = [word for word in topic['keywords'] if re.search(r'\b' + re.escape(word) + r'\b', text, re.I)]
        if evidence:
            matches.append(dict(topic=topic, evidence=evidence, status='suggested'))
    return sorted(matches, key=lambda item: -len(item['evidence']))[:3]
