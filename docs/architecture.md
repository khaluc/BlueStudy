# Kiến trúc — cập nhật phase 4

Upload API lưu ảnh/PDF gốc → worker khóa tài liệu queued → parser con: PDF text trích trực tiếp, ảnh/trang scan gọi Qwen3-VL qua Ollama host → lưu văn bản/pages chờ duyệt. Người dùng sửa/xác nhận → tạo session chứa snapshot.

Chat service chọn QwenCloud `qwen3.8-max-0902` khi có key; local Ollama dự phòng có ghi lý do. Worker vision không nhận cloud key. Cấu hình và giới hạn: [phase 4](phase-04-upload-ocr.md).

## Nền phase 3

Luồng hiện tại: client có Bearer token → API :8000 → PostgreSQL và volume nguồn. Worker lấy job từ PostgreSQL → orchestrator → classifier/teaching agent → chat :8001 → Ollama host.

API kiểm tra quyền ở mọi tài nguyên; worker kiểm tra lại trước khi gọi model. Model không có công cụ database/filesystem. Migration Alembic chạy trước API/worker. PostgreSQL không publish cổng host, API/chat chỉ publish loopback.

Nguồn text trong local volume; metadata, text cho AI, user, session và job trong PostgreSQL. Queue dùng khóa PostgreSQL, chưa cần Redis. Chat phát triển cổng 8001 chưa có auth; gateway 8000 có token. Các vai trò còn lại sẽ thêm theo phase.

Chi tiết và giới hạn giao dịch: [phase 3](phase-03-backend.md).

## Lịch sử thiết kế phase 2 (đã được bổ sung ở phase 3)

Phase 2 hiện chạy: client HTTP → FastAPI chat → Ollama trên host → Gemma được cấu hình.

Chat service không có database, không lưu hội thoại và không có quyền truy cập file học sinh. Mỗi request là một lượt độc lập. Prompt do server quản lý.

Kiến trúc đích: web → API gateway → storage/database và worker queue; chat gọi bộ điều phối với các công cụ đã kiểm tra quyền truy cập. Tác nhân phân loại, mapping, tạo tài liệu, quiz, giảng dạy và ghi nhớ là module trong service, không bắt buộc mỗi tác nhân thành microservice.

Lưu nguồn trong object storage; dữ liệu người dùng, tài liệu, bộ học và kết quả trong PostgreSQL. Lựa chọn queue, ORM, vector index và migration sẽ được chốt ở phase 3. Chưa có triển khai các thành phần này.

Compose phase 2 chỉ chạy chat và kết nối Ollama host. Chỉ publish cổng trên loopback; chưa được dùng như dịch vụ Internet vì chưa có xác thực hoặc rate limit.
