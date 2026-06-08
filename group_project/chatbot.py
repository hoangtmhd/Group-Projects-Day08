import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Đảm bảo import được các module từ thư mục dự án cá nhân
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "2A202600700-TranMinhHoang-project"))

from src.task9_retrieval_pipeline import retrieve
from src.task10_generation import reorder_for_llm, format_context, SYSTEM_PROMPT

load_dotenv(dotenv_path=project_root / "2A202600700-TranMinhHoang-project" / ".env")

class RAGChatbot:
    """
    Chatbot RAG có Conversation Memory dành cho bài tập nhóm.
    """
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        
        # Danh sách model Gemini khả dụng theo độ ưu tiên
        self.gemini_models = [
            "models/gemini-2.5-flash",
            "models/gemini-2.0-flash",
            "gemini-1.5-flash",
            "models/gemini-1.5-flash",
            "gemini-pro-latest"
        ]

    def _call_llm(self, system_prompt: str, user_message: str, temperature: float = 0.3, top_p: float = 0.9) -> str:
        """
        Gọi LLM hỗ trợ cả OpenAI và Gemini fallback.
        """
        use_openai = self.openai_key and not self.openai_key.startswith("sk-xxx")
        
        if use_openai:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=self.openai_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=temperature,
                    top_p=top_p,
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"  ⚠ OpenAI call failed in chatbot ({e}), switching to Gemini fallback...")
                use_openai = False
                
        if not use_openai:
            if not self.gemini_key:
                raise ValueError("Cần cấu hình GEMINI_API_KEY hoặc OPENAI_API_KEY hợp lệ trong file .env")
            
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_key)
            
            for model_name in self.gemini_models:
                try:
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        system_instruction=system_prompt
                    )
                    generation_config = genai.types.GenerationConfig(
                        temperature=temperature,
                        top_p=top_p,
                    )
                    response = model.generate_content(
                        user_message,
                        generation_config=generation_config
                    )
                    return response.text
                except Exception as ex:
                    print(f"  ⚠ Model {model_name} failed: {ex}. Trying next...")
            
            raise ValueError("Không có model LLM nào phản hồi thành công.")

    def rephrase_query(self, query: str, history: list[dict]) -> str:
        """
        Dựa vào lịch sử hội thoại, viết lại câu hỏi tiếp nối thành câu hỏi độc lập (standalone query) chứa đầy đủ ngữ cảnh.
        """
        if not history:
            return query

        history_str = ""
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_str += f"{role}: {msg['content']}\n"

        system_instruction = (
            "You are a helpful assistant that rephrases follow-up questions to be standalone questions in Vietnamese. "
            "Do not answer the question, just return the rephrased standalone question."
        )
        
        user_message = f"""Dựa trên lịch sử hội thoại sau và câu hỏi tiếp theo, hãy viết lại câu hỏi tiếp theo thành một câu hỏi độc lập (standalone question) bằng tiếng Việt. Câu hỏi độc lập này phải tự giải nghĩa được mà không cần đọc lại lịch sử hội thoại.

Lịch sử hội thoại:
{history_str}

Câu hỏi tiếp theo: {query}

Standalone Question:"""

        try:
            standalone = self._call_llm(system_instruction, user_message, temperature=0.1)
            print(f"  [Query Rephrased] '{query}' -> '{standalone.strip()}'")
            return standalone.strip()
        except Exception as e:
            print(f"  ⚠ Rephrase query failed: {e}. Using original query.")
            return query

    def chat(self, query: str, history: list[dict], top_k: int = 5, score_threshold: float = 0.3, use_reranking: bool = True) -> dict:
        """
        Giao tiếp với chatbot RAG:
        1. Viết lại câu hỏi nếu có lịch sử hội thoại.
        2. Truy vấn tài liệu liên quan.
        3. Reorder tránh lost-in-the-middle.
        4. Format ngữ cảnh.
        5. Gọi LLM để sinh câu trả lời có citation.
        """
        # Step 1: Rephrase query
        standalone_query = self.rephrase_query(query, history)

        # Step 2: Retrieve chunks
        chunks = retrieve(standalone_query, top_k=top_k, score_threshold=score_threshold, use_reranking=use_reranking)

        # Step 3: Reorder chunks
        reordered = reorder_for_llm(chunks)

        # Step 4: Format context
        context_str = format_context(reordered)

        # Format history string for generation prompt
        history_str = ""
        for msg in history[-5:]:  # Lấy tối đa 5 lượt chat gần nhất để tránh tràn context
            role = "Người dùng" if msg["role"] == "user" else "Trợ lý"
            history_str += f"{role}: {msg['content']}\n"

        # Step 5: Build User Message
        user_message = f"""Lịch sử hội thoại:
{history_str if history_str else "(Trống)"}

Ngữ cảnh tài liệu:
{context_str if context_str else "(Không tìm thấy tài liệu phù hợp)"}

---

Câu hỏi của người dùng: {query}
Câu hỏi Standalone (đã làm rõ ngữ cảnh): {standalone_query}

Hãy trả lời câu hỏi Standalone dựa trên Ngữ cảnh tài liệu và Lịch sử hội thoại ở trên. Chú ý tuân thủ tuyệt đối quy tắc trích dẫn nguồn [Tên tài liệu, Điều/Năm]. Nếu ngữ cảnh tài liệu không có thông tin, hãy trả lời 'Tôi không thể xác minh thông tin này từ nguồn hiện có'.
"""

        # Step 6: Call LLM
        answer = self._call_llm(SYSTEM_PROMPT, user_message)

        # Determine retrieval source
        retrieval_source = "none"
        if chunks:
            retrieval_source = chunks[0].get("source", "hybrid")

        return {
            "answer": answer,
            "sources": chunks,
            "standalone_query": standalone_query,
            "retrieval_source": retrieval_source
        }

if __name__ == "__main__":
    # Test thử chatbot
    bot = RAGChatbot()
    print("Khởi chạy thử nghiệm Chatbot RAG...")
    
    # Lượt 1
    h = []
    q1 = "Hình phạt cho tội tàng trữ trái phép chất ma tuý?"
    print(f"\nQ1: {q1}")
    res1 = bot.chat(q1, h)
    print(f"A1: {res1['answer']}")
    print(f"Sources: {len(res1['sources'])} chunks via {res1['retrieval_source']}")
    
    # Lượt 2 (Follow up)
    h.append({"role": "user", "content": q1})
    h.append({"role": "assistant", "content": res1["answer"]})
    q2 = "Thế còn tội vận chuyển trái phép thì sao?"
    print(f"\nQ2: {q2}")
    res2 = bot.chat(q2, h)
    print(f"A2: {res2['answer']}")
    print(f"Sources: {len(res2['sources'])} chunks via {res2['retrieval_source']}")
