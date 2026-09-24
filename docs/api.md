# API phase 4 — upload và duyệt nguồn

Gateway vẫn ở cổng 8000 và yêu cầu Bearer token.

| Method | Path | Nội dung |
|---|---|---|
| POST | /uploads | multipart file, title tùy chọn; trả document 202 |
| PATCH | /documents/{id}/text | text, expected_revision; sửa bản văn, giữ nguồn và pages gốc |
| POST | /documents/{id}/confirm | expected_revision; duyệt văn bản để học |
| POST | /documents/{id}/retry | expected_revision; chạy lại khi trích xuất failed |

Document bổ sung source_name, media_type, source_size, page_count, status, pages, extraction_error, revision. Status là queued/review_required/confirmed/failed. /source trả đúng MIME dưới dạng attachment, có kiểm tra quyền.

POST /sessions chỉ nhận tài liệu confirmed. Có thể gửi start_offset/end_offset để chọn đoạn tối đa 2400 ký tự. Session trả source_text và document_revision đã chụp tại lúc tạo. File tối đa 10 MiB và 20 trang; 413 quá dung lượng, 415 loại/MIME không khớp, 422 file lỗi hoặc giới hạn trang, 409 chưa xác nhận hoặc revision cũ.

Chat :8001 bổ sung provider và fallback_reason. Cloud nhận SSE nội bộ nhưng endpoint vẫn trả JSON hoàn tất; không trả reasoning_content. Readiness cloud cấu hình có key trả configured/upstream_verified=false, không xác thực key bằng yêu cầu có phí.

## Các endpoint từ phase 3

Base URL `http://127.0.0.1:8000`, Swagger `/docs`. Ngoài health, mọi endpoint cần `Authorization: Bearer <token>`. Thiếu/sai token trả 401; không có tài nguyên thuộc người gọi trả 404. Không nhận owner_id từ client.

| Method | Path | Chức năng |
|---|---|---|
| GET | /health/live, /health/ready | Tiến trình / schema DB |
| GET, PATCH | /users/me | Hồ sơ cơ bản |
| POST, GET | /documents | Tạo / liệt kê ghi chú |
| GET, DELETE | /documents/{id} | Đọc / xóa nguồn và session/job liên quan |
| GET | /documents/{id}/source | Tải nguồn qua kiểm tra quyền |
| POST | /sessions | Tạo phiên từ document_id |
| GET | /sessions/{id} | Xem phiên |
| POST, GET | /sessions/{id}/jobs | Gửi tác vụ / xem kết quả gần nhất |
| GET | /jobs/{id} | Xem trạng thái/kết quả |

Tạo tài liệu trả 201: `{"title":"Ghi chú","text":"Nội dung"}`; title 1–160 ký tự, text 1–2400. Danh sách hỗ trợ limit (1–100), offset. Chưa nhận file.

Tạo phiên trả 201: `{"document_id":"UUID"}`. Gửi job trả 202: `{"kind":"classify"}` hoặc `{"kind":"teach","question":"Câu hỏi tối đa 500 ký tự"}`.

Job có queued/succeeded/failed, result hoặc error_code. Queued bao gồm đang xử lý trong transaction. Lỗi: model_timeout, model_unavailable, invalid_model_output, invalid_ownership. Kết quả luôn unreviewed.

PATCH hồ sơ nhận display_name (1–80 ký tự), language_level support/basic/confident. Chưa có đăng ký công khai, reset mật khẩu, quiz/material API.

# Chat service phase 2

Base URL local: `http://127.0.0.1:8001`. OpenAPI: `/openapi.json`; giao diện thử: `/docs`.

| Method | Path | Kết quả |
|---|---|---|
| GET | /health/live | 200 khi service đang chạy; không kiểm tra mô hình |
| GET | /health/ready | 200 khi Ollama liệt kê đúng model đã cấu hình; 503 nếu chưa sẵn sàng |
| POST | /chat | Nhận message; trả answer và model |

```json
{"message": "Giải thích since và for bằng tiếng Việt"}
```

Message sau khi bỏ khoảng trắng phải có nội dung; tối đa 4000 ký tự. Chưa nhận history, file, document_id hoặc user_id. Readiness kiểm tra model đã cài, không đảm bảo inference vừa bộ nhớ.

Lỗi: 422 đầu vào không hợp lệ, 502 phản hồi model sai/rỗng/bị cắt, 503 model không khả dụng, 504 timeout. Không dùng câu trả lời mẫu để thay thế khi model lỗi.

Documents/users/sessions nằm trên gateway 8000; upload ảnh/PDF, materials, quizzes chưa triển khai.
# Bổ sung API bộ học và tiến độ (schema 0004)

Tất cả endpoint dưới đây yêu cầu bearer token tài khoản; tài nguyên khác chủ sở hữu trả 404.

| Endpoint | Chức năng |
|---|---|
| `GET /curriculum` | Danh mục chủ đề và URL nguồn |
| `GET /sessions/{id}/curriculum` | Gợi ý, bằng chứng từ khóa, lựa chọn hiện tại |
| `PATCH /sessions/{id}/curriculum` | `{ "topic_id": "gs9-u1" }` hoặc `null` để bỏ chọn |
| `GET /sessions` | Tối đa 100 phiên học gần đây |
| `POST /sessions/{id}/jobs` | Thêm kind `generate_bundle` bên cạnh `classify`, `teach` |
| `GET /sessions/{id}/materials` | Bộ học đã lưu; không trả khóa đáp án |
| `GET /materials/{id}` | Nội dung học và provenance |
| `POST /materials/{id}/attempts` | `{ "answers": [0,1,2,3,0] }`; đúng 5 số nguyên từ 0 đến 3; trả điểm và giải thích |
| `GET /users/me/progress` | 100 lượt gần nhất, điểm trung bình và nhận xét theo chủ đề |
| `GET /users/me/review` | Câu sai cần ôn lại từ tối đa 20 lượt gần nhất |
| `DELETE /users/me/progress` | Xóa toàn bộ lịch sử điểm của chủ tài khoản |
| `GET /documents?q=keyword` | Tìm trong tên/nội dung tài liệu của chủ tài khoản |

`PATCH /users/me` thêm `learning_preference`: `notes`, `flashcards`, `quiz`. Chat nội bộ chấp nhận `message` tối đa 8.000 ký tự, `purpose=chat|study_bundle`. Web dùng các endpoint có xác thực của gateway, không gọi chat trực tiếp.
