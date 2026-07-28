from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactRecord:
    artifact_id: str
    storage_key: str
    artifact_type: str
    mime_type: str | None
    size_bytes: int | None
    checksum_sha256: str | None
    retention_state: str


@dataclass(frozen=True)
class PublicArtifactDescriptor:
    artifact_id: str
    artifact_type: str
    mime_type: str | None
    size_bytes: int | None
    checksum_sha256: str | None
    retention_state: str


class ArtifactService:
    @staticmethod
    def to_public_descriptor(record: ArtifactRecord) -> PublicArtifactDescriptor:
        return PublicArtifactDescriptor(
            artifact_id=record.artifact_id,
            artifact_type=record.artifact_type,
            mime_type=record.mime_type,
            size_bytes=record.size_bytes,
            checksum_sha256=record.checksum_sha256,
            retention_state=record.retention_state,
        )
