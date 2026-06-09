"""
Task 7 — Reranking Module.

Sử dụng RRF (Reciprocal Rank Fusion) làm phương pháp chính.

RRF được chọn vì:
    - Không cần API key hay model download thêm
    - Hiệu quả tương đương cross-encoder trong nhiều benchmark
    - Dễ giải thích: RRF(d) = Σ 1 / (k + rank_r(d))
    - k=60 từ paper Cormack et al. 2009 — giảm ảnh hưởng của outlier ranks

Ngoài RRF, module còn cung cấp:
    - rerank_cross_encoder: dùng Jina Reranker API (cần JINA_API_KEY)
    - rerank_mmr: Maximal Marginal Relevance để tăng diversity
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

JINA_API_KEY = os.getenv("JINA_API_KEY", "")


def rerank_cross_encoder(
    query: str, candidates: list[dict], top_k: int = 5
) -> list[dict]:
    """
    Rerank candidates sử dụng Jina Reranker v2 API (multilingual).

    Args:
        query: Câu truy vấn
        candidates: List of {'content': str, 'score': float, 'metadata': dict}
        top_k: Số lượng kết quả sau rerank

    Returns:
        List of top_k candidates, re-scored và sorted by rerank_score descending.
    """
    if not JINA_API_KEY:
        raise ValueError("JINA_API_KEY chưa được set. Dùng rerank_rrf() thay thế.")

    import requests

    response = requests.post(
        "https://api.jina.ai/v1/rerank",
        headers={"Authorization": f"Bearer {JINA_API_KEY}"},
        json={
            "model": "jina-reranker-v2-base-multilingual",
            "query": query,
            "documents": [c["content"] for c in candidates],
            "top_n": top_k,
        },
        timeout=30,
    )
    response.raise_for_status()
    reranked = response.json()["results"]

    return [
        {**candidates[r["index"]], "score": r["relevance_score"]}
        for r in reranked
    ]


def rerank_mmr(
    query_embedding: list[float],
    candidates: list[dict],
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    """
    Maximal Marginal Relevance — chọn candidates vừa relevant vừa diverse.

    MMR = λ * sim(query, doc) - (1-λ) * max(sim(doc, selected_docs))

    Args:
        query_embedding: Vector embedding của query
        candidates: List of {'content', 'score', 'embedding', 'metadata'}
        top_k: Số lượng kết quả
        lambda_param: Trade-off relevance (1.0) vs diversity (0.0)

    Returns:
        List of top_k candidates selected by MMR.
    """
    import numpy as np

    def cosine_sim(a, b):
        a, b = np.array(a), np.array(b)
        norm_a, norm_b = np.linalg.norm(a), np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    selected_indices = []
    remaining = list(range(len(candidates)))

    for _ in range(min(top_k, len(candidates))):
        best_idx = None
        best_score = float("-inf")

        for idx in remaining:
            if "embedding" not in candidates[idx]:
                # Fallback nếu không có embedding
                mmr_score = candidates[idx].get("score", 0)
            else:
                relevance = cosine_sim(query_embedding, candidates[idx]["embedding"])
                max_sim_to_selected = 0.0
                for sel_idx in selected_indices:
                    if "embedding" in candidates[sel_idx]:
                        sim = cosine_sim(
                            candidates[idx]["embedding"],
                            candidates[sel_idx]["embedding"]
                        )
                        max_sim_to_selected = max(max_sim_to_selected, sim)
                mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim_to_selected

            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        if best_idx is not None:
            selected_indices.append(best_idx)
            remaining.remove(best_idx)

    result = []
    for rank, idx in enumerate(selected_indices):
        item = candidates[idx].copy()
        item["score"] = candidates[idx].get("score", 0)
        result.append(item)

    return result


def rerank_rrf(
    ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60
) -> list[dict]:
    """
    Reciprocal Rank Fusion — gộp kết quả từ nhiều ranker.

    RRF(d) = Σ 1 / (k + rank_r(d))

    Ưu điểm:
        - Không cần score calibration giữa các ranker
        - k=60 từ paper Cormack et al. 2009 giúp giảm ảnh hưởng của top ranks
        - Robust với các ranker có scale điểm khác nhau

    Args:
        ranked_lists: List of ranked result lists (mỗi list từ 1 ranker)
        top_k: Số lượng kết quả cuối cùng
        k: Smoothing constant (default=60)

    Returns:
        List of top_k candidates sorted by RRF score descending.
    """
    rrf_scores: dict[str, float] = {}
    content_map: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            key = item["content"][:200]  # Dùng 200 chars đầu làm key (tránh key quá dài)
            rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (k + rank)
            content_map[key] = item

    # Sort by RRF score descending
    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    results = []
    for content_key, score in sorted_items[:top_k]:
        item = content_map[content_key].copy()
        item["score"] = score
        results.append(item)

    return results


# =============================================================================
# Main rerank interface
# =============================================================================

def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
    method: str = "rrf",  # Đổi default sang "rrf" (không cần API key)
) -> list[dict]:
    """
    Unified reranking interface.

    Args:
        query: Câu truy vấn
        candidates: Danh sách candidates từ retrieval
        top_k: Số lượng kết quả sau rerank
        method: "rrf" | "cross_encoder" | "mmr"

    Returns:
        List of top_k reranked candidates.
    """
    if not candidates:
        return []

    if method == "rrf":
        # Với 1 list → dùng RRF để re-score theo rank position
        return rerank_rrf([candidates], top_k=top_k, k=60)
    elif method == "cross_encoder":
        return rerank_cross_encoder(query, candidates, top_k)
    elif method == "mmr":
        raise NotImplementedError(
            "MMR cần query_embedding. Dùng rerank_mmr() trực tiếp với embedding."
        )
    else:
        raise ValueError(f"Unknown rerank method: {method}")


if __name__ == "__main__":
    # Test với dummy data
    dummy_candidates = [
        {"content": "Điều 248: Tội tàng trữ trái phép chất ma tuý", "score": 0.8, "metadata": {}},
        {"content": "Nghệ sĩ X bị bắt vì sử dụng ma tuý", "score": 0.7, "metadata": {}},
        {"content": "Hình phạt tù từ 2-7 năm cho tội tàng trữ", "score": 0.6, "metadata": {}},
        {"content": "Python programming language overview", "score": 0.1, "metadata": {}},
    ]
    print("Testing RRF reranking...")
    results = rerank("hình phạt tàng trữ ma tuý", dummy_candidates, top_k=3, method="rrf")
    for r in results:
        print(f"[{r['score']:.4f}] {r['content']}")
