# Phase 3 — Nền backend và điều phối tác nhân

## Kết quả triển khai

- API FastAPI tại `http://localhost:8000/docs`, chat tại cổng 8001.
- PostgreSQL 17, schema Alembic: users, documents, study_sessions, jobs. Migration chạy bằng service riêng trước API/worker.
- Bearer token ngẫu nhiên 256 bit cho từng người dùng; DB chỉ lưu SHA-256. Tạo tài khoản qua CLI, chưa có đăng nhập giao diện.
- Tạo, liệt kê, đọc và xóa ghi chú văn bản; lưu nguồn UTF-8 trong volume riêng, tên file do server sinh; tải nguồn phải qua kiểm tra chủ sở hữu.
- Phiên học gắn với tài liệu; gửi tác vụ phân loại/giảng dạy và truy vấn kết quả đã lưu.
- Bộ điều phối chỉ nhận hành động đã khai báo. Phân loại kiểm tra JSON theo schema; giảng dạy nhận nguồn, câu hỏi và mức hỗ trợ ngôn ngữ.
- Model không truy cập DB/storage hay quyết định quyền. API và worker đều kiểm tra chủ sở hữu.
- Mỗi kết quả có source_document_id, model và review_status=unreviewed. Đây là liên kết tài liệu, chưa phải trích dẫn theo từng câu/trang.

## Hàng đợi và giao dịch

Worker chọn job bằng `FOR UPDATE SKIP LOCKED`, giữ khóa trong giao dịch suốt lần gọi model, kết thúc bằng succeeded hoặc failed. Bị ngắt trước commit khiến giao dịch rollback và job vẫn queued. API thấy queued cả khi đang xử lý; chưa có running/heartbeat.

Mỗi worker giữ một connection trong lúc suy luận, phù hợp thử nghiệm ít người dùng. Chưa có retry theo lịch, dead-letter queue hoặc giới hạn retry khi tiến trình liên tục crash. Lỗi model dự kiến được lưu failed; muốn thử lại thì gửi job mới.

Tham khảo khóa hàng của [SQLAlchemy](https://docs.sqlalchemy.org/en/20/core/selectable.html) và quy trình migration [Alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html).

## Lưu nguồn

Local object store trên volume `source_data`, chưa có S3/MinIO. Nguồn là văn bản gửi qua API đã bỏ khoảng trắng đầu/cuối, chưa phải file ảnh/PDF.

File và DB không dùng chung giao dịch phân tán. Tạo lỗi DB sẽ dọn file vừa tạo. Xóa file lỗi sẽ giữ bản ghi để thử lại; nếu tiến trình chết hoặc DB lỗi giữa xóa file và commit, có thể còn bản ghi thiếu nguồn (API trả 503). Cần cơ chế đối soát/outbox trước production; chưa có tính nguyên tử xuyên hai kho.

## Kiểm chứng

- 28 test đạt: 13 test chat và 15 case mới về migration, auth, quyền sở hữu, đầu vào, lưu xuyên app restart, delete cascade, lỗi model, rollback worker và đường dẫn nguồn.
- Migration 0001 chạy trên PostgreSQL thật; API readiness trả schema 0001.
- `alembic check` không phát hiện schema lệch model. Tài khoản demo vẫn xác thực được sau khi tạo lại API container.
- Smoke Docker thật: hai tài khoản tạm, ghi chú, phiên học, hai job; Qwen xử lý xong; tài khoản khác không đọc được dữ liệu; xóa nguồn xóa session/job. Dữ liệu thử tự dọn.
- Test hai consumer PostgreSQL: worker thứ hai bỏ qua hàng đang khóa và xử lý job khác, trong schema thử riêng được xóa sau test.
- Qwen trả unknown cho ghi chú trong smoke: đúng schema nhưng chưa đạt kỳ vọng phân loại. Một câu giải thích có nguồn hợp lý chưa đủ để thay đổi kết luận chất lượng model chưa đạt ở phase 2.

## Phần để phase sau

- Phase 4: ảnh/PDF, OCR, sửa văn bản.
- Phase 5: curriculum agent và nguồn chương trình đã duyệt.
- Phase 6: material/quiz agent và chấm điểm.
- Phase 7: tiến độ, ghi nhớ và ôn tập thích ứng.
- Phase 8: giao diện học sinh; hiện thử qua Swagger.

Giới hạn ghi chú 2400 ký tự và câu hỏi 500 ký tự để dùng chat phase 2; sẽ thay bằng chia đoạn/truy xuất ở phase tài liệu. Không tự cắt bớt nguồn.
