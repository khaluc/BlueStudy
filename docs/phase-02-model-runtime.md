# Phase 2 — Chọn mô hình và phương án chạy

Ngày kiểm tra: 21/09/2026.

## Cập nhật sau khi cài Ollama và bật Docker

Phần dưới mục này giữ lại lịch sử thiết lập Gemma ban đầu. Cấu hình local đang chạy thực tế là **qwen3-vl:2b-instruct-q8_0**, không phải Gemma. Chọn model có sẵn để kiểm chứng khả năng thay model; không tải thêm model.

- Ollama 0.34.2, Docker Engine 29.8.0; container `padayon-chat-1` healthy, cổng `127.0.0.1:8001`.
- Readiness trả 200 với đúng Qwen; cả 4 yêu cầu HTTP smoke test hoàn tất.
- 13 kiểm thử HTTP mock đạt. Thêm `pytest.ini` để chỉ thu thập test trong `tests`, tránh thư mục cache cũ không đọc được.
- Model digest: `9674b2259d72aeac7d8ee4743e01fe1e9bb624f93110c4bcd87d9d5844ab3bf7`.
- Context 4096, đầu ra tối đa 1024 token. Lần chạy đầu với 512 token bị cắt; đã tăng giới hạn và thêm chỉ dẫn trả lời gọn.
- Benchmark 31 lượt nối tiếp cùng một prompt: trung bình toàn bộ 4.480 giây, min 2.775, max 6.086; p95 trên 30 lượt sau lượt đầu là 5.702 giây.
- Đây là thời gian hoàn tất qua adapter trực tiếp đến Ollama, không phải TTFT hoặc benchmark tải nhiều người dùng. Model đã được dùng trước benchmark nên lượt đầu không đại diện chắc chắn cho cold start.
- Ollama báo model chiếm 2,703,522,528 byte VRAM; một ảnh chụp `nvidia-smi` trong lúc chạy ghi toàn GPU dùng 3683/6141 MiB. Đây không phải số đo đỉnh.
- Dữ liệu thô local: `data/benchmarks/llm.json` và `data/benchmarks/chat-smoke.json`; thư mục này được gitignore.

### Chất lượng: chưa đạt

Kiểm tra mẫu trong benchmark thấy ví dụ sai như “The movie started since 7:00 PM.” và gọi since/for là động từ. Smoke test điền đúng “were” nhưng giải thích câu điều kiện là “câu mệnh lệnh”; vì thế không thể xem đáp án đúng là bằng chứng giải thích đáng tin cậy. Câu chuyển bị động đúng; câu hỏi điểm kiểm tra không bịa điểm nhưng diễn đạt chưa tự nhiên.

Kết luận: **phần chạy local/Docker đã kiểm chứng; chất lượng gia sư của model hiện tại chưa được chấp nhận**. Chưa nghiệm thu chất lượng toàn phase 2. Cần đánh giá model thay thế hoặc bổ sung ngữ cảnh học liệu đã duyệt rồi chạy bộ đánh giá đa chủ đề; không sửa prompt theo một câu hỏi rồi coi như đã giải quyết độ chính xác chung. Có thể tiếp tục xây backend phase 3 bằng adapter hiện tại, nhưng chưa dùng đầu ra này để dạy/chấm học sinh thực tế.

## Quyết định tạm thời

Dùng Ollama chạy trên host, chat service FastAPI kết nối qua HTTP. Model được cấu hình bằng `OLLAMA_MODEL`, ban đầu là `gemma4:e2b`. Context ứng dụng đặt 4096 token, đầu ra tối đa 512 token để bắt đầu thử nghiệm. Client hiện chỉ dùng văn bản, không streaming, không thực thi tool calls.

Google liệt kê Gemma 4 E2B, E4B, 12B, 26B A4B và 31B. Context tối đa phụ thuộc biến thể: bản nhỏ 128K, bản vừa 256K; không áp dụng 256K cho mọi bản. Khả năng function calling của mô hình không đồng nghĩa hệ thống tác nhân đã được triển khai. [Nguồn Google](https://ai.google.dev/gemma/docs/core).

Ollama có tag `gemma4:e2b`; trang thư viện hiện ghi dung lượng artifact khoảng 7.2 GB. Đây là dung lượng tải, không phải VRAM khi chạy. Chưa chọn E4B/12B làm mặc định vì phải đo trên máy thực tế. [Nguồn Ollama](https://ollama.com/library/gemma4).

Client sử dụng `/api/chat` với `stream: false`; đo hiện tại là thời gian hoàn tất, không dùng để chứng minh mục tiêu phản hồi đầu tiên dưới 3 giây. [API Ollama](https://docs.ollama.com/api/chat).

## Môi trường quan sát được

- Windows; Python 3.14.7.
- RAM: 16,788,992,000 byte, khoảng 15.6 GiB.
- GPU: NVIDIA GeForce RTX 4050 Laptop GPU, 6141 MiB VRAM.
- Ollama: chưa tìm thấy executable trong PATH.
- Docker CLI có mặt, nhưng Docker Desktop Linux engine chưa chạy.

Không kết luận model sẽ vừa VRAM. Cần đo mức sử dụng RAM/VRAM, khả năng offload và độ trễ. Đặc biệt không đánh đồng E2B với tổng bộ nhớ của một model dense 2B.

## Đã triển khai

- Adapter model cấu hình được, không tự tải model hoặc chuyển sang cloud.
- Endpoint liveness, readiness kiểm tra tag model, chat một lượt.
- Giới hạn chiều dài đầu vào; phân biệt lỗi 502/503/504; không trả lỗi backend thô.
- Prompt tiếng Việt; không trả trường thinking của Ollama.
- Script benchmark ghi kết quả thật, không tạo số đo giả khi thiếu model.
- Kiểm thử HTTP mô phỏng các nhánh thành công và thất bại.

## Điều kiện còn lại để nghiệm thu thực tế

1. Cài Ollama và tải tag đã cấu hình; lưu phiên bản runtime và digest model khi đo.
2. Chạy smoke test chat tiếng Việt, sau đó benchmark ít nhất 30 lượt warm, ghi tài nguyên máy và thời gian hoàn tất.
3. Duyệt độ đúng của giải thích trên bộ câu hỏi tiếng Anh lớp 9. Benchmark hiện chỉ có một prompt để kiểm tra kết nối/độ trễ, chưa phải bộ đánh giá chất lượng.
4. So sánh E2B với biến thể khác nếu tài nguyên cho phép; chỉ chốt sau khi đo.
5. Thử OCR trên dữ liệu mẫu ở phase 4; chưa có OCR hoặc bộ học mẫu sinh từ ảnh trong phase này.

Trạng thái: nền tảng code và lựa chọn ban đầu đã có; nghiệm thu suy luận thật còn chờ runtime/model. Chưa chứng minh các mục tiêu hiệu năng phase 1.

## Kết quả kiểm tra code

- `python -m pytest -q`: 13 passed; sử dụng HTTP mock, không suy luận Gemma thật.
- Có cảnh báo deprecation từ TestClient/AnyIO và cảnh báo sandbox không ghi được cache pytest; không có test thất bại.
- `docker compose config --quiet`: thành công; chưa build/chạy container do Docker engine chưa chạy.
- `python -m scripts.benchmark_llm --runs 2`: dừng với thông báo Ollama/model chưa sẵn sàng; không sinh báo cáo hiệu năng.
