# Xây dựng theo từng phase

Đã triển khai luồng MVP phase 5–8 và công cụ kiểm chứng local phase 9; xem [báo cáo và giới hạn](phase-05-09-mvp.md). Phase 9 chưa nghiệm thu sư phạm hoặc tải nhiều người dùng.

Cấu trúc người dùng đề xuất là cấu trúc đích. Tên `__init__.py` và dấu gạch dưới được chuẩn hóa; file chức năng chỉ được thêm khi triển khai, tránh các module rỗng gây hiểu nhầm.

| Phase | Phạm vi | Thư mục/file chính | Điều kiện bàn giao |
|---|---|---|---|
| 1 | Phạm vi MVP | docs/phase-01-mvp-scope.md | Luồng học và tiêu chí nghiệm thu |
| 2 | Runtime mô hình | apps/chat/main.py, config.py, packages/llm, chat.Dockerfile, benchmark | Client/service có test; suy luận thật và đo hiệu năng là cửa kiểm chứng riêng |
| 3 | Nền backend và vai trò tác nhân | apps/api, apps/chat/agents, apps/chat/tools, apps/worker, packages/core, packages/db, packages/storage | Schema, migration, quyền truy cập, điều phối có hợp đồng và test |
| 4 | Nạp và OCR | routers/uploads.py, documents.py, packages/ocr, worker/tasks/ocr_task.py, upload_pipeline.py | Lưu nguồn, nhận dạng, sửa văn bản, xử lý lỗi |
| 5 | Liên kết chương trình | packages/curriculum, data/seeds, curriculum_agent.py | Mapping có nguồn, trạng thái xác minh và khả năng chưa khớp |
| 6 | Tạo bộ học và đánh giá | material_agent.py, quiz_agent.py, teaching_agent.py, routers/materials.py, quizzes.py | Nội dung dẫn nguồn, quiz được kiểm tra, chấm điểm xác định |
| 7 | Hồ sơ và tiến độ | memory_agent.py, memory_tool.py, db/models/memory.py, routers/users.py | Lưu xuyên phiên, ôn lỗi sai, xem/sửa/xóa dữ liệu |
| 8 | Frontend | apps/web | Upload, thư viện, học, quiz, chat và hồ sơ hoạt động xuyên suốt |
| 9 | Kiểm chứng và vận hành | tests/e2e, docs/runbook.md, infra | Đánh giá chất lượng, tải, quyền truy cập, backup/restore |

Kubernetes là tùy chọn sau khi luồng MVP chạy ổn bằng local/Compose. Chưa tạo deployment giả cho các service chưa tồn tại. LICENSE hiện ghi chưa lựa chọn giấy phép phát hành. Không tạo ảnh/PDF giả; sample thật sẽ được sinh hoặc bổ sung cùng phase OCR.
