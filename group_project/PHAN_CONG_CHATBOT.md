# Khung Ý Tưởng + Phân Công Chi Tiết (RAG Chatbot)

## 1) Mục tiêu nhóm

- Xây dựng chatbot hỏi đáp về pháp luật ma túy và tin tức liên quan.
- Câu trả lời có citation, có hội đáp tiếp nối (follow-up), và hiển thị nguồn trích dẫn.
- Có bộ evaluation độc lập để đo chất lượng pipeline theo đúng yêu cầu 2.

## 2) Khung ý tưởng sản phẩm

### Luồng xử lý tổng quan

1. Thu thập và chuẩn hóa dữ liệu (legal + news).
2. Tạo chunks, indexing và retrieval (semantic + lexical + rerank + page index).
3. Pipeline trả lời: retrieve -> rerank -> generate + citation.
4. Frontend chat để người dùng hỏi đáp, xem citation và lịch sử hỏi đáp.
5. Evaluation pipeline để đo faithfulness, relevance, recall, precision và so sánh A/B.

### Hướng chia giai đoạn

- Giai đoạn 1 (Nền tảng): dữ liệu + pipeline retrieval hoạt động.
- Giai đoạn 2 (Sản phẩm): chatbot UI và luồng hỏi đáp đầu-cuối.
- Giai đoạn 3 (Chất lượng): evaluation + báo cáo kết quả + tài liệu demo.

## 3) Phân công chi tiết theo thành viên

## 3.1 Thái Minh - Thu thập tài liệu, làm data

### Nhiệm vụ chính

- Thu thập văn bản pháp lý và tin tức liên quan đến ma túy.
- Làm sạch dữ liệu đầu vào, loại bỏ nội dung trùng lặp, đúng format.
- Chuẩn hóa markdown/text để đưa vào pipeline chunking.

### Đầu ra cần bàn giao

- Thư mục dữ liệu đầy đủ trong data/landing và data/standardized.
- Danh sách nguồn và quy tắc lọc dữ liệu.
- Mẫu file đầu vào đã được chuẩn hóa để team index trực tiếp.

## 3.2 Hoàng - Làm chatbot

### Nhiệm vụ chính

- Nối retrieval pipeline với generation để trả lời có citation.
- Hỗ trợ conversation memory cho follow-up questions.
- Đồng bộ API/hàm để frontend gọi và hiển thị source documents.

### Đầu ra cần bàn giao

- Luồng hỏi đáp chatbot chạy được end-to-end.
- Hàm trả về kết quả dạng: answer + sources + metadata cần thiết.
- Bản chat demo để team test nhanh trước khi tích hợp frontend.

## 3.3 Tâm - Docs hướng dẫn dùng app, tài liệu demo

### Nhiệm vụ chính

- Viết hướng dẫn cài đặt và chạy app cho giảng viên/người demo.
- Viết kịch bản demo ngắn gọn: input mẫu, output mong đợi, điểm nhấn.
- Tổng hợp mô tả kiến trúc và cách sử dụng các module.

### Đầu ra cần bàn giao

- Tài liệu hướng dẫn sử dụng app trong README/tài liệu bổ sung.
- Tài liệu demo buổi báo cáo (các bước + câu hỏi mẫu + expected behavior).

## 3.4 Giáp - Đánh giá chất lượng chatbot (tham chiếu yêu cầu 2)

### Nhiệm vụ chính

- Tạo golden dataset tối thiểu 15 cặp Q&A (question, expected_answer, expected_context).
- Triển khai evaluation pipeline theo 1 framework (ưu tiên RAGAS hoặc DeepEval).
- Đo 4 metric bắt buộc:
  - Faithfulness
  - Answer Relevance
  - Context Recall
  - Context Precision
- Chạy so sánh A/B ít nhất 2 cấu hình:
  - Ví dụ: có reranking vs không reranking
  - Hoặc hybrid retrieval vs dense-only
- Phân tích mẫu lỗi (worst performers) và đề xuất cải tiến.

### Đầu ra cần bàn giao

- group_project/evaluation/golden_dataset.json
- group_project/evaluation/eval_pipeline.py
- group_project/evaluation/results.md

## 3.5 Quang Minh - Frontend

### Nhiệm vụ chính

- Xây dựng giao diện chat (Streamlit/Gradio/Chainlit).
- Hiển thị lịch sử hỏi đáp, citation và danh sách source documents.
- Tối ưu trải nghiệm demo: dễ nhập câu hỏi, dễ xem nguồn, dễ thử follow-up.

### Đầu ra cần bàn giao

- Frontend chat tích hợp chatbot backend.
- Giao diện chạy ổn định trên local để demo trong lớp.

## 4) Checklist phối hợp giữa các vai trò

- Thái Minh bàn giao data standardized trước khi index chốt.
- Hoàng và Quang Minh thống nhất contract dữ liệu cho câu trả lời + citation.
- Giáp chốt format output của pipeline để eval script đọc được thống nhất.
- Tâm chốt tài liệu hướng dẫn sau khi frontend và eval đạt mức tối thiểu để demo.

## 5) Định nghĩa hoàn thành

- Chatbot trả lời được câu hỏi, có citation và follow-up memory.
- Frontend sử dụng được trong demo thực tế.
- Evaluation có điểm số, có so sánh A/B, có nhận xét cải tiến.
- Có tài liệu hướng dẫn dùng app và kịch bản demo rõ ràng.
