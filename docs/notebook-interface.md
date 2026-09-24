# Giao diện sổ tay BlueStudy

Thiết kế lại dựa trên ảnh tham khảo người dùng và hai trang:

- [Shipping Is Not One Cycle](https://nuesj4c5tehcg.kimi.page/): nền giấy, khoảng thở và typography serif.
- [Attention Residuals — Interactive Architecture Demo](https://7inif7p6jcz2y.kimi.page/): nền kẻ ô, sơ đồ tương tác và điều khiển khám phá từng bước.

Ảnh người dùng là tham chiếu bố cục chính: mục lục bên trái, bốn ô thống kê, sơ đồ ghi chú pastel, khung bài học bên phải, ghi chú nhỏ và các trang liên quan. Thương hiệu và nội dung giữ là BlueStudy/Tiếng Anh lớp 9.

## Cách sử dụng

Mở <http://localhost:8000/app/>. Khi chưa có phiên học, ứng dụng hiển thị vở mẫu **Local community** được biên soạn sẵn. Quiz mẫu chấm ngay trong trình duyệt, không gọi mô hình, không tạo tài liệu hoặc lưu điểm vào tài khoản.

Để học thật, bấm **Đăng nhập** và nhập mã tài khoản local. Trong **Tủ tài liệu**, thêm ảnh/PDF/ghi chú, kiểm tra và xác nhận văn bản, rồi bắt đầu học. Bấm **Tạo bộ ôn tập** để tạo các trang từ nguồn. Các chức năng upload, OCR, tạo học liệu, chat, chấm điểm và hồ sơ tiếp tục dùng API hiện có.

Sơ đồ kết nối bản nguồn với các flashcard của bộ học. Các đường nối chỉ biểu thị chung nguồn; không suy diễn quan hệ tiên quyết hoặc coi đây là knowledge graph đã kiểm chứng. Tìm kiếm làm nổi bật trang khớp; chế độ danh sách là cách thay thế để duyệt các trang. Có thu/phóng, đặt lại, chuyển trang và tự chuyển mỗi 3 giây khi chủ động bấm khám phá. Đổi màn hình sẽ dừng bộ hẹn giờ.

Khung bên phải có ba tab: **Bài học**, **Hỏi BlueStudy**, **Luyện tập**. Lựa chọn quiz được giữ khi đổi tab hoặc đọc trang khác trong cùng phiên hiển thị. Quiz thật gửi đủ 5 lựa chọn lên backend; đáp án và giải thích chỉ trả về sau khi nộp. Tải lại trang khôi phục học liệu và dữ liệu đã lưu; bài làm chưa nộp không được lưu.

Trên mobile, khung bài học nằm dưới sơ đồ; có thể kéo ngang sơ đồ hoặc chuyển sang danh sách. Có phím tắt điều hướng tab bằng trái/phải/Home/End, skip link, focus rõ ràng, dialog native và hỗ trợ giảm chuyển động. Font Lora và Be Vietnam Pro được lưu local với giấy phép OFL trong `apps/web/fonts`; không cần kết nối Google Fonts lúc sử dụng.

## File và kiểm chứng

- `apps/web/index.html`: khung ứng dụng, sidebar, breadcrumb và hướng dẫn.
- `apps/web/notebook.css`: kiểu giấy/sổ tay, sơ đồ và responsive.
- `apps/web/notebook.js`: dashboard, sơ đồ, reader, demo và lộ trình.
- `apps/web/app.js`: client API, xác thực, upload/review, hồ sơ và tiến độ.
- `scripts/smoke_notebook.py`: kiểm thử Chrome không gọi AI; thêm `--live` để kiểm thử một lần tạo học liệu thật.
- `scripts/smoke_web.py`: entry point tương thích để chạy kiểm thử notebook có dữ liệu thật.

Đã kiểm tra Chrome desktop 1440 px và mobile 390 px: tìm kiếm, danh sách, zoom/reset, chọn node, lật thẻ, chạy/dừng từng bước, tab/bàn phím, quiz mẫu, dialog; quiz mẫu không gửi POST. Luồng đăng nhập → tài liệu → phiên học → chọn chủ đề → Qwen tạo học liệu → quiz server → tiến độ → hồ sơ → tải lại → đăng xuất đã qua. 10 test hồi quy API học liệu/phân quyền đã qua.

Ảnh chụp local ở `data/benchmarks/design/notebook-desktop.png`, `notebook-mobile.png`, `notebook-quiz.png` và `notebook-live.png`; không commit artifact thử nghiệm.
