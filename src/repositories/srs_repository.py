"""Data-access operations for :class:`SRSVersion` (DATA_MODEL §2.6).

Version persistence rules:
- A new generation always inserts a new ``SRSVersion`` row with
  ``version_number`` = max existing + 1 (starts at 1). History is never
  overwritten (FR-064 / DATA_MODEL version behaviour).
- Retrieval is scoped by ``project_id`` so a version can never be fetched for
  the wrong project.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db.models import SRSVersion


class SRSVersionRepository:
    """Persistence helpers for :class:`SRSVersion`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def next_version_number(self, project_id: str) -> int:
        """Return the next sequential version number for a project.

        Starts at 1 for the first SRS version and increments for every new
        version (DATA_MODEL §2.6 version_number auto-increment).
        """
        max_number = self._session.scalar(
            select(func.max(SRSVersion.version_number)).where(SRSVersion.project_id == project_id)
        )
        return (max_number or 0) + 1

    def add(self, version: SRSVersion) -> SRSVersion:
        """Persist a new SRS version row."""
        self._session.add(version)
        self._session.flush()
        return version

    def get_latest_for_project(self, project_id: str) -> SRSVersion | None:
        """Return the most recently created SRS version for a project, or None."""
        stmt = (
            select(SRSVersion)
            .where(SRSVersion.project_id == project_id)
            .order_by(SRSVersion.version_number.desc())
            .limit(1)
        )
        return self._session.scalars(stmt).first()

    def list_for_project(self, project_id: str) -> list[SRSVersion]:
        """Return all SRS versions for a project, newest first."""
        stmt = (
            select(SRSVersion)
            .where(SRSVersion.project_id == project_id)
            .order_by(SRSVersion.version_number.desc())
        )
        return list(self._session.scalars(stmt))

    def get_version(self, project_id: str, version_id: str) -> SRSVersion | None:
        """Return a specific SRS version scoped to a project, or None."""
        stmt = select(SRSVersion).where(
            SRSVersion.project_id == project_id,
            SRSVersion.id == version_id,
        )
        return self._session.scalars(stmt).first()

    def save(self, version: SRSVersion) -> SRSVersion:
        """Persist changes made to an existing SRS version."""
        self._session.flush()
        return version
