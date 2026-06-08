"""
Task 10 — Generation Có Citation dùng Mistral AI.

Hướng dẫn:
    1. Reorder chunks để tránh "lost in the middle" effect
    2. Format context với source labels cho citation
    3. Inject vào prompt với SYSTEM_PROMPT
    4. Gọi Mistral AI API
    5. Return answer có citation + sources

Lựa chọn tham số:
    - top_k=5: Đủ evidence (5 chunks ~ 2500 chars), không quá dài gây lost in the middle
    - top_p=0.9: Nucleus sampling — diverse nhưng không quá random cho factual answers
    - temperature=0.3: RAG cần factual accuracy, ít sáng tạo
    - Model: mistral-small-latest — balance giữa tốc độ và chất lượng
"""

import os
from dotenv import load_dotenv

load_dotenv()

from .task9_retrieval_pipeline import retrieve

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")

# =============================================================================
# CONFIGURATION — Giải thích lựa chọn
# =============================================================================

# top_k: Số chunks đưa vào context
# Chọn 5 vì: đủ evidence mà không quá dài gây lost in the middle (Liu et al. 2023)
TOP_K = 5

# top_p (nucleus sampling): Xác suất tích luỹ cho token generation
# Chọn 0.9: đủ diverse nhưng không quá random với factual content
TOP_P = 0.9

# temperature: Độ ngẫu nhiên của output
# Chọn 0.3: RAG cần factual accuracy, ít hallucination
TEMPERATURE = 0.3

# Model Mistral — dùng mistral-small-latest (fast, cheap, đủ tốt)
MISTRAL_MODEL = "mistral-small-latest"


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """Trả lời câu hỏi một cách đầy đủ bằng tiếng Việt.
Với mỗi thông tin thực tế hoặc khẳng định, hãy chèn ngay citation trong ngoặc vuông
liên kết đến nguồn cụ thể (ví dụ: [Luật Phòng chống ma tuý 2021, Điều 3]
hoặc [VnExpress, 2024]).

Nếu thông tin không được nêu rõ trong context được cung cấp,
hãy trả lời 'Tôi không thể xác minh thông tin này từ nguồn hiện có'
thay vì đoán mò.

Quy tắc:
- CHỈ dùng thông tin từ context được cung cấp
- Mỗi khẳng định thực tế PHẢI có citation
- Nếu context không đủ, hãy nói rõ
- Cấu trúc câu trả lời với các đoạn văn rõ ràng"""


# =============================================================================
# DOCUMENT REORDERING (tránh lost in the middle)
# =============================================================================

def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """
    Sắp xếp chunks để tránh "lost in the middle" effect (Liu et al. 2023).

    LLM nhớ tốt thông tin ở ĐẦU và CUỐI prompt, quên thông tin ở GIỮA.
    Strategy: đặt chunks quan trọng nhất ở đầu và cuối, kém quan trọng ở giữa.

    Input (by score rank): [1st, 2nd, 3rd, 4th, 5th]
    Output:               [1st, 3rd, 5th, 4th, 2nd]
    → Most important first, second most important last, rest in middle

    Args:
        chunks: List sorted by score descending (from retrieval)

    Returns:
        List reordered để maximize LLM attention.
    """
    if len(chunks) <= 2:
        return chunks

    # Split: odd-indexed → first half (head), even-indexed → second half (tail, reversed)
    head = chunks[0::2]   # indices 0, 2, 4, ... (most important first)
    tail = chunks[1::2]   # indices 1, 3, 5, ...

    # head goes to front, tail reversed goes to back
    reordered = head + tail[::-1]
    return reordered


# =============================================================================
# CONTEXT FORMATTING
# =============================================================================

def format_context(chunks: list[dict]) -> str:
    """
    Format chunks thành context string cho prompt.
    Mỗi chunk có label source để LLM có thể cite.

    Args:
        chunks: List of {'content': str, 'metadata': dict, 'score': float}

    Returns:
        Formatted context string với source labels.
    """
    context_parts = []

    for i, chunk in enumerate(chunks, 1):
        metadata = chunk.get("metadata", {})
        source = metadata.get("source", f"Source {i}")
        # Bỏ đuôi .md để citation đẹp hơn
        source_clean = source.replace(".md", "").replace("_", " ").replace("-", " ")
        doc_type = metadata.get("type", "unknown")

        context_parts.append(
            f"[Document {i} | Source: {source_clean} ({source}) | Type: {doc_type}]\n"
            f"{chunk['content']}\n"
        )

    return "\n---\n".join(context_parts)


# =============================================================================
# GENERATION
# =============================================================================

def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """
    End-to-end RAG generation có citation dùng Mistral AI.

    Pipeline:
        1. Retrieve relevant chunks (Task 9)
        2. Reorder để tránh lost in the middle
        3. Format context với source labels
        4. Build prompt (system + context + query)
        5. Call Mistral AI
        6. Return answer + sources

    Args:
        query: Câu hỏi của user

    Returns:
        {
            'answer': str,           # Câu trả lời có citation
            'sources': list[dict],   # Các chunks đã dùng
            'retrieval_source': str  # 'hybrid' hoặc 'pageindex'
        }
    """
    # Step 1: Retrieve
    chunks = retrieve(query, top_k=top_k)

    if not chunks:
        return {
            "answer": "Tôi không thể xác minh thông tin này từ nguồn hiện có.",
            "sources": [],
            "retrieval_source": "none",
        }

    # Step 2: Reorder để tránh lost in the middle
    reordered = reorder_for_llm(chunks)

    # Step 3: Format context
    context = format_context(reordered)

    # Step 4: Build prompt
    user_message = f"Context:\n{context}\n\n---\n\nCâu hỏi: {query}"

    # Step 5: Call Mistral AI
    if not MISTRAL_API_KEY:
        return {
            "answer": (
                "MISTRAL_API_KEY chưa được set. "
                "Hãy thêm MISTRAL_API_KEY vào file .env.\n\n"
                f"Context đã retrieve:\n{context[:500]}..."
            ),
            "sources": chunks,
            "retrieval_source": chunks[0].get("source", "hybrid") if chunks else "none",
        }

    try:
        from mistralai import Mistral

        client = Mistral(api_key=MISTRAL_API_KEY)

        response = client.chat.complete(
            model=MISTRAL_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=TEMPERATURE,
            top_p=TOP_P,
            max_tokens=1024,
        )

        answer = response.choices[0].message.content

    except Exception as e:
        answer = (
            f"Lỗi gọi Mistral API: {e}\n\n"
            "Tôi không thể xác minh thông tin này từ nguồn hiện có."
        )

    # Step 6: Return
    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": chunks[0].get("source", "hybrid") if chunks else "none",
    }


if __name__ == "__main__":
    test_queries = [
        "Hình phạt cho tội tàng trữ trái phép chất ma tuý theo pháp luật Việt Nam?",
        "Những nghệ sĩ nào đã bị bắt vì liên quan tới ma tuý?",
        "Quy trình cai nghiện bắt buộc theo Luật Phòng chống ma tuý 2021?",
    ]

    for q in test_queries:
        print(f"\n{'='*70}")
        print(f"Q: {q}")
        print("=" * 70)
        result = generate_with_citation(q)
        print(f"\nA: {result['answer']}")
        print(f"\n[Sources: {len(result['sources'])} chunks | via {result['retrieval_source']}]")
