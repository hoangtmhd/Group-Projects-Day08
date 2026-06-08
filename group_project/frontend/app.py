import streamlit as st
import os
import sys
from pathlib import Path

# Đảm bảo import được RAGChatbot từ chatbot.py ở thư mục cha
sys.path.insert(0, str(Path(__file__).parent.parent))
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

try:
    bot = load_chatbot()
except Exception as e:
    st.error(f"Lỗi khởi tạo chatbot: {str(e)}")
    st.stop()

# CSS tùy chỉnh để làm giao diện đẹp hơn (Premium UI)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

    /* Main background */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #1e293b 0%, #0f172a 100%);
        color: #f8fafc;
    }
    
    /* Header Styling */
    .main-header {
        text-align: center;
        margin-bottom: 2rem;
        animation: fadeInDown 0.8s ease-out;
    }
    
    .main-title {
        font-weight: 700;
        font-size: 3rem;
        background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .sub-title {
        color: #94a3b8;
        font-size: 1.1rem;
        font-weight: 300;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.7);
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Sidebar Headers */
    .sidebar-header {
        color: #38bdf8;
        font-weight: 600;
        font-size: 1.2rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
        border-bottom: 1px solid rgba(56, 189, 248, 0.3);
        padding-bottom: 0.5rem;
    }

    /* Chat message styling */
    .stChatMessage {
        background-color: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(8px);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        animation: fadeInUp 0.4s ease-out;
    }
    
    .stChatMessage:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px -2px rgba(56, 189, 248, 0.15);
        border: 1px solid rgba(56, 189, 248, 0.2);
    }

    /* User Message specific */
    [data-testid="stChatMessage"]:nth-child(even) {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9));
        border-left: 4px solid #38bdf8;
    }

    /* Assistant Message specific */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.6), rgba(15, 23, 42, 0.7));
        border-left: 4px solid #c084fc;
    }

    /* Chat input area */
    .stChatInputContainer {
        padding-bottom: 2rem !important;
    }

    .stChatInputContainer > div {
        background-color: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid rgba(56, 189, 248, 0.3) !important;
        border-radius: 30px !important;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.1) !important;
        transition: all 0.3s ease;
    }
    
    .stChatInputContainer > div:focus-within {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 30px rgba(56, 189, 248, 0.2) !important;
    }

    /* Expander for sources */
    .streamlit-expanderHeader {
        background-color: rgba(30, 41, 59, 0.8) !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        color: #e2e8f0 !important;
        font-weight: 500 !important;
    }
    
    .streamlit-expanderContent {
        background-color: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-top: none !important;
        border-radius: 0 0 10px 10px !important;
        padding: 1rem !important;
    }

    /* Source Box styling */
    .source-box {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .source-box:hover {
        background: rgba(30, 41, 59, 0.8);
        border-color: rgba(56, 189, 248, 0.4);
    }

    /* Badges & Highlights */
    .score-badge {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
        box-shadow: 0 2px 10px rgba(16, 185, 129, 0.3);
        display: inline-block;
    }

    .source-title {
        color: #e2e8f0;
        font-weight: 600;
        font-size: 1rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #ef4444, #b91c1c) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 15px rgba(239, 68, 68, 0.4) !important;
    }

    /* Animations */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
""", unsafe_allow_html=True)

# Header UI
st.markdown("""
<div class="main-header">
    <div class="main-title">⚖️ Trợ Lý Pháp Luật Ma Túy</div>
    <div class="sub-title">Hệ thống RAG Chatbot thông minh với khả năng tra cứu, trích dẫn nguồn và duy trì ngữ cảnh hội thoại.</div>
</div>
""", unsafe_allow_html=True)

# Sidebar cấu hình tham số RAG
st.sidebar.markdown('<div class="sidebar-header">⚙️ Cấu Hình Hệ Thống</div>', unsafe_allow_html=True)
top_k = st.sidebar.slider("Số lượng tài liệu truy vấn (Top K)", min_value=1, max_value=10, value=5)
score_threshold = st.sidebar.slider("Ngưỡng tương đồng tối thiểu", min_value=0.0, max_value=1.0, value=0.3, step=0.05)
use_reranking = st.sidebar.checkbox("Sử dụng mô hình Reranking", value=True)

st.sidebar.markdown("<br>", unsafe_allow_html=True)

# Lịch sử hội thoại lưu trong session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Nút xóa lịch sử chat
if st.sidebar.button("🗑️ Xóa Lịch Sử Trò Chuyện"):
    st.session_state.messages = []
    st.rerun()

st.sidebar.markdown("""
---
<div class="sidebar-header">📖 Hướng Dẫn Sử Dụng</div>
<div style="color: #cbd5e1; font-size: 0.9rem; line-height: 1.6;">
    <ol style="padding-left: 1.2rem;">
        <li><b>Nhập câu hỏi</b> về pháp luật phòng chống ma túy (VD: <i>Hình phạt cho tội tàng trữ?</i>).</li>
        <li><b>Xem câu trả lời</b> do AI tổng hợp từ các văn bản pháp lý chính thức.</li>
        <li><b>Kiểm chứng nguồn</b> tại phần trích dẫn đính kèm bên dưới mỗi câu trả lời.</li>
        <li><b>Hỏi tiếp nối</b> tự do, hệ thống tự động ghi nhớ ngữ cảnh.</li>
    </ol>
</div>
""", unsafe_allow_html=True)

# Hiển thị lịch sử chat
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Nếu là câu trả lời của trợ lý và có nguồn trích dẫn, hiển thị nguồn
        if message["role"] == "assistant" and "sources" in message and message["sources"]:
            with st.expander(f"🔍 Trích xuất từ {len(message['sources'])} tài liệu nguồn"):
                for s_idx, src in enumerate(message["sources"], 1):
                    meta = src.get("metadata") or {}
                    doc_name = meta.get("doc_name") or meta.get("source") or "Không rõ nguồn"
                    score = src.get("score", 0.0)
                    
                    st.markdown(f"""
                    <div class="source-box">
                        <div class="source-title">📄 {doc_name}</div>
                        <div style="margin-bottom: 10px;"><span class='score-badge'>Độ tương đồng: {score:.3f}</span></div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.text_area(label="Nội dung trích xuất", value=src.get("content", ""), height=120, disabled=True, key=f"src_{idx}_{s_idx}", label_visibility="collapsed")

# Nhập câu hỏi mới từ người dùng
if prompt := st.chat_input("Hãy đặt câu hỏi về luật phòng chống ma túy..."):
    # 1. Hiển thị câu hỏi của user
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Thêm vào session history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 2. Xử lý câu trả lời từ RAG Chatbot
    with st.chat_message("assistant"):
        with st.spinner("Đang phân tích tài liệu và suy luận..."):
            # Lấy lịch sử dạng chat context (chỉ lấy role và content)
            chat_history = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages[:-1] # không lấy câu hỏi vừa nhập
            ]
            
            try:
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
                    with st.expander(f"🔍 Trích xuất từ {len(response['sources'])} tài liệu nguồn"):
                        for s_idx, src in enumerate(response["sources"], 1):
                            meta = src.get("metadata") or {}
                            doc_name = meta.get("doc_name") or meta.get("source") or "Không rõ nguồn"
                            score = src.get("score", 0.0)
                            
                            st.markdown(f"""
                            <div class="source-box">
                                <div class="source-title">📄 {doc_name}</div>
                                <div style="margin-bottom: 10px;"><span class='score-badge'>Độ tương đồng: {score:.3f}</span></div>
                            </div>
                            """, unsafe_allow_html=True)
                            st.text_area(label="Nội dung trích xuất", value=src.get("content", ""), height=120, disabled=True, key=f"src_new_{s_idx}", label_visibility="collapsed")
                else:
                    st.info("Không tìm thấy tài liệu phù hợp làm căn cứ trích dẫn.")
                    
                # Thêm câu trả lời vào session history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response["answer"],
                    "sources": response["sources"]
                })
            except Exception as e:
                st.error(f"Đã xảy ra lỗi trong quá trình xử lý: {str(e)}")
