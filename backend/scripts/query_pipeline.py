"""CLI script to test the Query Processing Pipeline locally."""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path so scripts can be run directly
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.qdrant_service import QdrantService
from backend.app.services.retrieval_service import RetrievalService


def print_step_banner(step: str, msg: str):
    symbols = {
        "1_VALIDATE": "❓ [Step 1: Validate Query]",
        "2_EMBED": "🧠 [Step 2: Embed Query]",
        "3_SEARCH": "🔍 [Step 3: Qdrant Search]",
        "4_FILTER": "🎯 [Step 4: Filter Chunks]",
        "5_CONSTRUCT": "🏗️  [Step 5: Construct Context]",
    }
    banner = symbols.get(step, f"⚙️  [{step}]")
    print(f"\n{banner} {msg}")


def main():
    parser = argparse.ArgumentParser(
        description="Run the Query Processing Pipeline (Search & Context Construction) for a natural-language question."
    )
    parser.add_argument(
        "--question",
        type=str,
        required=True,
        help="Natural language question to query.",
    )
    parser.add_argument(
        "--user-id",
        type=str,
        default="test_user_001",
        help="User ID for logical multi-tenant isolation (default: test_user_001).",
    )
    parser.add_argument(
        "--doc-id",
        type=str,
        default=None,
        help="Optional document ID to scope retrieval to a single document.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Maximum number of relevant chunks to retrieve (default: 5).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Minimum similarity score threshold (default: 0.5).",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run using mock embedding (useful for testing without live Gemini API keys).",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Multi-Document RAG Service - Query Processing Pipeline")
    print(f"Question:    {args.question}")
    print(f"User ID:     {args.user_id}")
    print(f"Document ID: {args.doc_id or 'ALL (Multi-Document Search)'}")
    print(f"Top-K:       {args.top_k}")
    print(f"Threshold:   {args.threshold}")
    print("=" * 70)

    if args.mock:
        print("\n[NOTE] Running in MOCK embedding mode.")

        class MockEmbeddingService(EmbeddingService):
            def embed_texts(self, texts, batch_size=None, max_retries=3):
                return [[0.05] * 768 for _ in range(len(texts))]

        service = RetrievalService(
            embedding_service=MockEmbeddingService(),
            qdrant_service=QdrantService(),
        )
    else:
        service = RetrievalService()

    context = service.retrieve_context(
        question=args.question,
        user_id=args.user_id,
        document_id=args.doc_id,
        top_k=args.top_k,
        similarity_threshold=args.threshold,
        on_step=print_step_banner,
    )

    print("\n" + "=" * 70)
    print("CONSTRUCTED CONTEXT FOR GENERATION")
    print("=" * 70)
    if context.formatted_text:
        print(context.formatted_text)
    else:
        print("(No relevant document chunks met the similarity criteria)")

    print("\n" + "=" * 70)
    print("SOURCE CITATIONS")
    print("=" * 70)
    if context.sources:
        for idx, src in enumerate(context.sources, 1):
            page_info = f"Page {src.page}" if src.page else "General"
            print(f"[{idx}] {src.document} | {page_info} | Similarity: {src.score}")
    else:
        print("No sources found.")
    print("=" * 70)


if __name__ == "__main__":
    main()
