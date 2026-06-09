"""
Task 5 — Semantic Search Module.

Viết module tìm kiếm ngữ nghĩa (dense retrieval) trên vector store.

Yêu cầu:
    - Input: query string + top_k
    - Output: danh sách chunks có score, sorted descending
    - Phải tương thích với embedding model và vector store ở Task 4
"""


import os
import weaviate
from weaviate.classes.query import MetadataQuery
from openai import OpenAI
from dotenv import load_dotenv


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng vector similarity.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,      # Nội dung chunk
            'score': float,      # Cosine similarity score
            'metadata': dict     # source, doc_type, chunk_index
        }
        Sorted by score descending.
    """
    load_dotenv()
    client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Bước 1: Embed query bằng cùng model ở Task 4
    response = client_openai.embeddings.create(
        input=[query],
        model="text-embedding-3-small"
    )
    query_embedding = response.data[0].embedding

    # Bước 2: Query vector store (cosine similarity)
    with weaviate.connect_to_local(port=8081, grpc_port=50052) as client:
        collection = client.collections.get("DrugLawDocs")
        
        results = collection.query.near_vector(
            near_vector=query_embedding,
            limit=top_k,
            return_metadata=MetadataQuery(distance=True)
        )

        # Bước 3: Return top_k results
        search_results = []
        for obj in results.objects:
            distance = obj.metadata.distance if obj.metadata.distance is not None else 0.0
            score = 1.0 - distance
            
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
                "score": score,
                "metadata": metadata
            })
        
        # Sắp xếp lại theo score giảm dần
        search_results.sort(key=lambda x: x["score"], reverse=True)
        return search_results



if __name__ == "__main__":
    # Test
    results = semantic_search("hình phạt cho tội tàng trữ ma tuý", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
