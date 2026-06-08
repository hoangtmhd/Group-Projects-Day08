"""
Task 8 — PageIndex Vectorless RAG.

Đăng ký tài khoản tại: https://pageindex.ai/
SDK & sample code: https://github.com/VectifyAI/PageIndex

PageIndex cho phép RAG mà không cần vector store — sử dụng
structural understanding của document thay vì embedding.

Cài đặt:
    pip install pageindex

Hướng dẫn:
    1. Đăng ký account tại pageindex.ai
    2. Lấy API key
    3. Upload documents
    4. Query sử dụng PageIndex API
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


def upload_documents():
    """
    Upload toàn bộ PDF documents từ thư mục landing/legal lên PageIndex.
    Vì PageIndex chỉ hỗ trợ định dạng PDF, chúng ta upload các file PDF pháp lý gốc.
    """
    if not PAGEINDEX_API_KEY:
        print("  ⚠ PAGEINDEX_API_KEY trống. Bỏ qua upload.")
        return

    from pageindex import PageIndexClient
    client = PageIndexClient(api_key=PAGEINDEX_API_KEY)

    # Lấy danh sách document đã có trên PageIndex
    try:
        existing_docs_res = client.list_documents()
        existing_names = {doc["name"] for doc in existing_docs_res.get("documents", [])}
    except Exception as e:
        print(f"  ⚠ Không thể lấy danh sách document từ PageIndex: {e}")
        existing_names = set()

    # Thư mục chứa PDF gốc
    legal_dir = Path(__file__).parent.parent / "data" / "landing" / "legal"
    if not legal_dir.exists():
        print(f"  ⚠ Thư mục {legal_dir} không tồn tại.")
        return

    # Quét các file PDF
    for pdf_file in legal_dir.glob("*.pdf"):
        if pdf_file.name in existing_names:
            print(f"  ✓ Đã tồn tại trên PageIndex: {pdf_file.name}")
            continue

        print(f"  → Đang upload: {pdf_file.name}...")
        try:
            res = client.submit_document(file_path=str(pdf_file))
            print(f"  ✓ Upload thành công: {pdf_file.name} (ID: {res.get('doc_id')})")
        except Exception as e:
            print(f"  ⚠ Lỗi khi upload {pdf_file.name}: {e}")


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval sử dụng PageIndex.
    Dùng làm fallback khi hybrid search không có kết quả tốt.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': 'pageindex'   # Đánh dấu nguồn retrieval
        }
    """
    if not PAGEINDEX_API_KEY:
        print("  ⚠ PAGEINDEX_API_KEY trống. Bỏ qua tìm kiếm PageIndex.")
        return []

    from pageindex import PageIndexClient
    import time
    client = PageIndexClient(api_key=PAGEINDEX_API_KEY)

    # 1. Lấy danh sách tài liệu hiện có
    try:
        docs_res = client.list_documents()
        docs = docs_res.get("documents", [])
    except Exception as e:
        print(f"  ⚠ Lỗi kết nối PageIndex: {e}")
        return []

    # Lọc ra các tài liệu đã hoàn thành (status == 'completed')
    completed_docs = [d for d in docs if d.get("status") == "completed"]
    if not completed_docs:
        print("  ⚠ Không có tài liệu nào ở trạng thái completed trên PageIndex để query.")
        return []

    all_results = []

    # 2. Thực hiện query trên từng tài liệu đã completed
    for doc in completed_docs:
        doc_id = doc["id"]
        doc_name = doc["name"]
        print(f"  → Đang gửi query lên PageIndex cho tài liệu: {doc_name} (ID: {doc_id})...")

        try:
            # Gửi query
            res = client.submit_query(doc_id=doc_id, query=query)
            retrieval_id = res.get("retrieval_id")
            if not retrieval_id:
                print(f"  ⚠ Không nhận được retrieval_id cho {doc_name}")
                continue

            # Poll cho tới khi kết quả sẵn sàng (tối đa 20s)
            start_time = time.time()
            nodes = []
            while time.time() - start_time < 20:
                ret_res = client.get_retrieval(retrieval_id)
                status = ret_res.get("status")
                if status == "completed":
                    # Hỗ trợ cả kết quả cũ (results) và kết quả mới (retrieved_nodes)
                    nodes = ret_res.get("results") or ret_res.get("retrieved_nodes") or []
                    break
                elif status == "failed":
                    print(f"  ⚠ Query thất bại cho {doc_name}")
                    break
                time.sleep(1.5)
            
            # Format kết quả
            for node in nodes:
                content = node.get("text") or node.get("content") or ""
                score = node.get("score") or 0.0
                metadata = node.get("metadata") or {}
                # Ghi nhận thông tin nguồn
                metadata["doc_name"] = doc_name
                metadata["doc_id"] = doc_id
                
                all_results.append({
                    "content": content,
                    "score": score,
                    "metadata": metadata,
                    "source": "pageindex"
                })
        except Exception as e:
            print(f"  ⚠ Lỗi trong quá trình query tài liệu {doc_name}: {e}")

    # 3. Sắp xếp tất cả các node từ các tài liệu theo score giảm dần
    all_results.sort(key=lambda x: x["score"], reverse=True)

    return all_results[:top_k]


if __name__ == "__main__":
    if not PAGEINDEX_API_KEY:
        print("⚠ Hãy set PAGEINDEX_API_KEY trong file .env")
        print("  Đăng ký tại: https://pageindex.ai/")
    else:
        print("Uploading documents...")
        upload_documents()

        print("\nTest query:")
        results = pageindex_search("hình phạt sử dụng ma tuý", top_k=3)
        for r in results:
            print(f"[{r['score']:.3f}] {r['content'][:100]}...")
