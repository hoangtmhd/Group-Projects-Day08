"""
Task 5 — Semantic Search Module.

Viết module tìm kiếm ngữ nghĩa (dense retrieval) trên ChromaDB.

Yêu cầu:
    - Input: query string + top_k
    - Output: danh sách chunks có score, sorted descending
    - Tương thích với BAAI/bge-m3 và ChromaDB từ Task 4
"""

from .task4_chunking_indexing import (
    EMBEDDING_MODEL,
    get_chroma_collection,
    get_embedding_model,
)

# Cache model để không load lại mỗi lần search
_model = None


def _get_model():
    """Lazy load embedding model."""
    global _model
    if _model is None:
        _model = get_embedding_model()
    return _model


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng ChromaDB + BAAI/bge-m3.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,      # Nội dung chunk
            'score': float,      # Cosine similarity score [0, 1]
            'metadata': dict     # source, doc_type, chunk_index
        }
        Sorted by score descending.
    """
    # Bước 1: Embed query bằng cùng model với Task 4
    model = _get_model()
    query_embedding = model.encode(query).tolist()

    # Bước 2: Query ChromaDB với cosine distance
    collection = get_chroma_collection(reset=False)

    if collection.count() == 0:
        print("  ⚠ ChromaDB collection trống. Hãy chạy Task 4 trước!")
        return []

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    # Bước 3: Convert distance → similarity và format output
    # ChromaDB dùng cosine distance [0, 2], similarity = 1 - distance/2
    output = []
    if results["documents"] and results["documents"][0]:
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            # Cosine distance → similarity score [0, 1]
            similarity = max(0.0, 1.0 - dist / 2.0)
            output.append({
                "content": doc,
                "score": similarity,
                "metadata": meta or {},
            })

    # Đảm bảo sorted descending theo score
    output.sort(key=lambda x: x["score"], reverse=True)
    return output[:top_k]


if __name__ == "__main__":
    # Test
    print("Testing semantic search...")
    results = semantic_search("hình phạt cho tội tàng trữ ma tuý", top_k=5)
    if results:
        for r in results:
            print(f"[{r['score']:.3f}] [{r['metadata'].get('type', '?')}] {r['content'][:80]}...")
    else:
        print("Không có kết quả. Hãy chạy Task 4 trước để index dữ liệu.")
