"""CLI script to ingest documents locally and verify each pipeline step."""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path so scripts can be run directly
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.services.document_service import DocumentService
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.qdrant_service import QdrantService


def print_step_banner(step: str, msg: str):
    symbols = {
        "1_UPLOAD": "📁 [Step 1: Upload]",
        "2_VALIDATE": "🔍 [Step 2: Validate]",
        "3_PARSE": "📄 [Step 3: Parse]",
        "4_CLEAN": "🧹 [Step 4: Clean]",
        "5_CHUNK": "✂️  [Step 5: Chunk]",
        "6_EMBED": "🧠 [Step 6: Embed]",
        "7_STORE": "💾 [Step 7: Store in Qdrant]",
        "FAILED": "❌ [Failed]",
    }
    banner = symbols.get(step, f"⚙️  [{step}]")
    print(f"\n{banner} {msg}")


def main():
    parser = argparse.ArgumentParser(
        description="Run the 7-step Document Ingestion Pipeline for a local document."
    )
    parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="Path to the document to ingest (.pdf, .docx, .txt)."
    )
    parser.add_argument(
        "--user-id",
        type=str,
        default="test_user_001",
        help="User ID for logical multi-tenant isolation (default: test_user_001)."
    )
    parser.add_argument(
        "--doc-id",
        type=str,
        default=None,
        help="Optional custom document ID."
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run using mock embedding and in-memory Qdrant (useful for testing without live API keys)."
    )

    args = parser.parse_args()
    file_path = Path(args.file)

    print("=" * 70)
    print("Multi-Document RAG Service - Document Ingestion Pipeline")
    print(f"Target Document: {file_path}")
    print(f"User ID:         {args.user_id}")
    print("=" * 70)

    if args.mock:
        print("\n[NOTE] Running in MOCK mode (in-memory Qdrant & synthetic embeddings).")
        
        class MockEmbeddingService(EmbeddingService):
            def embed_texts(self, texts, batch_size=None, max_retries=3):
                # Return dummy 768-dim vectors
                return [[0.01 * (i + 1)] * 768 for i in range(len(texts))]

        class MockQdrantService(QdrantService):
            def __init__(self):
                super().__init__(url=":memory:", collection_name="rag_documents")

        service = DocumentService(
            embedding_service=MockEmbeddingService(),
            qdrant_service=MockQdrantService()
        )
    else:
        service = DocumentService()

    result = service.ingest_file(
        file_path=file_path,
        user_id=args.user_id,
        document_id=args.doc_id,
        on_step=print_step_banner
    )

    print("\n" + "=" * 70)
    print("INGESTION SUMMARY")
    print("=" * 70)
    print(f"Status:       {result.status.value}")
    print(f"Document ID:  {result.document_id}")
    print(f"Document:     {result.document_name}")
    print(f"User ID:      {result.user_id}")
    print(f"Total Chunks: {result.chunk_count}")
    if result.error:
        print(f"Error:        {result.error}")
        sys.exit(1)
    else:
        print("🎉 Document successfully processed and stored into Qdrant!")
        print("=" * 70)


if __name__ == "__main__":
    main()
