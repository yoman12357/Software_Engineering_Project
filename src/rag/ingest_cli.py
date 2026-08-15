#!/usr/bin/env python3
"""RAG ingestion CLI for CyberSRS.

Usage:
    python -m src.rag.ingest_cli --manifest path/to/manifest.json --corpus-root path/to/knowledge

This script ingests the knowledge corpus into ChromaDB for RAG retrieval.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from src.core.config import Settings
from src.rag.ingestion import run_ingestion


def setup_logging(level: str = "INFO") -> None:
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CyberSRS RAG Ingestion Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m src.rag.ingest_cli --manifest knowledge/manifest.json "
            "--corpus-root knowledge\n"
            "  python -m src.rag.ingest_cli --manifest knowledge/manifest.json "
            "--corpus-root knowledge --force\n"
            "  python -m src.rag.ingest_cli --manifest knowledge/manifest.json "
            "--corpus-root knowledge --log-level DEBUG"
        ),
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Path to manifest.json",
    )
    parser.add_argument(
        "--corpus-root",
        type=Path,
        required=True,
        help="Root directory of the knowledge corpus (e.g., knowledge/)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-ingestion of already indexed documents",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate manifest and files without ingesting",
    )

    args = parser.parse_args()

    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    # Validate inputs
    if not args.manifest.exists():
        logger.error(f"Manifest not found: {args.manifest}")
        return 1

    if not args.corpus_root.exists():
        logger.error(f"Corpus root not found: {args.corpus_root}")
        return 1

    # Load settings
    settings = Settings()

    if args.dry_run:
        logger.info("DRY RUN: Validating manifest and files only")
        with open(args.manifest) as f:
            manifest = json.load(f)

        total_docs = 0
        total_size = 0
        for doc in manifest.get("documents", []):
            if doc.get("packaged", False):
                total_docs += 1
                file_path = args.corpus_root / doc["local_path"]
                if file_path.exists():
                    total_size += file_path.stat().st_size
                    logger.info(f"  OK: {doc['source_id']} ({file_path})")
                else:
                    logger.warning(f"  MISSING: {doc['source_id']} ({file_path})")

        logger.info(f"Dry run complete: {total_docs} documents, {total_size / 1024 / 1024:.2f} MB")
        return 0

    # Run ingestion
    logger.info("Starting RAG ingestion pipeline...")
    logger.info(f"Manifest: {args.manifest}")
    logger.info(f"Corpus root: {args.corpus_root}")
    logger.info(f"Force re-ingest: {args.force}")

    try:
        stats = run_ingestion(
            manifest_path=args.manifest,
            corpus_root=args.corpus_root,
            settings=settings,
            force=args.force,
        )

        # Print summary
        print("\n" + "=" * 60)
        print("INGESTION COMPLETE")
        print("=" * 60)
        print(f"Documents processed: {stats.documents_processed}")
        print(f"Documents failed:    {stats.documents_failed}")
        print(f"Total chunks:        {stats.total_chunks}")
        print(f"Total embeddings:    {stats.total_embeddings}")
        print(f"Elapsed time:        {stats.total_time_seconds:.1f}s")
        print(f"KB version:          {stats.kb_version}")

        if stats.errors:
            print(f"\nErrors ({len(stats.errors)}):")
            for err in stats.errors:
                print(f"  - {err}")

        if stats.documents_failed > 0:
            return 1

        return 0

    except Exception as e:
        logger.exception(f"Ingestion failed: {e}")
        return 1


if __name__ == "__main__":
    import json

    sys.exit(main())
