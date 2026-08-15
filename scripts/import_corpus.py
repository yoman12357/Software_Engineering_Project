#!/usr/bin/env python3
"""CyberSRS Knowledge Corpus Import and Validation.

Safely imports and validates the RAG starter corpus per security requirements.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import zipfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Security limits
MAX_ARCHIVE_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
ALLOWED_EXTENSIONS = {".pdf", ".csv", ".md", ".txt", ".json"}


@dataclass
class ValidationResult:
    """Result of validating a single document."""
    source_id: str
    file_path: str
    expected_hash: str
    actual_hash: str | None = None
    hash_match: bool = False
    file_exists: bool = False
    file_size: int = 0
    size_match: bool = False
    error: str | None = None


@dataclass
class CorpusInventory:
    """Complete inventory of the knowledge corpus."""
    total_files: int = 0
    files_by_org: dict[str, int] = field(default_factory=dict)
    files_by_type: dict[str, int] = field(default_factory=dict)
    documents: list[dict[str, Any]] = field(default_factory=list)
    missing_metadata: list[str] = field(default_factory=list)
    unreadable_files: list[str] = field(default_factory=list)
    duplicate_hashes: list[str] = field(default_factory=list)
    manual_sources: list[dict[str, Any]] = field(default_factory=list)
    hash_verification: dict[str, Any] = field(default_factory=dict)
    kb_version: str = ""
    validation_errors: list[str] = field(default_factory=list)


class SafeZipExtractor:
    """Secure ZIP extraction with path traversal prevention."""

    def __init__(self, zip_path: str, extract_dir: str, max_size: int = MAX_ARCHIVE_SIZE):
        self.zip_path = zip_path
        self.extract_dir = Path(extract_dir).resolve()
        self.max_size = max_size

    def validate_archive(self) -> tuple[bool, str | None]:
        """Validate archive before extraction."""
        try:
            with zipfile.ZipFile(self.zip_path, "r") as zf:
                # Check total uncompressed size
                total_size = sum(info.file_size for info in zf.infolist())
                if total_size > self.max_size:
                    return False, f"Archive too large: {total_size} bytes (max {self.max_size})"

                # Check individual file paths and sizes
                for info in zf.infolist():
                    if info.file_size > MAX_FILE_SIZE:
                        return False, f"File too large: {info.filename} ({info.file_size} bytes)"

                    # Path traversal check
                    if os.path.isabs(info.filename) or ".." in info.filename:
                        return False, f"Path traversal attempt: {info.filename}"

                    # Check for suspicious paths
                    if info.filename.startswith("/") or info.filename.startswith("\\"):
                        return False, f"Absolute path in archive: {info.filename}"

                return True, None
        except zipfile.BadZipFile as e:
            return False, f"Invalid ZIP file: {e}"

    def extract(self) -> tuple[bool, str | None]:
        """Extract archive safely."""
        ok, err = self.validate_archive()
        if not ok:
            return False, err

        try:
            with zipfile.ZipFile(self.zip_path, "r") as zf:
                zf.extractall(self.extract_dir)
            return True, None
        except Exception as e:
            return False, f"Extraction failed: {e}"


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def validate_manifest(manifest_path: Path) -> tuple[dict | None, list[str]]:
    """Validate manifest.json structure."""
    errors = []
    try:
        with open(manifest_path) as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        return None, [f"Invalid JSON in manifest: {e}"]
    except Exception as e:
        return None, [f"Failed to read manifest: {e}"]

    if "documents" not in manifest:
        errors.append("Manifest missing 'documents' key")
        return None, errors

    required_fields = [
        "source_id", "title", "organization", "version",
        "publication_date", "retrieval_date", "source_url",
        "local_path", "sha256", "size_bytes", "purpose",
        "packaged", "license_note"
    ]

    for i, doc in enumerate(manifest["documents"]):
        for req_field in required_fields:
            if req_field not in doc:
                errors.append(
                    f"Document {i} ({doc.get('source_id', 'unknown')}): "
                    f"missing field '{req_field}'"
                )
        if doc.get("packaged") is True and not doc.get("local_path"):
            errors.append(f"Document {doc.get('source_id')}: packaged=true but no local_path")

    return manifest, errors


def verify_hashes(manifest: dict, corpus_root: Path) -> list[ValidationResult]:
    """Verify SHA-256 hashes of all packaged documents."""
    results = []
    for doc in manifest["documents"]:
        if not doc.get("packaged", False):
            continue

        source_id = doc["source_id"]
        local_path = Path(corpus_root) / doc["local_path"]
        expected_hash = doc["sha256"].lower()
        expected_size = doc["size_bytes"]

        result = ValidationResult(
            source_id=source_id,
            file_path=doc["local_path"],
            expected_hash=expected_hash,
        )

        if not local_path.exists():
            result.error = "File not found"
            results.append(result)
            continue

        result.file_exists = True
        result.file_size = local_path.stat().st_size
        result.size_match = result.file_size == expected_size

        try:
            actual_hash = compute_sha256(local_path)
            result.actual_hash = actual_hash
            result.hash_match = actual_hash == expected_hash
        except Exception as e:
            result.error = f"Hash computation failed: {e}"

        results.append(result)

    return results


def load_manual_sources(manual_path: Path) -> list[dict]:
    """Load manual sources from JSON."""
    try:
        with open(manual_path) as f:
            data = json.load(f)
        return data.get("sources", [])
    except Exception:
        return []


def generate_inventory(
    manifest: dict,
    validation_results: list[ValidationResult],
    manual_sources: list[dict],
    corpus_root: Path,
) -> CorpusInventory:
    """Generate complete corpus inventory."""
    inv = CorpusInventory()

    # Document-level info
    for doc in manifest["documents"]:
        source_id = doc["source_id"]
        org = doc["organization"]
        ext = Path(doc["local_path"]).suffix.lower()
        v_result = next((r for r in validation_results if r.source_id == source_id), None)

        inv.total_files += 1 if doc.get("packaged") else 0
        inv.files_by_org[org] = inv.files_by_org.get(org, 0) + (1 if doc.get("packaged") else 0)
        if doc.get("packaged"):
            inv.files_by_type[ext] = inv.files_by_type.get(ext, 0) + 1

        doc_info = {
            "source_id": source_id,
            "title": doc["title"],
            "organization": org,
            "version": doc["version"],
            "publication_date": doc["publication_date"],
            "retrieval_date": doc["retrieval_date"],
            "source_url": doc["source_url"],
            "local_path": doc.get("local_path"),
            "format": ext,
            "size_bytes": doc["size_bytes"],
            "sha256": doc["sha256"],
            "packaged": doc.get("packaged", False),
            "license_note": doc.get("license_note", ""),
            "hash_verified": v_result.hash_match if v_result else None,
            "size_verified": v_result.size_match if v_result else None,
        }
        inv.documents.append(doc_info)

        # Check for missing metadata
        if not doc.get("publication_date"):
            inv.missing_metadata.append(f"{source_id}: publication_date")
        if not doc.get("license_note"):
            inv.missing_metadata.append(f"{source_id}: license_note")

    # Unreadable files
    for r in validation_results:
        if r.error or not r.file_exists:
            inv.unreadable_files.append(f"{r.source_id}: {r.error or 'file not found'}")

    # Duplicate hashes
    hash_counts: dict[str, list[str]] = {}
    for r in validation_results:
        if r.actual_hash:
            hash_counts.setdefault(r.actual_hash, []).append(r.source_id)
    for _hash, ids in hash_counts.items():
        if len(ids) > 1:
            inv.duplicate_hashes.extend(ids)

    # Manual sources
    inv.manual_sources = manual_sources

    # Hash verification summary
    total = len(validation_results)
    verified = sum(1 for r in validation_results if r.hash_match)
    size_ok = sum(1 for r in validation_results if r.size_match)
    inv.hash_verification = {
        "total_packaged": total,
        "hashes_verified": verified,
        "hashes_failed": total - verified,
        "sizes_verified": size_ok,
        "sizes_mismatch": total - size_ok,
    }

    # Knowledge-base version from manifest content hash
    manifest_content = json.dumps(manifest["documents"], sort_keys=True).encode()
    inv.kb_version = hashlib.sha256(manifest_content).hexdigest()[:16]

    return inv


def print_inventory(inv: CorpusInventory) -> None:
    """Print human-readable inventory."""
    print("=" * 60)
    print("CYBERSRS KNOWLEDGE CORPUS INVENTORY")
    print("=" * 60)
    print(f"Knowledge-base version: {inv.kb_version}")
    print(f"Total packaged files: {inv.total_files}")
    print()

    print("Files by organization:")
    for org, count in sorted(inv.files_by_org.items()):
        print(f"  {org}: {count}")
    print()

    print("Files by type:")
    for ext, count in sorted(inv.files_by_type.items()):
        print(f"  {ext}: {count}")
    print()

    print("Document details:")
    for doc in inv.documents:
        if doc.get("packaged"):
            status = "OK" if doc.get("hash_verified") else "FAIL"
        else:
            status = "SKIP"
        print(f"  [{status}] {doc['source_id']} ({doc['organization']}) - {doc['title'][:60]}")
        if doc.get("packaged") and not doc.get("hash_verified"):
            print("      WARNING: Hash mismatch!")
    print()

    print("Missing metadata:")
    for m in inv.missing_metadata:
        print(f"  - {m}")
    print()

    print("Unreadable/corrupted files:")
    for u in inv.unreadable_files:
        print(f"  - {u}")
    print()

    print("Duplicate hashes:")
    if inv.duplicate_hashes:
        for d in inv.duplicate_hashes:
            print(f"  - {d}")
    else:
        print("  None")
    print()

    print("Manual sources (not bundled):")
    for m in inv.manual_sources:
        print(f"  - {m['source_id']}: {m['title']} ({m['organization']})")
        print(f"    URL: {m['source_url']}")
        print(f"    Reason: {m.get('reason_not_bundled', 'N/A')}")
    print()

    print("Hash verification summary:")
    hv = inv.hash_verification
    print(f"  Total packaged: {hv['total_packaged']}")
    print(f"  Hashes verified: {hv['hashes_verified']}")
    print(f"  Hashes failed: {hv['hashes_failed']}")
    print(f"  Sizes verified: {hv['sizes_verified']}")
    print(f"  Sizes mismatch: {hv['sizes_mismatch']}")
    print()


def main():
    """Main entry point."""
    repo_root = Path(__file__).parent.parent
    corpus_zip = repo_root / "CyberSRS_RAG_Starter_Corpus_2026-08-07.zip"
    extract_dir = repo_root / "corpus_extract"
    knowledge_dir = extract_dir / "CyberSRS_RAG_Corpus" / "knowledge"

    if not corpus_zip.exists():
        print(f"ERROR: Corpus ZIP not found at {corpus_zip}")
        sys.exit(1)

    print(f"Extracting corpus from {corpus_zip}...")
    extractor = SafeZipExtractor(str(corpus_zip), str(extract_dir))
    ok, err = extractor.extract()
    if not ok:
        print(f"ERROR: {err}")
        sys.exit(1)
    print("Extraction complete.\n")

    # Validate manifest
    manifest_path = knowledge_dir / "manifest.json"
    manifest, errors = validate_manifest(manifest_path)
    if errors:
        print("MANIFEST VALIDATION ERRORS:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    if manifest is None:
        print("ERROR: Manifest is None")
        sys.exit(1)

    # Load manual sources
    manual_path = knowledge_dir / "manual_sources.json"
    manual_sources = load_manual_sources(manual_path)

    # Verify hashes
    print("Verifying SHA-256 hashes...")
    validation_results = verify_hashes(manifest, knowledge_dir)

    # Generate inventory
    inventory = generate_inventory(manifest, validation_results, manual_sources, knowledge_dir)

    # Print inventory
    print_inventory(inventory)

    # Save inventory as JSON
    output_path = repo_root / "ai" / "evaluation" / "corpus_inventory.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    inv_dict = {
        "kb_version": inventory.kb_version,
        "total_files": inventory.total_files,
        "files_by_org": inventory.files_by_org,
        "files_by_type": inventory.files_by_type,
        "documents": inventory.documents,
        "missing_metadata": inventory.missing_metadata,
        "unreadable_files": inventory.unreadable_files,
        "duplicate_hashes": inventory.duplicate_hashes,
        "manual_sources": inventory.manual_sources,
        "hash_verification": inventory.hash_verification,
        "generated": datetime.now(UTC).isoformat(),
    }
    with open(output_path, "w") as f:
        json.dump(inv_dict, f, indent=2)
    print(f"\nInventory saved to: {output_path}")

    # Exit with error if any hash failed
    if inventory.hash_verification["hashes_failed"] > 0:
        print("\nWARNING: Some hashes failed verification!")
        sys.exit(1)

    print("\nAll checks passed. Corpus ready for ingestion.")


if __name__ == "__main__":
    main()