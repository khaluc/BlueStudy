import pytest
from packages.core.study_source import prepare_study_source

EXAM = '''BỘ GIÁO DỤC VÀ ĐÀO TẠO
KỲ THI TỐT NGHIỆP TRUNG HỌC PHỔ THÔNG NĂM 2026
ĐỀ THI CHÍNH THỨC
(Đề thi có 04 trang)
Thời gian làm bài: 50 phút
Họ, tên thí sinh: PRIVATE NAME
Số báo danh: PRIVATE NUMBER
Mã đề: 1144
Read the following leaflet and mark the letter A, B, C or D that best fits each of the numbered blanks.
GREEN HANDS, CLEAN LAND
The theme for Green Week 2026 puts (1)_____ on the role of our community.
Since 2018, our annual campaigns have been coming up (3)_____ .
Participation in (4)_____ activity is open to all residents.
Completed forms (5)_____ be submitted by 30 June.
The harder we try, (6)_____ our future will be!
Question 1. A. example B. influence C. intention D. emphasis
Question 3. A. gold B. roses C. goods D. sky
Question 4. A. other B. neither C. either D. both
Question 5. A. ought B. should not C. should D. ought not
Question 6. A. greener B. greenest C. the greener D. the greenest
Trang 1/4 - Mã đề thi 1144'''


def test_headers_removed_passage_numbers_and_choices_preserved():
    source=prepare_study_source(EXAM)
    assert source.exam and source.cloze
    for removed in ['PRIVATE','1144','50 phút','04 trang','BỘ GIÁO']:
        assert removed not in source.text
    for retained in ['Green Week 2026','Since 2018','30 June','(1)_____','D. emphasis','D. the greenest']:
        assert retained in source.text
    assert 'Mã đề: 1144' in EXAM


@pytest.mark.parametrize('question',[
    'Đề thi này năm bao nhiêu?', 'Mã đề của bài là gì?', 'Thời gian làm bài bao lâu?',
    'Đề thi có bao nhiêu trang?', 'Chủ đề của Tuần lễ Xanh 2026 là gì?',
    'Hạn chót nộp đơn đăng ký là ngày nào?', 'Hai hoạt động được lên kế hoạch là gì?',
])
def test_administration_and_cloze_trivia_rejected(question):
    with pytest.raises(ValueError):prepare_study_source(EXAM).validate_items([question])


def test_language_questions_and_ordinary_reading_allowed():
    prepare_study_source(EXAM).validate_items([
        'Điền từ vào chỗ trống: puts _____ on the role of our community.',
        'Cấu trúc so sánh kép trong The harder we try, ... là gì?',
        'Cụm từ come up roses có nghĩa là gì?',
    ],['Ôn cách dùng giới từ và thì hiện tại hoàn thành.'])
    ordinary='The library opens in 2026. The event lasts 50 minutes.'
    source=prepare_study_source(ordinary)
    assert source.text==ordinary and not source.exam
    source.validate_items(['When does the library open?'])


def test_flat_ocr_header_does_not_remove_exercise():
    source=prepare_study_source('Mã đề: 1144 Read the following text. Question 1. A. one B. two C. three D. four')
    assert '1144' not in source.text and 'A. one' in source.text


def test_header_only_cannot_generate_learning_materials():
    with pytest.raises(ValueError):prepare_study_source('Mã đề: 1144\nThời gian làm bài: 50 phút')
