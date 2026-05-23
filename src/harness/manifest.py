"""Write manifest — tracks every file ``harness`` wrote, with its hash.

On ``harness sync`` (or rerunning ``init``) we use the manifest to:

  * detect drift — a file we wrote that the user later edited
  * refuse to overwrite drifted files unless ``--force`` is passed
  * emit a structured plan of what would change

The manifest lives at ``.harness/manifest.json`` by default.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

MANIFEST_FILENAME = ".harness/manifest.json"


@dataclass
class ManifestEntry:
    """One file we wrote — path is repo-relative."""

    path: str
    sha256: str
    bytes: int
    written_by: str  # adapter or blueprint name


@dataclass
class Manifest:
    """The set of files harness has written to a repo."""

    schema_version: int = 1
    harness_version: str = ""
    entries: list[ManifestEntry] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(
            {
                "schema_version": self.schema_version,
                "harness_version": self.harness_version,
                "entries": [asdict(e) for e in self.entries],
            },
            indent=2,
            sort_keys=False,
        ) + "\n"

    @classmethod
    def load(cls, path: str | Path) -> Manifest:
        p = Path(path)
        if not p.exists():
            return cls()
        data = json.loads(p.read_text())
        entries = [ManifestEntry(**e) for e in data.get("entries", [])]
        return cls(
            schema_version=data.get("schema_version", 1),
            harness_version=data.get("harness_version", ""),
            entries=entries,
        )

    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.to_json())

    def lookup(self, repo_relative_path: str) -> ManifestEntry | None:
        for e in self.entries:
            if e.path == repo_relative_path:
                return e
        return None


# ── helpers ────────────────────────────────────────────────────────────────


def hash_file(path: Path) -> str:
    """Return the sha256 hex digest of a file."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_entry(*, repo_root: Path, path: Path, written_by: str) -> ManifestEntry:
    """Create a manifest entry for a file that exists on disk."""
    rel = str(path.resolve().relative_to(repo_root.resolve()))
    return ManifestEntry(
        path=rel,
        sha256=hash_file(path),
        bytes=path.stat().st_size,
        written_by=written_by,
    )


def file_matches_manifest(repo_root: Path, entry: ManifestEntry) -> bool:
    """True iff the file on disk matches the manifest hash."""
    p = repo_root / entry.path
    if not p.exists():
        return False
    return hash_file(p) == entry.sha256


def detect_drift(repo_root: Path, manifest: Manifest) -> list[ManifestEntry]:
    """Return manifest entries whose on-disk file no longer matches.

    Used by ``harness sync --check`` to exit non-zero in CI when generated
    files have been hand-edited.
    """
    drifted: list[ManifestEntry] = []
    for e in manifest.entries:
        if not file_matches_manifest(repo_root, e):
            drifted.append(e)
    return drifted


__all__ = [
    "MANIFEST_FILENAME",
    "Manifest",
    "ManifestEntry",
    "build_entry",
    "detect_drift",
    "file_matches_manifest",
    "hash_bytes",
    "hash_file",
]
