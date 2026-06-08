"""
Task 6 — Lexical Search Module (BM25).

Mặc định sử dụng BM25. Nếu dùng phương pháp khác (TF-IDF, Elasticsearch,
Weaviate BM25 built-in), hãy giải thích cơ chế trong buổi demo → +5 bonus.

Cài đặt:
    pip install rank-bm25

BM25 hoạt động thế nào:
    - Term Frequency (TF): từ xuất hiện nhiều trong document → điểm cao
    - Inverse Document Frequency (IDF): từ hiếm → quan trọng hơn
    - Document length normalization: document dài không bị ưu tiên quá mức
    - Formula: score(q,d) = Σ IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl))
    - k1=1.5 (term saturation), b=0.75 (length normalization)
"""

import weaviate
from weaviate.classes.query import MetadataQuery

# CORPUS không cần thiết cho phương pháp Weaviate BM25 built-in, 
# nhưng chúng ta khai báo để giữ tương thích.
CORPUS: list[dict] = []  # List of {'content': str, 'metadata': dict}


def build_bm25_index(corpus: list[dict]):
    """
    Xây dựng BM25 index từ corpus.
    Do sử dụng Weaviate BM25 built-in nên index đã được xây dựng sẵn trên CSDL.
    """
    pass


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25 tích hợp sẵn trong Weaviate.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,      # BM25 score
            'metadata': dict
        }
        Sorted by score descending.
    """
    with weaviate.connect_to_local() as client:
        collection = client.collections.get("DrugLawDocs")
        
        # Thực hiện tìm kiếm BM25 trên Weaviate
        results = collection.query.bm25(
            query=query,
            limit=top_k,
            return_metadata=MetadataQuery(score=True)
        )
        
        search_results = []
        for obj in results.objects:
            properties = obj.properties or {}
            metadata = {
                "source": properties.get("source"),
                "doc_type": properties.get("doc_type"),
                "header_1": properties.get("header_1"),
                "header_2": properties.get("header_2"),
                "header_3": properties.get("header_3")
            }
            
            search_results.append({
                "content": properties.get("content", ""),
                "score": obj.metadata.score if obj.metadata.score is not None else 0.0,
                "metadata": metadata
            })
            
        # Sắp xếp kết quả giảm dần theo score
        search_results.sort(key=lambda x: x["score"], reverse=True)
        return search_results



if __name__ == "__main__":
    # Test
    results = lexical_search("Điều 248 tàng trữ trái phép chất ma tuý", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
