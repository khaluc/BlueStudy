# Đề thi PDF có cấu trúc

Mở `/app/#exams` hoặc **Đề thi & ôn tập**. Tải PDF (tối đa 10 MB, 20 trang); cũng có thể mở PDF trong thư viện và chọn **Chuyển thành đề thi có cấu trúc**.

1. PDF có lớp chữ được trích xuất trực tiếp; trang scan đi qua OCR hiện có. Bản gốc được giữ trong kho tài liệu.
2. Bộ tách cấu trúc nhận dạng `Question N.`/`Câu N.`, các phương án A–D và hướng dẫn/đoạn đọc dùng chung. Không tạo mới câu hỏi. Nối nội dung qua trang, xử lý nhãn đáp án bị dính số trong lớp chữ PDF. Thiếu lựa chọn hoặc số câu thì dừng ở `needs_review`; không cho chấm đề thiếu.
3. AI phân tích từng nhóm tối đa 5 câu, phân loại chủ đề và kỹ năng; đề xuất đáp án cùng giải thích và trích dẫn. Mỗi nhóm lưu độc lập để thấy tiến độ thật. Các chủ đề hiện có: ngữ pháp, từ vựng, đọc hiểu, liên kết/sắp xếp văn bản. Kỹ năng chi tiết gồm từ loại, trật tự từ, dạng động từ, giới từ, cụm từ, từ nối, từ hạn định, ý chính, suy luận, quy chiếu, chèn câu, diễn đạt tương đương…
4. Người học chọn A–D, có thể để trống. Máy chủ chấm theo đáp án đề xuất và thống kê câu sai theo kỹ năng. AI nhận số liệu này để viết gợi ý ôn tập. Nếu bước viết nhận xét lỗi, điểm và giải thích đã chấm vẫn được giữ.

**Giới hạn đáp án:** bản này chưa nhập/đối chiếu đáp án chính thức. Mọi kết quả đều gắn `ai_unverified` và hiển thị là tạm tính. Câu có đáp án không chắc chắn hoặc không có trích dẫn khớp nguồn sẽ không tính điểm. Trích dẫn khớp không chứng minh suy luận của AI đúng. Chưa xác thực ký hiệu gạch chân hoặc bố cục đặc biệt bị mất trong lớp chữ; người học nên đối chiếu PDF gốc.

Lựa chọn chưa nộp lưu trong sessionStorage của trình duyệt; kết quả và nhận xét lưu trong PostgreSQL theo tài khoản. Kết quả đề thi nằm trong mục này, tách khỏi tiến độ bộ ôn tập 5 câu. Có nút xuất JSON gồm cấu trúc và phân loại; không xuất khóa đáp án qua API đề chưa nộp.

API: `POST /exams` với `document_id`, `GET /exams`, `GET /exams/{id}`, `POST /exams/{id}/attempts` với danh sách đáp án 0–3 hoặc null, `GET /exams/{id}/attempts`. API kiểm tra chủ sở hữu; xóa tài liệu xóa đề và kết quả liên quan. Migration `0008` bổ sung `exams`, `exam_attempts`.

Kiểm tra: `python -m pytest -q`, `python -m scripts.smoke_exams`. File Đại học Vinh được kiểm chứng: 8 trang, 40 câu, 6 nhóm đoạn đọc/hướng dẫn. Dữ liệu đã nhập có thể mở từ danh sách đề. Script nhập một PDF được chỉ định: `python -m scripts.import_exam "duong-dan.pdf"`.
