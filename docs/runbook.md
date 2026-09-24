# Chạy và kiểm tra BlueStudy

## MVP phase 5–9

Giao diện: <http://localhost:8000/app/>. Chat AI: <http://localhost:8000/app/#chat>. Đề thi: <http://localhost:8000/app/#exams>. Schema hiện tại `0008`.
Xem [luồng sử dụng, kiểm thử, backup/restore và giới hạn](phase-05-09-mvp.md).
Chạy test API mặc định không gọi cloud; `scripts.smoke_study` và `scripts.smoke_web` gọi mô hình thật.

## Phase 4: Qwen Max API + Qwen3-VL local

Upload/OCR: [hướng dẫn và cấu hình](phase-04-upload-ocr.md). `.env` đã chọn VISION_PROVIDER=ollama. Chỉ chat service được truyền DASHSCOPE_API_KEY, worker đọc ảnh không nhận key này. Sau khi điền key local, tái tạo chat/worker để nhận env mới.

```powershell
docker compose up --build -d
python -m scripts.generate_test_data
python -m scripts.smoke_uploads
```

Smoke upload chạy model ảnh thật trên Ollama và dọn các tài liệu thử. Với PDF nhiều trang, giới hạn tổng extraction 120 giây có thể cần điều chỉnh sau benchmark. Trạng thái failed giữ nguồn, cho phép sửa tay hoặc retry.

## Backend phase 3

Giữ `.env` hiện tại. Cài mới: sao chép `.env.example`, thay POSTGRES_PASSWORD bằng chuỗi hex ngẫu nhiên, chọn model đã tải. Đổi env không tự đổi mật khẩu của DB trong volume đã tồn tại.

```powershell
docker compose up --build -d
docker compose ps
docker compose exec -T api python -m alembic current
```

API 8000, chat 8001; PostgreSQL không mở cổng host. Migration chạy trước API/worker. Dữ liệu nằm trong named volumes postgres_data/source_data.

Tạo demo local một lần trên host từ thư mục padayon: `python -m scripts.provision_local_demo`. Token ở `data/local-demo.json`, không commit; dùng trường token trong Authorize của Swagger. Tạo tài khoản khác: `docker compose exec -T api python -m scripts.create_user --name "Learner"`; lệnh này hiển thị token một lần, giữ riêng.

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q -p no:cacheprovider
docker compose exec -T api python -m scripts.smoke_backend
docker compose exec -T api python -m scripts.check_postgres_queue
```

Smoke tạo dữ liệu thử rồi tự dọn; queue check dùng schema thử riêng. Smoke gọi model thật, có thể thất bại nếu output sai schema.

Dừng bằng `docker compose stop`; chạy lại bằng `docker compose up -d`. Không dùng `down -v` nếu muốn giữ dữ liệu. Chưa có backup production hoặc triển khai Internet.

## Chat phase 2

## 1. Chuẩn bị model

Máy phát triển hiện đã chạy Ollama và có `qwen3-vl:2b-instruct-q8_0`. File `.env` local chọn model này với `LLM_NUM_PREDICT=1024`. Không cần tải Gemma để chạy cấu hình local hiện tại. `.env.example` vẫn là mẫu Gemma ban đầu; đừng chép đè `.env` đang dùng nếu muốn giữ Qwen.

Cài Ollama từ [trang chính thức](https://ollama.com/download), khởi động ứng dụng Ollama, rồi chạy:

```powershell
ollama --version
ollama pull gemma4:e2b
ollama list
```

Nếu ứng dụng chưa chạy, mở terminal riêng và dùng `ollama serve`. Quá trình tải model cần vài GB đĩa/mạng; mã dự án không tự tải. Chưa thực hiện cài đặt/tải trong phase này.

## 2. Chạy chat

Theo lệnh cài Python trong README. Từ thư mục padayon, tạo `.env` từ `.env.example`, rồi chạy:

```powershell
python -m uvicorn apps.chat.main:app --host 127.0.0.1 --port 8001
```

Terminal thứ hai:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/health/ready
$body = @{ message = 'Explain since and for in Vietnamese, with two English examples.' } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8001/chat -Method Post -ContentType 'application/json; charset=utf-8' -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
```

## 3. Kiểm thử và đo

```powershell
python -m pytest -q
python -m scripts.benchmark_llm --runs 6
python -m scripts.smoke_chat
```

Kết quả ghi `data/benchmarks/llm.json` khi mọi lượt thành công. Lượt đầu chỉ được đánh dấu có thể cold; script không unload model. p95 warm tính trên các lượt còn lại, là độ trễ toàn bộ câu trả lời. Sáu lượt là smoke benchmark; dùng ít nhất 31 lượt tổng cho đánh giá ban đầu và lưu cấu hình máy, phiên bản runtime, digest model riêng. Cần duyệt câu trả lời trước khi chấp nhận chất lượng.

## 4. Docker tùy chọn

Khởi động Docker Desktop Linux engine và Ollama host trước:

```powershell
docker compose config
docker compose up --build chat
```

Compose kết nối `host.docker.internal:11434`. Nếu container không truy cập được Ollama host, kiểm tra cấu hình bind và firewall theo [FAQ Ollama](https://docs.ollama.com/faq); ưu tiên chạy Python trực tiếp khi phát triển. Không mở cổng model/chat ra mạng công cộng. Compose không cài hoặc chạy Ollama.

## 5. Chẩn đoán

- Ready 503: kiểm tra Ollama đang chạy, URL `.env` và tag trong `ollama list`.
- Chat 503: kiểm tra runtime/model, bộ nhớ và log Ollama; API không trả nguyên lỗi backend.
- Chat 504: inference quá chậm; kiểm tra mức tải và thử giảm độ dài yêu cầu.
- Chat 502: đầu ra rỗng/sai hoặc chạm giới hạn token; kiểm tra model, cân nhắc tăng `LLM_NUM_PREDICT` rồi đo lại.
- Docker pipe không tồn tại: Docker Desktop Linux engine chưa chạy; vẫn có thể dùng Python trực tiếp.

Phase 3 đã có dữ liệu lưu bền và worker. OCR, K8s, backup production chưa triển khai.
