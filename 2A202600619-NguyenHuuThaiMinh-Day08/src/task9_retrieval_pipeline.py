"""
Task 9 — Retrieval Pipeline Hoàn Chỉnh.

Kết hợp semantic search + lexical search + reranking + PageIndex fallback
thành một pipeline thống nhất.

Logic:
    1. Chạy semantic_search + lexical_search song song
    2. Merge kết quả bằng RRF (Reciprocal Rank Fusion)
    3. Rerank bằng RRF (second pass)
    4. Nếu top result score < threshold → fallback sang PageIndex
    5. Return top_k results
"""

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank, rerank_rrf
from .task8_pageindex_vectorless import pageindex_search


# =============================================================================
# CONFIGURATION
# =============================================================================

SCORE_THRESHOLD = 0.3   # Nếu best score < threshold → fallback PageIndex
DEFAULT_TOP_K = 5
RERANK_METHOD = "rrf"   # Dùng RRF (không cần API key)


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """
    Retrieval pipeline hoàn chỉnh với fallback logic.

    Pipeline:
        Query
          ├→ Semantic Search (dense) → dense_results
          ├→ Lexical Search (BM25)   → sparse_results
          │
          ├→ RRF Merge → merged_results
          ├→ Rerank (RRF second pass) → final_results
          │
          └→ If best_score < threshold:
                └→ PageIndex Vectorless → fallback_results

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả cuối cùng
        score_threshold: Ngưỡng điểm tối thiểu cho hybrid results
        use_reranking: Có áp dụng reranking hay không

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': str  # 'hybrid' hoặc 'pageindex'
        }
    """
    # Step 1: Song song chạy semantic + lexical (retrieval rộng hơn để merge)
    candidate_k = top_k * 3  # Lấy nhiều hơn để có pool merge tốt hơn

    try:
        dense_results = semantic_search(query, top_k=candidate_k)
    except Exception as e:
        print(f"  ⚠ Semantic search error: {e}")
        dense_results = []

    try:
        sparse_results = lexical_search(query, top_k=candidate_k)
    except Exception as e:
        print(f"  ⚠ Lexical search error: {e}")
        sparse_results = []

    # Step 2: Merge bằng RRF
    merged = []
    if dense_results or sparse_results:
        all_lists = [lst for lst in [dense_results, sparse_results] if lst]
        merged = rerank_rrf(all_lists, top_k=top_k * 2, k=60)
        for item in merged:
            item["source"] = "hybrid"

    # Step 3: Rerank (second RRF pass để sort ổn định)
    if use_reranking and merged:
        final_results = rerank(query, merged, top_k=top_k, method=RERANK_METHOD)
    else:
        final_results = merged[:top_k]

    # Ensure source field
    for item in final_results:
        if "source" not in item:
            item["source"] = "hybrid"

    # Step 4: Check threshold → fallback PageIndex
    if not final_results or (final_results[0]["score"] < score_threshold):
        top_score = final_results[0]["score"] if final_results else 0.0
        print(
            f"  ⚠ Hybrid score ({top_score:.3f}) < threshold ({score_threshold}). "
            f"Fallback → PageIndex"
        )
        try:
            fallback = pageindex_search(query, top_k=top_k)
            if fallback:
                return fallback
        except Exception as e:
            print(f"  ⚠ PageIndex fallback error: {e}")

    return final_results[:top_k]


if __name__ == "__main__":
    test_queries = [
        "Hình phạt cho tội tàng trữ trái phép chất ma tuý",
        "Nghệ sĩ nào bị bắt vì sử dụng ma tuý năm 2024",
        "Luật phòng chống ma tuý 2021 quy định gì về cai nghiện",
    ]

    for q in test_queries:
        print(f"\nQuery: {q}")
        print("-" * 60)
        results = retrieve(q, top_k=3)
        for i, r in enumerate(results, 1):
            print(f"  {i}. [{r['score']:.4f}] [{r['source']}] {r['content'][:80]}...")
