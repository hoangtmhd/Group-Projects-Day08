# Hướng Dẫn Cài Đặt và Chạy Frontend (Giao diện Chatbot)

Thư mục `frontend` chứa toàn bộ mã nguồn liên quan đến giao diện người dùng (UI) cho hệ thống RAG Chatbot Pháp luật Ma Túy, được xây dựng bằng **Streamlit**.

## 1. Cấu trúc thư mục

- `frontend/app.py`: Tệp tin chính chứa logic giao diện Streamlit, xử lý lịch sử hội thoại (Conversation Memory) và giao tiếp với `RAGChatbot` ở backend.

*(Lưu ý: Giao diện sẽ tự động tìm và import module backend `chatbot.py` từ thư mục cha `group_project/chatbot.py`)*

## 2. Yêu cầu hệ thống (Prerequisites)

Đảm bảo bạn đã cài đặt Python (phiên bản >= 3.10) và đã cài đặt đủ các thư viện phụ thuộc của dự án ở thư mục gốc.

Các thư viện chính cần thiết:
- `streamlit`
- `google-generativeai` (nếu dùng model Gemini)
- `openai` (nếu dùng model GPT)

Để cài đặt tự động, bạn mở Terminal tại **thư mục gốc của toàn dự án** (`Group-Projects-Day08-main`) và chạy:
```bash
pip install -r requirements.txt
```

Nếu gặp lỗi thiếu module `google.generativeai` trong quá trình chạy, hãy cài đặt bổ sung:
```bash
pip install google-generativeai
```

## 3. Cách chạy Giao diện (Run the app)

**Bước 1:** Mở Terminal (Command Prompt, PowerShell hoặc VS Code Terminal).

**Bước 2:** Di chuyển vào thư mục `frontend` bằng lệnh:
```bash
cd group_project/frontend
```

**Bước 3:** Khởi chạy Streamlit bằng lệnh:
```bash
streamlit run app.py
```
*(Nếu hệ điều hành của bạn không nhận diện được lệnh `streamlit`, hãy thử dùng: `python -m streamlit run app.py`)*

**Bước 4:** Trình duyệt web mặc định của bạn sẽ tự động mở lên với đường dẫn `http://localhost:8501`. Giao diện AI Chatbot đã sẵn sàng để bạn trải nghiệm!

## 4. Các tính năng chính của Giao diện
- **Premium UI:** Giao diện Dark Mode sang trọng, thân thiện với các hiệu ứng nổi bật (Animations, Hover effects).
- **Hội thoại thông minh:** Ghi nhớ ngữ cảnh trò chuyện (Follow-up Memory). Bạn có thể hỏi các câu hỏi tiếp nối tự nhiên.
- **Minh bạch thông tin (Citations):** Mỗi câu trả lời đều đi kèm với nút "🔍 Trích xuất từ X tài liệu nguồn" cho phép bạn xem trực tiếp các điều luật, đoạn văn bản pháp luật mà AI đã dùng làm căn cứ sinh ra câu trả lời.
- **Tùy chỉnh RAG Pipeline:** Cung cấp Sidebar để điều chỉnh số lượng tài liệu trích xuất (Top K), ngưỡng tương đồng (Score Threshold) và bật/tắt tính năng Reranking trực tiếp khi đang chạy.
