# Kết quả bài lab

Đã sinh và review đủ năm báo cáo thật bằng `openai:gpt-6-luna` trong Docker. Mỗi chủ đề có `.md`, `.sources.json`, `.meta.json` và ít nhất ba họ nguồn arxiv, hf-search, web.

| Báo cáo | Nguồn lượt sinh ban đầu | Task lượt sinh ban đầu | Thời gian lượt sinh ban đầu |
|---|---:|---:|---:|
| [World model](../reports/survey-about-world-model.md) | 12 | 6 | 406.6 giây |
| [RL for LLM reasoning](../reports/survey-about-reinforcement-learning-for-llm-reasoning.md) | 13 | 8 | 1235.0 giây |
| [LLM agents and tool use](../reports/survey-about-llm-agents-and-tool-use.md) | 15 | 6 | 314.7 giây |
| [Video and multimodal generation](../reports/survey-about-video-and-multimodal-generation.md) | 16 | 13 | 427.8 giây |
| [Efficient inference and small language models](../reports/survey-about-efficient-inference-and-small-language-models.md) | 20 | 4 | 312.0 giây |

Các file liên kết là phiên bản sau review; video hiện có 17 nguồn sau khi thêm bài gốc VBench, các report khác giữ số nguồn trong bảng. Trong metadata hiện tại, thống kê trên cùng đo **lượt sửa bằng agent**; `previous_run` giữ lượt sinh ban đầu trong bảng. `previous_artifacts` giữ SHA-256 của bộ tệp gốc. Hai ngày công bố SLM được sửa bằng mã trong sandbox, không gọi thêm LLM; metadata ghi riêng ở `citation_metadata_repair`.

Đã đọc toàn bộ năm report và sửa lỗi số liệu, ngày công bố, phạm vi benchmark, điều khiển chuyển động, dữ liệu huấn luyện. Xem [review chi tiết và giới hạn](REPORT_REVIEW.md), [ghi chú từng lượt sửa](review/) và [bằng chứng truy cập nguồn](source-review-receipt.json). References do finalizer sinh trong sandbox; report/source ở host đúng bytes tải về. .gitattributes giữ nguyên bytes khi Git checkout trên Windows.

Kiểm tra cuối: 35 test offline pass; self_check.py xác nhận năm bộ tệp và git/secrets OK; bốn module cung cấp sẵn không sửa; quét tệp nộp và lịch sử Git không thấy mẫu khóa API; Docker sandbox đã dọn. Bằng chứng/hash hiện tại: [final-verification.json](final-verification.json), [VERIFICATION.md](VERIFICATION.md), [docker-cleanup.json](docker-cleanup.json). Các biên bản cũ giữ phạm vi lịch sử; giảng viên vẫn chấm phần nội dung theo rubric.

Chỉ cần khóa OpenAI và Docker Desktop. Exa không cần khóa riêng; tìm kiếm dự phòng dùng cùng model/key OpenAI và cũng tính phí API. Khóa luôn ở host, .env không đưa lên Git. Token metadata chỉ gồm lead, chưa gồm subagent, tìm kiếm dự phòng hoặc lượt thất bại; tổng chi phí không xác định. Hai lượt LLM-agents thất bại không tính vào metadata thành công; bản nháp đã được researcher mới kiểm chứng lại trong sandbox trước khi chấp nhận.

Người dùng đã cho phép review, sửa, commit và push lên repo hiện tại. Kết quả công bố được xác nhận bằng lịch sử commit trên GitHub.

Kiểm tra lại không gọi LLM:

```powershell
.venv/Scripts/python.exe scripts/verify_submission.py
```

Tạo lại báo cáo sẽ dùng API và thay bộ tệp tương ứng:

```powershell
.venv/Scripts/python.exe research.py "survey about world model"
```
