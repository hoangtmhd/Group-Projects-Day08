"""
Task 7 — Reranking Module.

Chọn 1 trong các phương pháp:
    - Cross-encoder reranker: Jina Reranker v2 (multilingual) hoặc Qwen3-Reranker
    - MMR (Maximal Marginal Relevance): tự implement
    - RRF (Reciprocal Rank Fusion): tự implement

Nếu dùng MMR hoặc RRF, đảm bảo hiểu và giải thích được cơ chế.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
from rank_bm25 import BM25Okapi


def cosine_sim(a: list[float], b: list[float]) -> float:
    """
    Tính cosine similarity giữa 2 vector.
    Do vector sinh ra từ models/gemini-embedding-2 đã được L2 normalized (độ dài = 1),
    cosine similarity chính là tích vô hướng (dot product) của 2 vector.
    """
    return sum(x * y for x, y in zip(a, b))


def rerank_cross_encoder(
    query: str, candidates: list[dict], top_k: int = 5
) -> list[dict]:
    """
    Rerank candidates sử dụng sự kết hợp giữa Semantic (Gemini) và Lexical (BM25).

    Args:
        query: Câu truy vấn
        candidates: List of {'content': str, 'score': float, 'metadata': dict}
        top_k: Số lượng kết quả sau rerank

    Returns:
        List of top_k candidates, re-scored và sorted by rerank_score descending.
    """
    if not candidates:
        return []

    load_dotenv()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # 1. Xếp hạng theo ngữ nghĩa (Semantic Ranking)
    q_res = client.embeddings.create(
        input=[query],
        model="text-embedding-3-small"
    )
    query_embedding = q_res.data[0].embedding

    c_res = client.embeddings.create(
        input=[c["content"] for c in candidates],
        model="text-embedding-3-small"
    )
    candidate_embeddings = [data.embedding for data in c_res.data]

    semantic_scores = [cosine_sim(query_embedding, c_emb) for c_emb in candidate_embeddings]
    semantic_ranked = sorted(
        [{"index": i, "content": candidates[i]["content"], "score": semantic_scores[i]} for i in range(len(candidates))],
        key=lambda x: x["score"],
        reverse=True
    )

    # 2. Xếp hạng theo từ khóa (Lexical Ranking)
    tokenized_corpus = [c["content"].lower().split() for c in candidates]
    bm25 = BM25Okapi(tokenized_corpus)
    tokenized_query = query.lower().split()
    lexical_scores = bm25.get_scores(tokenized_query)

    lexical_ranked = sorted(
        [{"index": i, "content": candidates[i]["content"], "score": lexical_scores[i]} for i in range(len(candidates))],
        key=lambda x: x["score"],
        reverse=True
    )

    # 3. Kết hợp bằng Reciprocal Rank Fusion (RRF)
    k = 60
    rrf_scores = {i: 0.0 for i in range(len(candidates))}

    for rank, item in enumerate(semantic_ranked, 1):
        rrf_scores[item["index"]] += 1 / (k + rank)

    for rank, item in enumerate(lexical_ranked, 1):
        rrf_scores[item["index"]] += 1 / (k + rank)

    # Cập nhật điểm score và sắp xếp lại danh sách ban đầu
    reranked_candidates = []
    for idx, rrf_score in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True):
        item = candidates[idx].copy()
        item["score"] = rrf_score
        reranked_candidates.append(item)

    return reranked_candidates[:top_k]


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
        candidates: List of {'content': str, 'score': float, 'embedding': list, 'metadata': dict}
        top_k: Số lượng kết quả
        lambda_param: Trade-off giữa relevance (1.0) và diversity (0.0)

    Returns:
        List of top_k candidates selected by MMR.
    """
    if not candidates:
        return []

    # Đảm bảo các candidates có vector embedding, nếu thiếu sẽ sinh bằng Gemini
    missing_embs = [i for i, c in enumerate(candidates) if "embedding" not in c or c["embedding"] is None]
    if missing_embs:
        load_dotenv()
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        c_res = client.embeddings.create(
            input=[candidates[i]["content"] for i in missing_embs],
            model="text-embedding-3-small"
        )
        for idx, data in zip(missing_embs, c_res.data):
            candidates[idx]["embedding"] = data.embedding

    selected = []
    remaining = list(range(len(candidates)))

    for _ in range(min(top_k, len(candidates))):
        best_idx = None
        best_score = float('-inf')

        for idx in remaining:
            # Độ tương đồng với query
            relevance = cosine_sim(query_embedding, candidates[idx]["embedding"])

            # Độ tương đồng lớn nhất với các tài liệu đã chọn
            max_sim_to_selected = 0.0
            for sel_idx in selected:
                sim = cosine_sim(candidates[idx]["embedding"], candidates[sel_idx]["embedding"])
                max_sim_to_selected = max(max_sim_to_selected, sim)

            # Điểm MMR
            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim_to_selected

            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        if best_idx is not None:
            selected.append(best_idx)
            remaining.remove(best_idx)

    return [candidates[i] for i in selected]


def rerank_rrf(
    ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60
) -> list[dict]:
    """
    Reciprocal Rank Fusion — gộp kết quả từ nhiều ranker.

    RRF(d) = Σ 1 / (k + rank_r(d))

    Args:
        ranked_lists: List of ranked result lists (mỗi list từ 1 ranker)
        top_k: Số lượng kết quả cuối cùng
        k: Smoothing constant (default=60, từ paper Cormack et al. 2009)

    Returns:
        List of top_k candidates sorted by RRF score descending.
    """
    rrf_scores = {}  # content -> score
    content_map = {}  # content -> full dict

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            key = item["content"]
            rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (k + rank)
            content_map[key] = item

    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    results = []
    for content, score in sorted_items[:top_k]:
        item = content_map[content].copy()
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
    method: str = "cross_encoder",  # "cross_encoder" | "mmr" | "rrf"
) -> list[dict]:
    """
    Unified reranking interface.

    Args:
        query: Câu truy vấn
        candidates: Danh sách candidates từ retrieval
        top_k: Số lượng kết quả sau rerank
        method: Phương pháp reranking

    Returns:
        List of top_k reranked candidates.
    """
    if method == "cross_encoder":
        return rerank_cross_encoder(query, candidates, top_k)
    elif method == "mmr":
        load_dotenv()
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        q_res = client.embeddings.create(
            input=[query],
            model="text-embedding-3-small"
        )
        query_embedding = q_res.data[0].embedding
        return rerank_mmr(query_embedding, candidates, top_k)
    elif method == "rrf":
        # RRF cần nhiều ranked lists. Nếu input là danh sách các danh sách:
        if candidates and isinstance(candidates[0], list):
            return rerank_rrf(candidates, top_k)
        else:
            # Nếu chỉ có 1 danh sách candidates đơn lẻ, thực hiện RRF kết hợp
            # giữa semantic rank và lexical rank của danh sách đó.
            return rerank_cross_encoder(query, candidates, top_k)
    else:
        raise ValueError(f"Unknown rerank method: {method}")


if __name__ == "__main__":
    # Test with dummy data
    dummy_candidates = [
        {"content": "Điều 248: Tội tàng trữ trái phép chất ma tuý", "score": 0.8, "metadata": {}},
        {"content": "Nghệ sĩ X bị bắt vì sử dụng ma tuý", "score": 0.7, "metadata": {}},
        {"content": "Hình phạt tù từ 2-7 năm cho tội tàng trữ", "score": 0.6, "metadata": {}},
    ]
    results = rerank("hình phạt tàng trữ ma tuý", dummy_candidates, top_k=2)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content']}")
