# BlueStudy — Phase 1: Phạm vi MVP

Trạng thái: Hoàn thành bản đặc tả ban đầu. Chưa triển khai hoặc kiểm chứng bằng phần mềm.

## 1. Mục tiêu

Giúp học sinh lớp 9 Việt Nam biến ghi chú rời rạc, đặc biệt tài liệu có tiếng Anh học thuật, thành tài liệu dễ hiểu và một lượt ôn tập có phản hồi.

Vòng học cốt lõi: **Nạp tài liệu → kiểm tra văn bản → tạo bộ học → làm quiz → ôn lỗi sai → lưu tiến độ.**

## 2. Phạm vi mặc định

- Sản phẩm: web sử dụng được trên điện thoại và máy tính.
- Ngôn ngữ giao diện: tiếng Việt; giải thích thuật ngữ theo dạng Anh–Việt.
- Người dùng chính: học sinh lớp 9.
- Môn thí điểm: Tiếng Anh 9. Đây là lựa chọn khởi đầu có thể điều chỉnh.
- Chưa mặc định bộ sách. Chỉ công bố liên kết chương trình khi có nguồn tham chiếu được kiểm tra; nếu chưa có, hiển thị “Chưa xác minh”.
- Bản thử nghiệm nội bộ có thể dùng một hồ sơ cục bộ. Trước khi mở cho nhiều người dùng, phải có đăng nhập và kiểm tra quyền truy cập dữ liệu.
- Không cố định phiên bản mô hình trong phase 1. Khả năng và thông số Gemma trong lộ trình đầu vào cần được xác minh ở phase chọn mô hình.

## 3. Tính năng bắt buộc và điều kiện nghiệm thu

| Mã | Tính năng | Điều kiện nghiệm thu |
|---|---|---|
| F01 | Nhập tài liệu | Nhận JPEG, PNG, PDF hoặc văn bản dán; giới hạn MVP dự kiến 10 MB/file và 10 trang/PDF; báo rõ lỗi định dạng, dung lượng hoặc PDF có mật khẩu. |
| F02 | Lưu nguồn | Lưu bản gốc, tên file, thời điểm tải lên và chủ sở hữu; từ bộ học mở lại đúng tài liệu nguồn. |
| F03 | Trích xuất và sửa văn bản | Trích xuất chữ theo trang; cho học sinh xem, sửa và xác nhận trước khi tạo bộ học; không âm thầm tạo nội dung khi trích xuất rỗng hoặc thất bại. |
| F04 | Phân loại | Gợi ý loại tài liệu: ghi chú, đề bài hoặc tóm tắt; học sinh có thể sửa nhãn. |
| F05 | Gợi ý chủ đề | Hiển thị chủ đề đề xuất và căn cứ; liên kết được xác minh phải có nguồn chương trình/bộ sách; cho phép chưa liên kết khi không đủ bằng chứng. |
| F06 | Tạo bộ học | Tạo ghi chú có cấu trúc, đề cương ngắn, 5 flashcard và 5 câu trắc nghiệm; phần giải thích bổ sung được phân biệt với nội dung lấy từ nguồn. |
| F07 | Làm và chấm quiz | Mỗi câu có 4 lựa chọn, một đáp án đúng và giải thích; chỉ hiện đáp án sau khi nộp; chấm điểm bằng quy tắc xác định, lưu lần làm và cho xem câu sai. |
| F08 | Chat theo tài liệu | Hỗ trợ “tóm tắt 5 dòng”, “giải thích dễ hơn”, “tạo flashcard”, “tạo quiz”; sử dụng tài liệu đang chọn và nói rõ khi nguồn thiếu thông tin. |
| F09 | Hồ sơ học tập | Lưu mức tiếng Anh do học sinh tự chọn, cách trình bày ưa thích, chủ đề đã học và lịch sử điểm; dữ liệu còn sau khi tải lại ứng dụng. |
| F10 | Ôn tập tiếp theo | Khi đạt dưới 3/5, đề xuất xem lại câu sai và luyện thêm chủ đề tương ứng; đây là quy tắc MVP, không phải kết luận cố định về năng lực. |
| F11 | Kiểm soát dữ liệu | Cho xem, sửa hồ sơ và xóa tài liệu; xóa cả văn bản trích xuất, chỉ mục truy xuất và bộ học phụ thuộc, đồng thời cập nhật tiến độ liên quan. |

## 4. Luồng sử dụng chính

1. Học sinh chọn mức giải thích tiếng Anh: cần hỗ trợ nhiều / cơ bản / khá; có thể bỏ qua và sửa sau.
2. Tải một tài liệu hoặc dán ghi chú, chọn môn và bộ sách nếu biết.
3. Ứng dụng hiển thị tiến trình xử lý, văn bản theo trang và nút sửa lỗi.
4. Học sinh xác nhận văn bản; ứng dụng đề xuất loại tài liệu và chủ đề.
5. Chọn “Tạo bộ học” để nhận ghi chú, đề cương, flashcard và quiz.
6. Học flashcard, làm quiz và nhận giải thích cho từng câu sai.
7. Trang tiến độ lưu kết quả và đề xuất lượt ôn tiếp theo.
8. Chat tiếp với tài liệu bằng các nút yêu cầu nhanh hoặc câu hỏi tự nhập.

Các màn hình tối thiểu: thư viện tài liệu, nhập/kiểm tra tài liệu, không gian học có chat, quiz/kết quả, hồ sơ/tiến độ. Có thể gộp màn hình khi thiết kế giao diện.

## 5. Chất lượng nội dung

- Ghi chú gồm ý chính, thuật ngữ Anh–Việt, ví dụ và điểm dễ nhầm.
- Mỗi mục học và câu hỏi có tham chiếu tới trang hoặc đoạn nguồn liên quan.
- Không đưa vào quiz chấm điểm những thông tin không đủ căn cứ hoặc câu hỏi có nhiều đáp án hợp lý.
- Nội dung OCR không rõ phải được đánh dấu nếu công cụ cung cấp tín hiệu đáng tin cậy; luôn cho phép đối chiếu bản gốc và sửa tay.
- Không tự gắn nhãn “đúng chương trình lớp 9” chỉ dựa trên dự đoán của mô hình.
- Sở thích học được lưu như lựa chọn có thể thay đổi, không coi là một kiểu năng lực cố định.
- Nội dung trong tài liệu tải lên được xử lý như dữ liệu học tập; không được dùng để thay đổi chỉ dẫn hệ thống hay truy cập dữ liệu người khác.

## 6. Chỉ tiêu kiểm chứng

Các mốc thời gian dưới đây là mục tiêu, chưa phải cam kết hiệu năng.

| Chỉ tiêu | Cách đo và mục tiêu ban đầu |
|---|---|
| Tạo bộ học | p95 dưới 30 giây cho một trang in rõ, tối đa 500 từ; đo từ lúc xác nhận tạo bộ học đến khi lưu đủ đầu ra. Đo riêng thời gian tải lên và OCR. |
| Chat | p95 dưới 3 giây đến nội dung phản hồi đầu tiên với câu hỏi đơn giản trên tài liệu đã xử lý; đo riêng thời gian hoàn tất câu trả lời. |
| Bộ dữ liệu đánh giá | 50 tài liệu có quyền sử dụng, gồm ảnh rõ, ảnh khó đọc, PDF có text và PDF scan; tối thiểu 30 tài liệu một trang in rõ cho đo hiệu năng. |
| Kiểm tra nội dung | Người duyệt chấm độ đúng, độ rõ và sự phù hợp trình độ theo thang 1–5; mục tiêu ít nhất 90% bộ học đạt từ 4/5 ở cả ba tiêu chí. |
| Đáp án quiz | Toàn bộ đáp án trong tập kiểm thử phát hành được người duyệt kiểm tra; sửa mọi lỗi đáp án phát hiện trước khi cho học sinh thử. |
| Hoàn thành luồng học | Ít nhất 4/5 người thử hoàn thành từ tải tài liệu đến xem kết quả quiz mà không cần người hướng dẫn thao tác. |
| Tính bền vững dữ liệu | Tải lại ứng dụng vẫn xem được nguồn, bộ học và kết quả; lỗi tạo nội dung không làm mất tài liệu nguồn. |

Ghi lại phần cứng, mô hình, kích thước tài liệu và mức tải đồng thời trong mỗi báo cáo hiệu năng. Trước khi thử nghiệm, cố định cấu hình đo; không suy rộng kết quả một người dùng sang tải thực tế.

## 7. Ngoài phạm vi MVP

- Truyện minh họa, infographic tự sinh và sơ đồ phức tạp.
- Hỗ trợ toàn bộ môn học/bộ sách ngay khi ra mắt.
- Ứng dụng di động native, chạy mô hình trên thiết bị và chế độ offline đầy đủ.
- Fine-tuning, nhận dạng công thức viết tay chuyên sâu và chấm tự luận mở.
- Cổng giáo viên, phụ huynh, thanh toán và chia sẻ công khai.
- Triển khai mỗi tác nhân thành một microservice riêng.

## 8. Vai trò AI cần có ở các phase triển khai

Hệ thống cần các vai trò phân loại, liên kết chương trình, tạo tài liệu, gia sư, đánh giá, ghi nhớ và truy xuất. MVP có thể tổ chức chúng thành các mô-đun trong một backend với bộ điều phối rõ ràng. Phân quyền, lưu dữ liệu và tính điểm trắc nghiệm do mã ứng dụng kiểm soát.

Phase chọn mô hình phải xác minh phiên bản Gemma, khả năng tiếng Việt, đầu ra có cấu trúc, yêu cầu phần cứng và độ trễ trước khi quyết định. Phase này không giả định mọi vai trò phải gọi mô hình riêng.

## 9. Lộ trình dự kiến 6 tuần

Đây là khung lập kế hoạch, cần điều chỉnh theo nhân lực và kết quả thử mô hình.

| Tuần | Kết quả cần có |
|---|---|
| 1 | Chốt đặc tả, chọn nguồn chương trình, kiểm chứng mô hình/OCR và thiết kế luồng màn hình. |
| 2 | Nhập tài liệu, lưu nguồn, trích xuất và sửa văn bản. |
| 3 | Phân loại, liên kết chủ đề có căn cứ và tạo ghi chú/flashcard. |
| 4 | Quiz, chấm điểm, chat theo nguồn và xử lý lỗi. |
| 5 | Hồ sơ, tiến độ, ôn lỗi sai, xóa dữ liệu và kiểm tra quyền truy cập. |
| 6 | Đánh giá nội dung, đo hiệu năng, thử với người dùng và sửa lỗi. |

## 10. Điều kiện hoàn thành MVP

- F01–F11 hoạt động trong một luồng liên tục, có kiểm thử các nhánh lỗi chính.
- Có dữ liệu chương trình được kiểm tra cho phạm vi thí điểm; trường hợp không khớp phải hiển thị trung thực.
- Đã kiểm thử tải tài liệu lỗi, OCR rỗng, timeout mô hình, tạo bộ học lại và tải lại trang.
- Nếu có nhiều người dùng, đã kiểm thử việc không thể đọc/sửa/xóa nguồn, bộ học hoặc lịch sử của người khác.
- Có báo cáo chất lượng và hiệu năng, chỉ rõ chỉ tiêu đạt/chưa đạt cùng giới hạn của bản thử nghiệm.
- Người học xem được nguồn, sửa được hồ sơ và xóa được dữ liệu của mình.

## 11. Bàn giao phase 1

Đã xác định phạm vi, luồng sử dụng, tiêu chí nghiệm thu, phần hoãn lại và kế hoạch kiểm chứng. Chưa có ứng dụng, tích hợp AI hoặc kết quả benchmark.

Bước tiếp theo — phase 2: xác minh mô hình và phương án chạy; kiểm kê phần cứng/môi trường, thử OCR và một bộ học mẫu trước khi chốt stack triển khai.
