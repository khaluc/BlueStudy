# Chat AI

Mở `/app/#chat` hoặc chọn **Chat AI** trong menu để hỏi bài ngay, không cần tải tài liệu trước. Bản Docker local tự mở tài khoản mặc định, không có bước nhập mã. Tài liệu, lịch sử và tiến độ vẫn thuộc tài khoản cũ.

API bật chế độ này qua `LOCAL_ACCESS_FILE`, trỏ đến tệp tài khoản được mount chỉ đọc. `/local-session` cấp cookie HttpOnly, SameSite Strict; chỉ chấp nhận host local và yêu cầu cùng origin. Khi không cấu hình, API vẫn yêu cầu bearer token. Các trình duyệt dùng bản local này cùng chia sẻ một góc học tập.

- Tin nhắn và câu trả lời lưu trong PostgreSQL theo tài khoản. Menu lịch sử mở lại cuộc trò chuyện; nút Chat mới tạo luồng riêng.
- Bấm **Tạo quiz trắc nghiệm** hoặc nhập “tạo quiz”, “quiz me on this”: quiz 5 câu xuất hiện ngay trong chat với các ô chọn A–D. Nút **Nộp bài** chỉ bật khi trả lời đủ; máy chủ chấm điểm, trả giải thích và lưu kết quả để xem lại sau khi tải trang. Mỗi quiz lưu một lần nộp; tạo quiz mới để luyện tiếp. Kết quả này nằm trong lịch sử chat, chưa cộng vào sổ tiến bộ của bộ ôn tập.
- Bảng hoạt động ghi ba bước thực tế: **Classifier Agent** nhận diện ý định bằng quy tắc; **Source Agent** lấy đoạn nguồn, đọc ảnh qua Qwen-VL hoặc lấy hội thoại gần nhất; **Quiz Agent** gọi model tạo câu hỏi, kiểm tra cấu trúc/trích dẫn rồi lưu đáp án riêng. Đây là các bước xử lý có lưu trạng thái, không phải ba model chạy song song. Dữ liệu từ ảnh/hội thoại vẫn cần kiểm tra độ chính xác.
- Khi nguồn là đề thi, cả quiz chat và bộ ôn tập dùng bản nguồn học đã lọc đầu đề: mã đề, thông tin thí sinh, số trang và thời gian làm bài không được dùng làm mục tiêu ôn. Bản OCR lưu trữ vẫn giữ nguyên. Với bài điền từ, ưu tiên từ vựng, cụm từ, ngữ pháp và câu có chỗ trống; giữ nguyên các mốc thời gian trong đoạn đọc nếu chúng là ngữ cảnh ngôn ngữ. Kiểm tra bằng quy tắc chặn một số dạng câu hỏi hành chính và câu hỏi ngoài trọng tâm điền từ; không thay thế thẩm định đáp án của giáo viên. Chỉ tạo từ đoạn nguồn đang chọn, không giả định có các trang/đáp án chưa tải lên.
- Nút `+` nhận ảnh/PDF. Với PNG/JPEG, chọn ảnh, nhập câu hỏi và bấm **Gửi**: Qwen-VL local xem trực tiếp ảnh rồi trả lời trong chat, không yêu cầu xác nhận OCR. Nếu không nhập câu hỏi, hệ thống yêu cầu đọc và giải thích ảnh. Ảnh còn đính kèm được dùng cho câu hỏi tiếp theo; chọn **Bỏ ảnh** để quay lại chat văn bản.
- Với PDF, tệp gốc được lưu trong thư viện; sau trích xuất, chọn **Kiểm tra văn bản**, sửa và xác nhận đoạn nguồn tối đa 2.400 ký tự.
- Nguồn đã xác nhận được dùng cho các câu hỏi tiếp theo. Có thể bỏ đính kèm hoặc tạo bộ ôn tập qua luồng hiện có.
- Bảng hoạt động hiển thị trạng thái hàng đợi, nguồn và model thực tế trả lời. Đây không phải luồng suy nghĩ nội bộ của model. Giao diện cập nhật bằng polling, chưa truyền từng token.
- Model nhận tối đa ba lượt hội thoại gần nhất cùng nguồn. Giao diện hiển thị tối đa 100 lượt gần nhất và danh sách 50 cuộc trò chuyện mới nhất.
- Xóa chat xóa tin nhắn; tài liệu gốc vẫn ở thư viện. Xóa tài liệu ngắt liên kết nguồn, không tự xóa nội dung chat đã lưu.

API yêu cầu bearer token: `GET/POST /chat/threads`, `GET/PATCH/DELETE /chat/threads/{id}`, `GET/POST /chat/threads/{id}/turns`. POST turn trả 202; worker xử lý với model đã cấu hình. Mỗi luồng chỉ có một lượt đang chờ, trả 409 khi gửi thêm hoặc thay nguồn/xóa lúc đang xử lý.

Migration `0005` thêm `chat_threads`, `chat_turns`; `0006` thêm liên kết ảnh cho từng lượt. Gửi `image_document_id` cùng `message` vào endpoint turns để hỏi ảnh. Upload với `purpose=chat_image` lưu ảnh đã kiểm tra định dạng và bỏ hàng đợi OCR. Worker đọc bytes gốc, gửi kèm câu hỏi tới Ollama; lỗi vision được báo, không thay bằng model chỉ nhận văn bản.

Migration `0007` bổ sung quiz, kết quả nộp bài và ngữ cảnh xử lý riêng trên máy chủ. API turns luôn loại đáp án và giải thích khỏi quiz chưa nộp. `POST /chat/threads/{thread_id}/turns/{turn_id}/quiz-submit` nhận `answers` (5 số nguyên 0–3); gửi lại cùng đáp án trả cùng kết quả, đổi đáp án sau khi nộp trả 409.

Kiểm tra: `python -m pytest -q`, `python -m scripts.smoke_inline_quiz` (tạo quiz thật), `python -m scripts.smoke_chat_image` (gọi Qwen-VL thật), `python -m scripts.smoke_local_access`.
