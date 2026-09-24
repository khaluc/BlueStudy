# Phase 4 — Tải tài liệu, đọc ảnh/PDF và duyệt văn bản

## Cập nhật xác minh API

Sau khi người dùng điền key, đã tạo lại chat container và gửi một request thật. HTTP 200, provider=qwen_cloud, model=qwen3.8-max-0902, fallback_reason=null; câu trả lời đúng yêu cầu thử “BlueStudy API OK”. Kết nối cloud đã xác minh, chưa đánh giá chất lượng gia sư bằng phép thử ngắn này. Key không được ghi vào báo cáo.

## Cấu hình đã chọn cùng người dùng

| Công việc | Provider/model |
|---|---|
| Chat, giải thích; dùng lại cho tạo tài liệu ở phase 6 | QwenCloud API, `qwen3.8-max-0902` |
| Đọc ảnh và trang PDF scan | Ollama trên máy, `qwen3-vl:2b-instruct-q8_0` |
| PDF đã có chữ | Trích xuất lớp chữ bằng PDFium, không cần gọi model |
| Chat dự phòng | Model Ollama cấu hình trong OLLAMA_MODEL |
| Đọc ảnh dự phòng khi vision lỗi/timeout | Tesseract `vie+eng` trên worker |

Worker đọc ảnh không nhận DASHSCOPE_API_KEY và không gọi vision cloud. Văn bản đưa vào chat có thể được gửi tới QwenCloud khi key đã cấu hình. Mỗi kết quả chat ghi provider/model/fallback_reason; mỗi trang OCR/vision ghi tương tự. Dự phòng có thể tắt bằng LOCAL_FALLBACK_ENABLED=false.

Tên endpoint và cách gọi theo [QwenCloud](https://docs.qwencloud.com/developer-guides/getting-started/first-api-call). Model snapshot chat lấy đúng ID người dùng cung cấp; quyền truy cập model phải được kiểm chứng bằng key thực tế của tài khoản.

## Chức năng

- POST /uploads nhận multipart JPEG/PNG/PDF; trả 202 và document_id.
- Lưu nguyên bytes bản gốc, SHA-256, tên file, MIME, kích thước và số trang.
- Giới hạn 10 MiB/file, PDF tối đa 20 trang, ảnh tối đa 20 megapixel/cạnh 12000 px; kiểm tra nội dung thực và đuôi file/MIME.
- Từ chối file rỗng, hỏng, PDF có mật khẩu, ảnh động, loại không hỗ trợ. Giới hạn cả body multipart kể cả không có Content-Length.
- Worker xử lý nền; mỗi trang có text, method, cảnh báo và thông tin provider nếu dùng model.
- Chữ chuẩn hóa Unicode NFC. Bản trích xuất theo trang được giữ nguyên để đối chiếu; trường text cho phép chỉnh sửa riêng.
- PDF mixed gồm trang text và trang scan được xử lý theo từng trang.
- Xem/sửa/xác nhận/retry/tải nguồn đều kiểm tra chủ sở hữu.

## Trạng thái và duyệt

Upload: queued → review_required hoặc failed. Chỉ sau POST /documents/{id}/confirm mới thành confirmed và tạo được phiên học.

PATCH /documents/{id}/text nhận text và expected_revision. Mỗi lần sửa tăng revision; thao tác trên revision cũ trả 409. Xác nhận cũng cần expected_revision hiện tại. Không cho sửa khi đang queued.

OCR rỗng/timeout/lỗi giữ nguyên nguồn, ghi extraction_error và không sinh tài liệu học. Người dùng có thể nhập lại văn bản hoặc POST /documents/{id}/retry với revision hiện tại khi failed.

Nguồn gốc không đổi sau chỉnh sửa. Mỗi phiên học lưu source_text và document_revision riêng; sửa tài liệu sau đó không thay thế nội dung của phiên cũ.

Tổng text tối đa 100000 ký tự, tối đa 20000/trang. Chat hiện vẫn có cửa sổ nhỏ: nếu tài liệu dài hơn 2400 ký tự, tạo phiên cần chọn start_offset/end_offset để lấy đoạn tối đa 2400 ký tự. Không cắt nguồn âm thầm.

## Bật Qwen Max API

Sửa `.env` local, không gửi key vào chat hoặc frontend:

```dotenv
CHAT_PROVIDER=qwen_cloud
DASHSCOPE_API_KEY=your_actual_key
QWEN_BASE_URL=https://maas.qwencloudapi.com/compatible-mode/v1
QWEN_CHAT_MODEL=qwen3.8-max-0902
QWEN_ENABLE_THINKING=true
VISION_PROVIDER=ollama
OLLAMA_VISION_MODEL=qwen3-vl:2b-instruct-q8_0
LOCAL_FALLBACK_ENABLED=true
```

Sau khi sửa: `docker compose up -d --force-recreate chat worker`. Không dùng `docker compose config` để chia sẻ log sau khi điền key vì lệnh này có thể in giá trị môi trường.

Cloud client dùng giao thức tương thích OpenAI qua httpx, không bắt buộc SDK OpenAI. Đọc SSE từ cloud, chỉ ghép delta.content; không lưu hoặc trả reasoning_content. API /chat hiện trả JSON khi hoàn tất, chưa stream tới giao diện. enable_thinking không bảo đảm độ trễ thấp; có timeout và giới hạn token.

Chưa có key thì cloud không được gọi và chat trả fallback_reason=missing_api_key nếu dự phòng bật. Readiness cloud chỉ báo configured/upstream_verified=false để tránh gọi API tính phí trong healthcheck. Muốn xác minh key/model phải thử request thật và kiểm tra provider=qwen_cloud, fallback_reason=null.

## Kiểm chứng và giới hạn

- 58 test tự động đạt ở thời điểm tích hợp: pipeline, quyền sở hữu, revision, snapshot, file lỗi/quá giới hạn, multipart chunked, parser timeout, cloud SSE và dự phòng; các nhánh model dùng mock trong test này.
- File mẫu tổng hợp có sẵn ở data/samples; tạo lại bằng `python -m scripts.generate_test_data`.
- Smoke thực tế: `python -m scripts.smoke_uploads`, ghi kết quả vào data/benchmarks/phase4-uploads.json và tự xóa tài liệu/phiên thử.
- Đã chạy thành công 5/5 mẫu: PNG, JPEG, PDF scan, PDF text và PDF mixed. Ảnh/trang scan trả provider=ollama, đúng model Qwen3-VL local, fallback_reason=null; nội dung mẫu in rõ tiếng Việt/Anh khớp khi đối chiếu. Mỗi nguồn tải lại khớp bytes và tạo được session sau xác nhận.
- Thời gian từng mẫu (từ sau upload đến xác nhận/tạo session, gồm polling): PNG 24.35 giây ở lượt đầu, JPEG 4.13, scan 7.14, PDF text 3.12, mixed 3.09. Đây là smoke 5 mẫu tổng hợp, không phải p95 hoặc benchmark chữ viết tay.
- API readiness đang ở schema 0002. Chat readiness báo local dự phòng vì missing_api_key; chưa có kết quả suy luận cloud thật.
- Cloud đã được kiểm chứng kết nối bằng request thật sau khi điền key (xem cập nhật đầu trang). Chất lượng giảng dạy Qwen Max vẫn cần đánh giá riêng.
- Vision không cung cấp confidence đã hiệu chỉnh; trường confidence để null. Tesseract trả điểm nội bộ và từ thấp điểm; đây không phải xác suất đúng.
- Chữ viết tay, công thức, bảng nhiều cột và ảnh mờ chưa có tập đánh giá đại diện. Vision có thể chép thiếu hoặc bịa chữ; luôn cần đối chiếu bản gốc.
- Trang PDF có cả lớp chữ và chữ trong ảnh hiện ưu tiên lớp chữ; cảnh báo review_text_layer nhắc kiểm tra phần có thể bị bỏ sót.
- Parser/OCR chạy trong tiến trình con có timeout (inspect 20 giây, extract 120 giây); Linux giới hạn bộ nhớ khoảng 1.5 GiB cho parser. Quá hạn toàn tài liệu trả lỗi, không âm thầm chấp nhận một phần trang.
- Giao dịch giữa file và DB vẫn có giới hạn đã ghi ở phase 3. Giao diện học sinh sẽ triển khai phase 8; hiện thao tác qua Swagger.
