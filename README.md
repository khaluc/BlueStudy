# BlueStudy

Nền tảng học tiếng Anh học thuật cho người học ở nhiều trình độ: đọc hiểu, từ vựng, ngữ pháp, viết, ghi chú và ôn tập theo tài liệu. Không giới hạn lớp 9 hoặc một chương trình học cụ thể. Cấu trúc `apps/`, `packages/`, `infra/`, `docs/`, `data/`, `tests/` và `scripts/`.

## Current application

- Home: `/app/#home` with English and Vietnamese interfaces.
- Speaking: `/app/#speaking`, three-part practice, separate guided/independent modes, AssemblyAI live transcription, script highlighting and AI coaching.
- Chat: `/app/#chat`, image understanding, study conversations and interactive quizzes.
- Exams: `/app/#exams`, structured PDF exams and skill-based revision.
- Learning map: `/app/#map`, recent results and evidence-based revision priorities.

Copy `.env.example` to `.env` and provide your own credentials. Never commit `.env` or API keys. Start services with `docker compose up -d --build`.

Speaking marks compare recognised text and timing; they are not acoustic pronunciation assessments. AI exam answers and coaching are provisional.

The phase notes below document earlier versions; some older navigation and screenshots have since been replaced.

## Hiện trạng

- Phase 1: có đặc tả MVP trong `docs/phase-01-mvp-scope.md`.
- Phase 2: có chat service FastAPI, client Ollama, cấu hình, kiểm thử và script đo độ trễ. Máy phát triển hiện dùng `qwen3-vl:2b-instruct-q8_0` trong `.env`; xem báo cáo phase 2 để biết kết quả thực tế.
- Phase 3: PostgreSQL, migration, API có token, ghi chú văn bản, phiên học, worker và hai vai trò phân loại/giảng dạy. Xem [báo cáo](docs/phase-03-backend.md).
- Phase 4: upload ảnh/PDF, Qwen3-VL local đọc ảnh, duyệt/sửa văn bản và cấu hình chat Qwen Max API. Xem [hướng dẫn phase 4](docs/phase-04-upload-ocr.md).
- Phase 5–8: gợi ý chủ đề Global Success, bộ ôn tập/flashcard/quiz, hồ sơ và tiến độ xuyên phiên, giao diện tiếng Việt tại **http://localhost:8000/app/**.
- Phase 9: kiểm thử kỹ thuật, script Chrome E2E và backup/restore. Chưa nghiệm thu chất lượng bởi giáo viên hoặc kiểm thử tải. Xem [hướng dẫn và giới hạn bản MVP](docs/phase-05-09-mvp.md).

Kiểm chứng local: **109 test đạt, 1 test live bỏ qua**, E2E Chrome và backup/restore đã chạy riêng. [Báo cáo kiểm thử](docs/phase-09-verification.md).

## Mở giao diện học tập

**Đề thi PDF:** mở **http://localhost:8000/app/#exams** để chuyển toàn bộ PDF thành câu hỏi A–D, phân loại kỹ năng, làm bài và nhận gợi ý ôn theo kết quả. Điểm theo đáp án AI được ghi rõ là tạm tính. [Hướng dẫn và giới hạn](docs/structured-exams.md).

Bản Docker local mở trực tiếp góc học tập mặc định, không cần đăng nhập hay nhập mã. Tài liệu và lịch sử cũ được giữ nguyên; các trình duyệt trên máy dùng chung tài khoản này.

Trong Chat AI, bấm **Tạo quiz trắc nghiệm** để làm 5 câu bằng các ô chọn A–D, nộp bài và xem giải thích. Bảng hoạt động hiển thị ba bước xử lý thật; điểm được lưu trong lịch sử chat.

**Chat AI riêng:** mở **http://localhost:8000/app/#chat** để hỏi bài ngay, lưu lịch sử và đính kèm ảnh/PDF. Có bảng trạng thái xử lý và hỗ trợ điện thoại. Xem [hướng dẫn chat](docs/chat-interface.md).

Chạy `docker compose up -d --build`, mở **http://localhost:8000/app/**. Giao diện sổ tay có sơ đồ pastel và khung bài học/chat/quiz; có thể thử vở mẫu trước khi đăng nhập. Có thể nộp quiz, xem lại câu sai và tiếp tục phiên học đã lưu. Xem [hướng dẫn giao diện mới](docs/notebook-interface.md).

## Dùng ảnh/PDF

Vào http://localhost:8000/docs và Authorize bằng token demo. Gọi POST /uploads để chọn file; dùng GET /documents/{id} chờ review_required, xem pages/text và tải bản gốc qua /source. Sửa bằng PATCH /documents/{id}/text nếu cần; POST /documents/{id}/confirm với expected_revision hiện tại trước khi tạo phiên học.

**Đúng cấu hình đã chọn:** chat `qwen3.8-max-0902` qua API, đọc ảnh `qwen3-vl:2b-instruct-q8_0` qua Ollama local. Điền DASHSCOPE_API_KEY trong `.env` để bật cloud chat. Không có key thì chat dùng local dự phòng và báo rõ lý do; ảnh không gửi sang vision cloud.

## Thử backend đang chạy

Mở **http://localhost:8000/docs**. Tài khoản demo local ở `data/local-demo.json` (gitignored); chép trường `token` vào **Authorize**, không nhập tiền tố Bearer vì Swagger tự thêm.

1. `POST /documents`: gửi title và text (tối đa 2400 ký tự).
2. `POST /sessions`: gửi document_id nhận ở bước trước.
3. `POST /sessions/{session_id}/jobs`: gửi `{"kind":"classify"}` hoặc `{"kind":"teach","question":"Giải thích ghi chú này"}`.
4. `GET /jobs/{job_id}`: xem kết quả; đầu ra AI chưa được duyệt.

Khởi động backend: `docker compose up --build -d`. Cài mới cần `.env` với POSTGRES_PASSWORD ngẫu nhiên dạng hex. Không chép đè `.env` đang dùng. Tạo demo một lần bằng `python -m scripts.provision_local_demo`.

## Chạy trên PowerShell

Chạy các lệnh trong thư mục `padayon`. Python 3.14 đã được dùng để kiểm thử.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m uvicorn apps.chat.main:app --host 127.0.0.1 --port 8001
```

API docs: http://127.0.0.1:8001/docs. Service khởi động được khi chưa có Ollama; readiness và chat sẽ trả 503 nếu mô hình chưa sẵn sàng.

Xem [runbook](docs/runbook.md) để cài/chạy mô hình và [kế hoạch phase](docs/phases.md) để biết các bước tiếp theo.
