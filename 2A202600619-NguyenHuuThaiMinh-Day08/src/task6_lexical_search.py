"""
Task 6 — Lexical Search Module (BM25).

Sử dụng BM25Okapi từ rank-bm25. Corpus được load từ ChromaDB
(để đồng nhất với Task 5, không cần đọc file lại).

BM25 hoạt động thế nào:
    - Term Frequency (TF): từ xuất hiện nhiều trong document → điểm cao hơn
    - Inverse Document Frequency (IDF): từ hiếm trong toàn corpus → quan trọng hơn
    - Document length normalization: document dài không bị ưu tiên quá mức
    - Formula: score(q,d) = Σ IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl))
    - k1=1.5 (term saturation — điểm tăng chậm khi TF tăng)
    - b=0.75 (length normalization strength)

→ BM25 vượt trội TF-IDF vì có length normalization và term saturation.

Cài đặt:
    pip install rank-bm25
"""

import numpy as np
from pathlib import Path
try:
    from rank_bm25 import BM25Okapi
except ImportError:
    import math

    class BM25Okapi:
        def __init__(self, corpus, k1=1.5, b=0.75):
            self.k1 = k1
            self.b = b
            self.corpus_size = len(corpus)
            self.doc_lengths = [len(doc) for doc in corpus]
            self.avgdl = sum(self.doc_lengths) / self.corpus_size if self.corpus_size > 0 else 0
            self.doc_freqs = []
            self.nd = {}  # Number of documents containing term
            
            for doc in corpus:
                frequencies = {}
                for term in doc:
                    frequencies[term] = frequencies.get(term, 0) + 1
                self.doc_freqs.append(frequencies)
                for term in frequencies:
                    self.nd[term] = self.nd.get(term, 0) + 1
            
            self.idf = {}
            for term, freq in self.nd.items():
                self.idf[term] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1)

        def get_scores(self, query):
            scores = [0.0] * self.corpus_size
            for term in query:
                if term not in self.idf:
                    continue
                idf = self.idf[term]
                for i in range(self.corpus_size):
                    freq = self.doc_freqs[i].get(term, 0)
                    numerator = freq * (self.k1 + 1)
                    denominator = freq + self.k1 * (1 - self.b + self.b * self.doc_lengths[i] / self.avgdl)
                    scores[i] += idf * numerator / denominator
            return scores

from .task4_chunking_indexing import get_chroma_collection

# Cache BM25 index và corpus
_bm25 = None
_corpus: list[dict] = []


def _load_corpus_from_chroma() -> list[dict]:
    """Load tất cả chunks từ ChromaDB để build BM25 index."""
    collection = get_chroma_collection(reset=False)
    count = collection.count()

    if count == 0:
        return []

    # ChromaDB get all — lấy theo batch nếu nhiều
    result = collection.get(
        include=["documents", "metadatas"],
        limit=count,
    )

    corpus = []
    for doc, meta in zip(result["documents"], result["metadatas"]):
        corpus.append({
            "content": doc,
            "metadata": meta or {},
        })
    return corpus


def _build_bm25_index(corpus: list[dict]) -> BM25Okapi:
    """
    Xây dựng BM25 index từ corpus.

    Tokenization: lowercase + split() — đơn giản nhưng hiệu quả cho tiếng Việt
    (tiếng Việt đã phân tách âm tiết bằng dấu cách)
    """
    tokenized_corpus = [doc["content"].lower().split() for doc in corpus]
    return BM25Okapi(tokenized_corpus)


def _ensure_index():
    """Lazy load: build BM25 index lần đầu tiên khi cần."""
    global _bm25, _corpus
    if _bm25 is None or not _corpus:
        _corpus = _load_corpus_from_chroma()
        if _corpus:
            _bm25 = _build_bm25_index(_corpus)


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25Okapi.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,      # BM25 score (unnormalized)
            'metadata': dict
        }
        Sorted by score descending.
    """
    _ensure_index()

    if not _corpus or _bm25 is None:
        print("  ⚠ BM25 corpus trống. Hãy chạy Task 4 trước!")
        return []

    # Tokenize query tương tự corpus
    tokenized_query = query.lower().split()
    scores = _bm25.get_scores(tokenized_query)

    # Lấy top_k indices theo score
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        score = float(scores[idx])
        if score > 0:  # Chỉ lấy kết quả có score > 0
            results.append({
                "content": _corpus[idx]["content"],
                "score": score,
                "metadata": _corpus[idx]["metadata"],
            })

    # Đảm bảo sorted descending
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def rebuild_index():
    """Force rebuild BM25 index (dùng sau khi re-index ChromaDB)."""
    global _bm25, _corpus
    _bm25 = None
    _corpus = []
    _ensure_index()
    print(f"  ✓ BM25 index rebuilt với {len(_corpus)} documents")


if __name__ == "__main__":
    # Test
    print("Testing BM25 lexical search...")
    results = lexical_search("Điều 248 tàng trữ trái phép chất ma tuý", top_k=5)
    if results:
        for r in results:
            print(f"[{r['score']:.3f}] [{r['metadata'].get('type', '?')}] {r['content'][:80]}...")
    else:
        print("Không có kết quả. Hãy chạy Task 4 trước.")
