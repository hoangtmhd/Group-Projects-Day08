"""
Task 4 — Chunking & Indexing vào Vector Store.

Hướng dẫn:
    1. Đọc toàn bộ markdown files từ data/standardized/
    2. Chọn 1 chunking strategy (giải thích lý do)
    3. Chọn 1 embedding model (giải thích lý do)
    4. Index vào vector store (Weaviate khuyến cáo)

Chunking options (langchain-text-splitters):
    - RecursiveCharacterTextSplitter: an toàn, phổ biến
    - MarkdownHeaderTextSplitter: tốt cho file có heading
    - SemanticChunker: dùng embedding để tách (nâng cao)

Embedding model options:
    - sentence-transformers/all-MiniLM-L6-v2 (384 dim, nhẹ)
    - BAAI/bge-m3 (1024 dim, multilingual, tốt cho tiếng Việt)
    - OpenAI text-embedding-3-small (1536 dim, API)

Vector store options:
    - Weaviate (khuyến cáo: hỗ trợ hybrid search built-in)
    - ChromaDB (đơn giản, local)
    - FAISS (chỉ dense search)

Cài đặt:
    pip install langchain-text-splitters sentence-transformers weaviate-client
"""

import json
from pathlib import Path
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn của bạn trong comment
# =============================================================================

# CHUNK_SIZE = 500: Chọn 500 ký tự (khoảng 80-100 từ tiếng Việt) làm kích thước tối đa cho mỗi chunk.
# Kích thước này đủ nhỏ để đảm bảo tính tập trung ngữ nghĩa (semantic focus) cao cho tìm kiếm dense/semantic search,
# đồng thời đảm bảo không bị vượt quá giới hạn của các mô hình LLM và tối ưu thời gian xử lý.
CHUNK_SIZE = 500

# CHUNK_OVERLAP = 50: Chọn 50 ký tự (khoảng 8-10 từ tiếng Việt) làm overlap giữa các chunk liền kề.
# Overlap giúp giữ được tính liên tục của ngữ cảnh, tránh việc các câu bị ngắt đôi giữa các chunk và mất thông tin.
CHUNK_OVERLAP = 50

# CHUNKING_METHOD = "hybrid": Kết hợp chia theo cấu trúc Markdown Header trước (giúp giữ ngữ cảnh phân cấp),
# sau đó nếu chunk nào vượt quá CHUNK_SIZE thì chia tiếp bằng RecursiveCharacterTextSplitter.
CHUNKING_METHOD = "hybrid"

# EMBEDDING_MODEL = "text-embedding-3-small": Sử dụng mô hình embedding của OpenAI.
EMBEDDING_MODEL = "text-embedding-3-small"

# models/text-embedding-3-small sinh vector embedding có số chiều là 1536.
EMBEDDING_DIM = 1536

# VECTOR_STORE = "weaviate": Sử dụng Weaviate chạy local qua Docker để hỗ trợ tìm kiếm kết hợp Hybrid Search (dense + sparse)
# nguyên bản (built-in) chất lượng cao.
VECTOR_STORE = "weaviate"


# =============================================================================
# IMPLEMENTATION
# =============================================================================

def load_documents() -> list[dict]:
    """
    Đọc toàn bộ markdown files từ data/standardized/.

    Returns:
        List of {'content': str, 'metadata': {'source': str, 'type': str}}
    """
    documents = []
    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        doc_type = "legal" if "legal" in str(md_file) else "news"
        documents.append({
            "content": content,
            "metadata": {"source": md_file.name, "type": doc_type}
        })
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk documents theo strategy đã chọn.

    Returns:
        List of {'content': str, 'metadata': dict} — mỗi item là 1 chunk
    """
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    recursive_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    chunks = []
    for doc in documents:
        # Bắt đầu phân đoạn theo Markdown Header trước
        md_docs = markdown_splitter.split_text(doc["content"])
        for md_doc in md_docs:
            combined_metadata = {**doc["metadata"], **md_doc.metadata}
            text = md_doc.page_content
            
            # Nếu phân đoạn nhỏ hơn CHUNK_SIZE, giữ nguyên
            if len(text) <= CHUNK_SIZE:
                chunks.append({
                    "content": text,
                    "metadata": combined_metadata
                })
            else:
                # Nếu phân đoạn quá dài, chia tiếp bằng RecursiveCharacterTextSplitter
                splits = recursive_splitter.split_text(text)
                for i, chunk_text in enumerate(splits):
                    chunks.append({
                        "content": chunk_text,
                        "metadata": {**combined_metadata, "chunk_index": i}
                    })
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Embed toàn bộ chunks bằng model đã chọn.

    Returns:
        Mỗi chunk dict được thêm key 'embedding': list[float]
    """
    import os
    from openai import OpenAI
    from dotenv import load_dotenv

    load_dotenv()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    texts = [c["content"] for c in chunks]
    
    # Chia nhỏ thành các batch để an toàn
    batch_size = 500
    embeddings = []
    
    print(f"Starting OpenAI embeddings generation for {len(texts)} chunks...")
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        print(f"  Embedding batch {i // batch_size + 1} / {(len(texts) - 1) // batch_size + 1}...")
        
        response = client.embeddings.create(
            input=batch_texts,
            model=EMBEDDING_MODEL
        )
        for data in response.data:
            embeddings.append(data.embedding)

    for chunk, emb in zip(chunks, embeddings):
        chunk["embedding"] = emb
    return chunks


def index_to_vectorstore(chunks: list[dict]):
    """
    Lưu chunks vào vector store đã chọn.
    """
    with weaviate.connect_to_local(port=8081, grpc_port=50052) as client:
        # Nếu collection đã tồn tại, xóa đi để tạo mới
        if client.collections.exists("DrugLawDocs"):
            client.collections.delete("DrugLawDocs")
        
        collection = client.collections.create(
            name="DrugLawDocs",
            vectorizer_config=Configure.Vectorizer.none(),
            properties=[
                Property(name="content", data_type=DataType.TEXT),
                Property(name="source", data_type=DataType.TEXT),
                Property(name="doc_type", data_type=DataType.TEXT),
                Property(name="header_1", data_type=DataType.TEXT),
                Property(name="header_2", data_type=DataType.TEXT),
                Property(name="header_3", data_type=DataType.TEXT),
            ]
        )

        with collection.batch.dynamic() as batch:
            for chunk in chunks:
                meta = chunk["metadata"]
                properties = {
                    "content": chunk["content"],
                    "source": meta.get("source", ""),
                    "doc_type": meta.get("type", ""),
                    "header_1": meta.get("Header 1", ""),
                    "header_2": meta.get("Header 2", ""),
                    "header_3": meta.get("Header 3", ""),
                }
                batch.add_object(
                    properties=properties,
                    vector=chunk["embedding"]
                )


def run_pipeline():
    """Chạy toàn bộ pipeline: load → chunk → embed → index."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print("=" * 50)

    docs = load_documents()
    print(f"\n✓ Loaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"✓ Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"✓ Embedded {len(chunks)} chunks")

    index_to_vectorstore(chunks)
    print("✓ Indexed to vector store")


if __name__ == "__main__":
    run_pipeline()
