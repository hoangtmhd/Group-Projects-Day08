"""
Task 8 — PageIndex Vectorless RAG.

PageIndex là vectorless RAG — hiểu cấu trúc document (headings, tables, sections)
thay vì dùng embedding. Phù hợp cho tài liệu pháp luật có cấu trúc rõ ràng.

Đăng ký tại: https://pageindex.ai/
SDK: https://github.com/VectifyAI/PageIndex

Cài đặt:
    pip install pageindex
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


def upload_documents():
    """
    Upload toàn bộ markdown documents lên PageIndex.

    Chú ý: Chỉ cần upload 1 lần. Sau đó có thể query nhiều lần.
    """
    if not PAGEINDEX_API_KEY:
        raise ValueError("PAGEINDEX_API_KEY chưa được set trong .env")

    try:
        from pageindex import PageIndex

        pi = PageIndex(api_key=PAGEINDEX_API_KEY)

        md_files = list(STANDARDIZED_DIR.rglob("*.md"))
        if not md_files:
            print("  ⚠ Không có file markdown. Hãy chạy Task 3 trước.")
            return

        print(f"  Uploading {len(md_files)} files...")
        for md_file in md_files:
            content = md_file.read_text(encoding="utf-8")
            doc_type = "legal" if "legal" in str(md_file) else "news"

            pi.upload(
                content=content,
                metadata={
                    "filename": md_file.name,
                    "type": doc_type,
                    "source": md_file.name,
                }
            )
            print(f"  ✓ Uploaded: {md_file.name}")

    except ImportError:
        print("  ⚠ PageIndex chưa cài. Chạy: pip install pageindex")
    except Exception as e:
        print(f"  ✗ Lỗi upload: {e}")


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval sử dụng PageIndex.
    Dùng làm fallback khi hybrid search không có kết quả tốt.

    PageIndex hiểu cấu trúc document (Điều X, Khoản Y, Mục Z)
    nên đặc biệt hiệu quả với tài liệu pháp luật có nhiều heading.

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
        print("  ⚠ PAGEINDEX_API_KEY chưa set. Trả về fallback results.")
        return _fallback_search(query, top_k)

    try:
        from pageindex import PageIndex

        pi = PageIndex(api_key=PAGEINDEX_API_KEY)
        results = pi.query(query=query, top_k=top_k)

        return [
            {
                "content": r.text if hasattr(r, "text") else str(r),
                "score": float(r.score) if hasattr(r, "score") else 0.5,
                "metadata": r.metadata if hasattr(r, "metadata") else {},
                "source": "pageindex",
            }
            for r in results
        ]

    except ImportError:
        print("  ⚠ PageIndex chưa cài. Dùng fallback.")
        return _fallback_search(query, top_k)
    except Exception as e:
        print(f"  ⚠ PageIndex error: {e}. Dùng fallback.")
        return _fallback_search(query, top_k)


def _fallback_search(query: str, top_k: int) -> list[dict]:
    """
    Fallback khi không có PageIndex API key: dùng simple keyword search
    trực tiếp trên markdown files trong data/standardized/.
    """
    results = []
    query_terms = query.lower().split()

    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            content_lower = content.lower()

            # Tính điểm đơn giản: đếm số keyword matches
            match_count = sum(1 for term in query_terms if term in content_lower)
            if match_count == 0:
                continue

            # Tìm đoạn text có chứa nhiều keyword nhất
            lines = content.split("\n")
            best_snippet = ""
            best_line_score = 0
            for i, line in enumerate(lines):
                line_lower = line.lower()
                line_score = sum(1 for term in query_terms if term in line_lower)
                if line_score > best_line_score and len(line.strip()) > 30:
                    best_line_score = line_score
                    # Lấy snippet xung quanh dòng đó
                    start = max(0, i - 1)
                    end = min(len(lines), i + 3)
                    best_snippet = "\n".join(lines[start:end])

            if not best_snippet:
                best_snippet = content[:500]

            doc_type = "legal" if "legal" in str(md_file) else "news"
            score = match_count / (len(query_terms) + 1)  # Normalize

            results.append({
                "content": best_snippet.strip(),
                "score": score,
                "metadata": {"source": md_file.name, "type": doc_type},
                "source": "pageindex",  # Đánh dấu là pageindex (fallback)
            })
        except Exception:
            continue

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    if not PAGEINDEX_API_KEY:
        print("⚠ PAGEINDEX_API_KEY chưa set trong .env")
        print("  Đăng ký tại: https://pageindex.ai/")
        print("\nTest fallback search:")
        results = pageindex_search("hình phạt sử dụng ma tuý", top_k=3)
    else:
        print("Uploading documents...")
        upload_documents()
        print("\nTest query:")
        results = pageindex_search("hình phạt sử dụng ma tuý", top_k=3)

    for r in results:
        print(f"[{r['score']:.3f}] [{r['source']}] {r['content'][:100]}...")
