import streamlit as st
import os
import sys
from pathlib import Path

# Đảm bảo import được RAGChatbot từ chatbot.py
sys.path.insert(0, str(Path(__file__).parent))
from chatbot import RAGChatbot

# Thiết lập tiêu đề trang và cấu hình
st.set_page_config(
    page_title="Hệ Thống Trợ Lý Luật Ma Túy - Nhóm RAG v2",
    page_icon="⚖️",
    layout="wide"
)

# Khởi tạo chatbot backend
@st.cache_resource
def load_chatbot():
    return RAGChatbot()

bot = load_chatbot()

# CSS tùy chỉnh để làm giao diện đẹp hơn
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .main {
        max-width: 1200px;
        margin: 0 auto;
    }
    .stChatFloatingInputContainer {
        bottom: 20px;
    }
    .chat-source-box {
        background-color: #f9f9f9;
        border-left: 5px solid #ff4b4b;
        padding: 10px;
        margin: 5px 0;
        border-radius: 4px;
        font-size: 0.9rem;
    }
    .score-badge {
        background-color: #e1e4e8;
        padding: 2px 6px;
        border-radius: 10px;
        font-weight: bold;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚖️ Trợ Lý Pháp Luật & Tin Tức Phòng Chống Ma Túy")
st.caption("Ứng dụng RAG Chatbot có trích dẫn nguồn & Lịch sử hội thoại (Conversation Memory)")

# Sidebar cấu hình tham số RAG
st.sidebar.header("Cấu Hình RAG Pipeline")
top_k = st.sidebar.slider("Số lượng tài liệu truy vấn (Top K Chunks)", min_value=1, max_value=10, value=5)
score_threshold = st.sidebar.slider("Ngưỡng điểm tương đồng (Score Threshold)", min_value=0.0, max_value=1.0, value=0.3, step=0.05)
use_reranking = st.sidebar.checkbox("Sử dụng Reranking (Jina AI / Cross-Encoder)", value=True)

# Lịch sử hội thoại lưu trong session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Nút xóa lịch sử chat
if st.sidebar.button("Xóa Lịch Sử Trò Chuyện"):
    st.session_state.messages = []
    st.rerun()

st.sidebar.markdown("""
---
### Hướng Dẫn Sử Dụng:
1. Nhập câu hỏi liên quan đến luật phòng chống ma túy (ví dụ: *Hình phạt cho tội tàng trữ ma túy?*).
2. Trợ lý sẽ trả lời dựa trên tài liệu pháp lý đã được nạp.
3. Bạn có thể đặt câu hỏi tiếp theo (ví dụ: *Thế còn tội vận chuyển thì sao?*), chatbot sẽ tự động hiểu ngữ cảnh trước đó.
4. Xem chi tiết các đoạn tài liệu được trích dẫn ở phần **Nguồn Trích Dẫn** ngay bên dưới câu trả lời.
""")

# Hiển thị lịch sử chat
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Nếu là câu trả lời của trợ lý và có nguồn trích dẫn, hiển thị nguồn
        if message["role"] == "assistant" and "sources" in message and message["sources"]:
            with st.expander(f"🔍 Xem nguồn trích dẫn cho câu trả lời này ({len(message['sources'])} chunks)"):
                for s_idx, src in enumerate(message["sources"], 1):
                    meta = src.get("metadata") or {}
                    doc_name = meta.get("doc_name") or meta.get("source") or "Không rõ nguồn"
                    score = src.get("score", 0.0)
                    
                    st.markdown(f"**[{s_idx}] Tài liệu:** `{doc_name}` | **Độ tương đồng (Score):** <span class='score-badge'>{score:.3f}</span>", unsafe_allow_html=True)
                    st.text_area(label=f"Nội dung đoạn trích [{s_idx}]", value=src.get("content", ""), height=100, disabled=True, key=f"src_{idx}_{s_idx}")

# Nhập câu hỏi mới từ người dùng
if prompt := st.chat_input("Nhập câu hỏi của bạn tại đây..."):
    # 1. Hiển thị câu hỏi của user
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Thêm vào session history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 2. Xử lý câu trả lời từ RAG Chatbot
    with st.chat_message("assistant"):
        with st.spinner("Đang truy vấn tài liệu pháp lý và suy luận câu trả lời..."):
            # Lấy lịch sử dạng chat context (chỉ lấy role và content)
            chat_history = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages[:-1] # không lấy câu hỏi vừa nhập
            ]
            
            # Gọi chatbot backend
            response = bot.chat(
                query=prompt,
                history=chat_history,
                top_k=top_k,
                score_threshold=score_threshold,
                use_reranking=use_reranking
            )
            
            # Hiển thị câu trả lời
            st.markdown(response["answer"])
            
            # Hiển thị nguồn trích dẫn
            if response["sources"]:
                with st.expander(f"🔍 Xem nguồn trích dẫn cho câu trả lời này ({len(response['sources'])} chunks)"):
                    for s_idx, src in enumerate(response["sources"], 1):
                        meta = src.get("metadata") or {}
                        doc_name = meta.get("doc_name") or meta.get("source") or "Không rõ nguồn"
                        score = src.get("score", 0.0)
                        st.markdown(f"**[{s_idx}] Tài liệu:** `{doc_name}` | **Độ tương đồng (Score):** <span class='score-badge'>{score:.3f}</span>", unsafe_allow_html=True)
                        st.text_area(label=f"Nội dung đoạn trích [{s_idx}]", value=src.get("content", ""), height=100, disabled=True, key=f"src_new_{s_idx}")
            else:
                st.info("Không tìm thấy tài liệu phù hợp làm căn cứ trích dẫn.")
                
            # Thêm câu trả lời vào session history
            st.session_state.messages.append({
                "role": "assistant",
                "content": response["answer"],
                "sources": response["sources"]
            })
