# Kết quả kiểm chứng MVP local

Ghi nhận ngày 2026-09-23. Môi trường Windows, Docker Desktop, PostgreSQL 17, Chrome, Python 3.14. Schema `0004`.

| Kiểm tra | Kết quả |
|---|---|
| `python -m pytest -q -p no:cacheprovider --tb=short` | **69 passed, 1 skipped**. Ca bị skip là E2E có gọi cloud, cần bật chủ động |
| `node --check apps/web/app.js` | Qua kiểm tra cú pháp |
| `docker compose exec -T api python -m alembic check` | Không có schema drift |
| `python -m scripts.smoke_study` | Qwen Cloud `qwen3.8-max-0902`, `fallback_reason=null`; sinh bộ học hợp lệ, nộp quiz và đọc lại điểm đã lưu |
| `python -m scripts.smoke_web` | Chrome thật: đăng nhập, thêm ghi chú, tạo phiên/chọn chủ đề, tạo bộ học, hiển thị flashcard, nộp quiz, tiến độ, sửa hồ sơ, tải lại trang, mobile 390 px không tràn ngang |
| `python -m scripts.smoke_web_upload` | Chrome mobile: tải PDF có text, chờ trích xuất, sửa/xác nhận, tạo phiên học, đăng xuất và xóa token khỏi tab |
| `python -m scripts.smoke_backup` | Backup có tài liệu mẫu; khôi phục PostgreSQL vào DB tạm, kiểm tra SHA-256 nguồn thành công; xóa DB/tài liệu thử sau kiểm tra |
| `docker compose exec -T api python -m scripts.check_postgres_queue` | Hai consumer lấy các job khác nhau, bỏ qua row đang bị khóa |

Các test backend bổ sung kiểm tra không trả khóa đáp án trong job/học liệu trước khi nộp, dữ liệu khác chủ tài khoản trả 404, kiểm tra kiểu và số lượng đáp án, chấm điểm server, xóa cascade, nguồn trích dẫn không tồn tại, gợi ý chủ đề không khớp, lưu lựa chọn chủ đề/hoạt động, tổng hợp điểm, ôn lỗi và bộ nhớ tách theo người dùng. Test generation riêng xác nhận tắt thinking/tăng ngân sách chỉ áp dụng cho bundle, không đổi chat thường.

Ban đầu dùng chế độ chat ngắn cho bundle không đạt đầu ra cấu trúc. Đã tách `purpose=study_bundle` với system prompt JSON và ngân sách riêng, sau đó kiểm chứng bằng API và Chrome thật. Đáp án mô hình thường tập trung ở lựa chọn đầu: backend hiện xáo trộn lựa chọn một lần, cập nhật đáp án rồi lưu nhất quán.

Kết quả mẫu synthetic trong `data/benchmarks/live-study.json`; ảnh desktop/mobile trong cùng thư mục. Đây là artifact local không commit. Một số câu dịch còn máy móc, ví dụ dịch “reduce traffic” thành “giảm thiểu giao thông”; chưa có đánh giá độc lập của giáo viên. Mẫu nhỏ không đủ xác nhận chất lượng sư phạm hoặc mức độ phù hợp của toàn bộ chương trình.

Các warning của test hiện tại gồm deprecation từ FastAPI/Starlette TestClient và cảnh báo Pillow trong ca cố tình dùng ảnh quá lớn. Không có test thất bại.

Chưa kiểm thử tải nhiều người dùng, phục hồi đầy đủ vào môi trường triển khai khác, đăng nhập công khai, đánh giá của giáo viên/học sinh hoặc SLA. Kết quả hai worker là kiểm tra đúng đắn của queue, không phải benchmark tải. Backup verification kiểm tra phục hồi DB và khớp nguồn, không thay cho diễn tập khôi phục toàn bộ ứng dụng ở môi trường mới.
