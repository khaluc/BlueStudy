# Phase 5–9: luồng học MVP

## Phạm vi đã triển khai

| Phase | Chức năng |
|---|---|
| 5 | 12 chủ đề Tiếng Anh 9 Global Success; gợi ý theo từ khóa có bằng chứng; trả `unmatched` khi không có căn cứ; học sinh chọn/sửa/bỏ chủ đề của phiên học |
| 6 | Tạo tóm tắt, ghi chú, 5 flashcard và 5 câu trắc nghiệm từ bản chụp văn bản đã xác nhận; kiểm tra JSON, số lượng, lựa chọn khác nhau, trích dẫn nguồn; xáo trộn đáp án một lần rồi lưu; chấm điểm xác định ở server |
| 7 | Lưu mức hỗ trợ ngôn ngữ, hoạt động ưa thích, phiên học, học liệu và các lượt làm bài; tổng hợp điểm theo chủ đề; ôn câu sai theo lượt mới nhất; truy xuất tối đa 3 lỗi gần đây cho tác nhân giảng dạy; tìm kiếm tài liệu có giới hạn quyền sở hữu |
| 8 | Web tiếng Việt tại `/app/`: đăng nhập bằng mã tài khoản local, tải ảnh/PDF, dán ghi chú, sửa/xác nhận OCR, chọn đoạn học, học liệu, quiz, chat, hồ sơ và tiến độ |
| 9 | Bộ kiểm thử API/quyền truy cập/schema; script thử Qwen thật; kiểm thử Chrome opt-in; sao lưu nhất quán và thử khôi phục vào DB tạm |

Frontend MVP sử dụng HTML/CSS/JavaScript thuần, được FastAPI phục vụ cùng origin. Chưa chuyển sang Next.js như cấu trúc đích ban đầu. Cách này không cần thêm Node/service để chạy thử và vẫn giữ API độc lập để thay frontend sau.

## Khởi động và sử dụng

Chạy từ thư mục `padayon`:

```powershell
docker compose up -d --build
```

Mở <http://localhost:8000/app/>. Mã truy cập tài khoản local nằm ở trường `token` trong `data/local-demo.json`; đây là token học sinh, không phải `DASHSCOPE_API_KEY`. Nếu chưa có tài khoản, dùng script provision trong runbook. Không đưa file này lên Git hoặc gửi qua chat. Giao diện giữ token trong `sessionStorage`, đăng xuất sẽ xóa token của tab.

Luồng: thêm tài liệu → kiểm tra văn bản → xác nhận → chọn đoạn tối đa 2.400 ký tự → bắt đầu học → chọn chủ đề → tạo bộ ôn tập → nộp quiz → xem tiến độ. Đối với PDF dài, tạo nhiều phiên từ các khoảng văn bản khác nhau. Phiên học giữ bản chụp nguồn nên sửa tài liệu không làm thay đổi bộ học cũ.

## Mô hình và nguồn

- Chat và tạo bộ học: Qwen Cloud theo `.env`, hiện `qwen3.8-max-0902`.
- Tạo bộ học dùng chế độ JSON riêng, tắt thinking, ngân sách tối đa 8.192 token và giới hạn 90 giây. Chat thông thường giữ cấu hình thinking hiện có. Không trả reasoning cho người học.
- Nếu lỗi cloud và cho phép fallback, dùng Ollama local; thông tin provider/fallback được lưu trong provenance. Local generation được cấp ngữ cảnh 8.192 và đầu ra 4.096 token; vẫn có thể không đạt schema hoặc chất lượng.
- OCR tiếp tục chạy Qwen3-VL **local** qua Ollama; không chuyển ảnh sang cloud vision.
- Danh sách chủ đề tham khảo [HEID / Global Success](https://heid.vn/chinh-phuc-tu-vung-tieng-anh-lop-9-theo-chu-de-da-dang/). Chỉ đối chiếu tên/chủ đề unit. Từ khóa gợi ý do dự án biên soạn; chưa phải mapping đầy đủ chuẩn đầu ra Bộ GDĐT và chưa phủ các bộ sách khác.
- Registry chạy ở `packages/curriculum/grade9_topics.py`; bản seed để kiểm tra ở `data/seeds/grade9_curriculum.json`.

## Hợp đồng và dữ liệu

Migration `0003`: bảng `materials`, `quiz_attempts`, job `generate_bundle`. Migration `0004`: hoạt động học ưa thích và chủ đề do người học chọn.

Học liệu lưu khóa đáp án riêng trong DB. API GET học liệu không trả `correct`, `explanation`, `quote` của quiz; endpoint job chỉ trả ID học liệu và provenance. Sau khi nộp 5 đáp án hợp lệ, server trả điểm và giải thích. Các đáp án có thể được suy ra từ ghi chú/flashcard: đây là quiz tự luyện, không phải hệ thống thi chống gian lận.

Điểm tổng hợp dựa trên tối đa 100 lượt gần nhất. Nhận xét theo chủ đề cần ít nhất 3 lượt; các lượt có thể là làm lại cùng bộ học, vì vậy không coi là chứng nhận thành thạo. Ôn lỗi sai dùng tối đa 20 lượt gần nhất và bỏ lỗi đã trả lời đúng ở lượt mới hơn. Bộ nhớ cho giảng dạy dùng tối đa 5 lượt gần nhất. Học sinh có thể sửa hồ sơ/chủ đề, xóa lịch sử điểm hoặc xóa tài liệu cùng các dữ liệu học phụ thuộc.

Mọi nội dung AI mang trạng thái `unreviewed`. Trích dẫn tồn tại trong nguồn chỉ chứng minh sự hiện diện của đoạn dẫn, không tự động chứng minh câu hỏi/đáp án đúng về ngữ nghĩa.

## Kiểm chứng

Kết quả thực tế và giới hạn: [báo cáo phase 9](phase-09-verification.md).

```powershell
python -m pytest -q -p no:cacheprovider --tb=short
python -m scripts.smoke_study
python -m pip install -r requirements-e2e.txt
python -m scripts.smoke_web
python -m scripts.smoke_web_upload
python -m scripts.smoke_backup
python -m scripts.backup
python -m scripts.verify_backup data/backups/<thu-muc-vua-tao>
```

`smoke_study` và `smoke_web` gọi mô hình thật, có thể phát sinh phí cloud. Không chạy trong bộ test mặc định. Browser dùng Chrome đã cài; ảnh chụp và kết quả kiểm tra lưu trong `data/benchmarks/`, không commit. Tài liệu thử được xóa sau khi kết thúc; script browser khôi phục hồ sơ ban đầu.

Backup dừng tạm API/worker đang chạy, chụp PostgreSQL và volume tài liệu rồi khởi động lại các service đó. Bản sao không chứa `.env`; lưu riêng thông tin triển khai/khóa truy cập bằng phương thức phù hợp. `verify_backup` kiểm tra checksum, restore DB vào tên ngẫu nhiên `padayon_restore_<uuid>`, đối chiếu SHA-256 nguồn, rồi xóa DB tạm; không ghi đè database đang dùng. Không giải nén archive lên hệ thống khi kiểm tra.

## Giới hạn còn lại trước khi triển khai rộng

- Chưa có đánh giá chất lượng bởi giáo viên hoặc thử nghiệm với học sinh; một mẫu API thành công không chứng minh chất lượng chương trình lớp 9.
- Chưa chạy kiểm thử tải nhiều người dùng hoặc đo SLA. Queue giữ transaction khi suy luận; cần thay đổi kiến trúc khi tăng tải.
- Chưa có đăng ký/khôi phục tài khoản, token rotation, giới hạn chi phí theo tài khoản hoặc triển khai HTTPS công khai. Bản Compose chỉ bind loopback, dành cho thử nghiệm local.
- Chưa có lịch ôn cách quãng, truy xuất ngữ nghĩa, truyện hoặc sơ đồ kiến thức. Điểm mạnh/yếu hiện là nhận xét từ lịch sử quiz, không suy đoán tính cách hay kiểu học cố định.
- Kubernetes, chuyển frontend sang Next.js và mở rộng sách/môn nằm ngoài bản chạy MVP này.

Phase 9 mới là kiểm chứng kỹ thuật local; chỉ đánh dấu nghiệm thu sản phẩm sau khi hoàn thành đánh giá sư phạm và thử tải.
