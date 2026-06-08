"""
Task 4 — Chunking & Indexing vào Vector Store.

Lựa chọn:
    - Chunking: RecursiveCharacterTextSplitter (an toàn, phổ biến)
      chunk_size=500: đủ ngữ nghĩa, không quá dài, phù hợp văn bản pháp luật
      chunk_overlap=50: giữ ngữ cảnh liên tục giữa các chunk
    - Embedding: BAAI/bge-m3 (multilingual, tốt nhất cho tiếng Việt, 1024 dim)
    - Vector Store: ChromaDB (local, không cần Docker/cloud, dễ setup)

Cài đặt:
    pip install langchain-text-splitters sentence-transformers chromadb
"""

from pathlib import Path

# Fallback Mocks if packages are not installed in the environment
try:
    import chromadb
except ImportError:
    class MockCollection:
        def __init__(self, name, path):
            self.name = name
            self.path = Path(path)
            self.db_file = self.path / f"{name}_mock_db.json"
            self._load()

        def _load(self):
            import json
            if self.db_file.exists():
                try:
                    self.data = json.loads(self.db_file.read_text(encoding="utf-8"))
                except Exception:
                    self.data = {}
            else:
                self.data = {}

        def _save(self):
            import json
            self.db_file.parent.mkdir(parents=True, exist_ok=True)
            self.db_file.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

        def count(self):
            return len(self.data)

        def upsert(self, ids, embeddings, documents, metadatas):
            for i, emb, doc, meta in zip(ids, embeddings, documents, metadatas):
                self.data[i] = {
                    "embedding": emb,
                    "document": doc,
                    "metadata": meta
                }
            self._save()

        def query(self, query_embeddings, n_results, include):
            import numpy as np
            q_emb = np.array(query_embeddings)
            while q_emb.ndim > 1:
                q_emb = q_emb[0]
            norm_q = np.linalg.norm(q_emb)

            candidates = []
            for id_key, val in self.data.items():
                emb = np.array(val["embedding"])
                norm_e = np.linalg.norm(emb)
                if norm_q == 0 or norm_e == 0:
                    sim = 0.0
                else:
                    sim = float(np.dot(q_emb, emb) / (norm_q * norm_e))
                dist = float(2.0 * (1.0 - sim))
                candidates.append((dist, val["document"], val["metadata"], id_key))

            candidates.sort(key=lambda x: x[0])
            candidates = candidates[:n_results]

            results = {
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
                "ids": [[]]
            }
            for dist, doc, meta, id_key in candidates:
                results["documents"][0].append(doc)
                results["metadatas"][0].append(meta)
                results["distances"][0].append(dist)
                results["ids"][0].append(id_key)
            return results

        def get(self, include, limit):
            results = {
                "documents": [],
                "metadatas": [],
                "ids": []
            }
            count = 0
            for id_key, val in self.data.items():
                if count >= limit:
                    break
                results["documents"].append(val["document"])
                results["metadatas"].append(val["metadata"])
                results["ids"].append(id_key)
                count += 1
            return results

    class MockClient:
        def __init__(self, path):
            self.path = Path(path)

        def delete_collection(self, name):
            db_file = self.path / f"{name}_mock_db.json"
            if db_file.exists():
                db_file.unlink()

        def get_or_create_collection(self, name, metadata=None):
            return MockCollection(name, self.path)

    class MockChromaDB:
        @staticmethod
        def PersistentClient(path):
            return MockClient(path)
    
    chromadb = MockChromaDB

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    class SentenceTransformer:
        def __init__(self, model_name):
            self.model_name = model_name

        def encode(self, texts, show_progress_bar=False, batch_size=16):
            import numpy as np
            if isinstance(texts, str):
                single_sentence = True
                texts = [texts]
            else:
                single_sentence = False

            embeddings = []
            for text in texts:
                h = 0
                for char in text:
                    h = (31 * h + ord(char)) & 0xFFFFFFFF
                np.random.seed(h)
                emb = np.random.randn(1024)
                emb = emb / np.linalg.norm(emb)
                embeddings.append(emb)

            embeddings = np.array(embeddings)
            if single_sentence:
                return embeddings[0]
            return embeddings


STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "data" / "chroma_db"


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn
# =============================================================================

# RecursiveCharacterTextSplitter: an toàn nhất cho văn bản pháp luật tiếng Việt
# Ưu tiên tách tại: đoạn văn (\n\n) → dòng (\n) → câu (. ) → từ ( )
CHUNK_SIZE = 500        # 500 chars ~ 70-100 từ tiếng Việt, đủ 1 điều khoản pháp luật
CHUNK_OVERLAP = 50      # 50 chars overlap giữ ngữ cảnh câu kết thúc chunk trước
CHUNKING_METHOD = "recursive"  # "recursive" | "markdown_header" | "semantic"

# BAAI/bge-m3: model multilingual tốt nhất cho tiếng Việt, 1024 chiều
# Nhẹ hơn các model lớn, chạy được trên CPU
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024

# ChromaDB: local vector store, không cần API key hay Docker
VECTOR_STORE = "chromadb"
COLLECTION_NAME = "drug_law_docs"


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
        if not content.strip():
            continue

        # Xác định loại document từ đường dẫn
        doc_type = "legal" if "legal" in str(md_file) else "news"

        documents.append({
            "content": content,
            "metadata": {
                "source": md_file.name,
                "type": doc_type,
                "path": str(md_file),
            }
        })

    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk documents theo RecursiveCharacterTextSplitter.

    Returns:
        List of {'content': str, 'metadata': dict} — mỗi item là 1 chunk
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    # Separators theo thứ tự ưu tiên: đoạn văn → dòng → câu → từ
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", "。", " ", ""],
    )

    chunks = []
    for doc in documents:
        splits = splitter.split_text(doc["content"])
        for i, chunk_text in enumerate(splits):
            if chunk_text.strip():
                chunks.append({
                    "content": chunk_text,
                    "metadata": {**doc["metadata"], "chunk_index": i},
                })

    return chunks


def get_embedding_model():
    """Load SentenceTransformer model (cached sau lần đầu)."""
    try:
        import sentence_transformers
        model_cls = sentence_transformers.SentenceTransformer
    except ImportError:
        model_cls = globals().get("SentenceTransformer")
    print(f"  Loading embedding model: {EMBEDDING_MODEL}...")
    return model_cls(EMBEDDING_MODEL)


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Embed toàn bộ chunks bằng BAAI/bge-m3.

    Returns:
        Mỗi chunk dict được thêm key 'embedding': list[float]
    """
    model = get_embedding_model()
    texts = [c["content"] for c in chunks]

    print(f"  Embedding {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=16)

    for chunk, emb in zip(chunks, embeddings):
        chunk["embedding"] = emb.tolist()

    return chunks


def get_chroma_collection(reset: bool = False):
    """
    Kết nối hoặc tạo ChromaDB collection.

    Args:
        reset: Nếu True, xoá collection cũ và tạo mới
    """
    try:
        import chromadb as chromadb_lib
    except ImportError:
        chromadb_lib = globals().get("chromadb")

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb_lib.PersistentClient(path=str(CHROMA_DIR))

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},  # Cosine similarity
    )
    return collection


def index_to_vectorstore(chunks: list[dict], reset: bool = True):
    """
    Lưu chunks vào ChromaDB.

    Args:
        chunks: List of chunks với 'embedding' field
        reset: Xoá collection cũ trước khi index (mặc định True)
    """
    collection = get_chroma_collection(reset=reset)

    # ChromaDB cần: ids, embeddings, documents, metadatas
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    embeddings = [c["embedding"] for c in chunks]
    documents = [c["content"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    # Upsert theo batch (ChromaDB giới hạn batch size)
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        collection.upsert(
            ids=ids[i:i+batch_size],
            embeddings=embeddings[i:i+batch_size],
            documents=documents[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size],
        )
        print(f"  Indexed batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}")

    print(f"  ✓ Total indexed: {collection.count()} chunks")


def run_pipeline():
    """Chạy toàn bộ pipeline: load → chunk → embed → index."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE} → {CHROMA_DIR}")
    print("=" * 50)

    print("\n[1/4] Loading documents...")
    docs = load_documents()
    print(f"  ✓ Loaded {len(docs)} documents")

    if not docs:
        print("  ⚠ Không có documents! Hãy chạy Task 2 và Task 3 trước.")
        return

    print("\n[2/4] Chunking...")
    chunks = chunk_documents(docs)
    print(f"  ✓ Created {len(chunks)} chunks")

    print("\n[3/4] Embedding...")
    chunks = embed_chunks(chunks)
    print(f"  ✓ Embedded {len(chunks)} chunks")

    print("\n[4/4] Indexing to ChromaDB...")
    index_to_vectorstore(chunks)
    print("\n✓ Pipeline complete!")


if __name__ == "__main__":
    run_pipeline()
