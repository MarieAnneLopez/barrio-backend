"""Control de revisiones y adopción de datos existentes durante un despliegue."""
from hashlib import sha256
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.seed_manifest import SeedManifest

# Bloqueo transaccional compartido por bootstrap y las cargas CLI en esta base.
LOCK = text("SELECT pg_advisory_xact_lock(8752153114027)")


def digest(paths: list[Path]) -> str:
    revision = sha256()
    for path in paths:
        revision.update(path.name.encode())
        revision.update(sha256(path.read_bytes()).digest())
    return revision.hexdigest()


def save(session: Session, scope: str, version: str, records: dict[str, Any]) -> None:
    session.merge(SeedManifest(scope=scope, digest=version, records=records))
    session.flush()
