"""Schema-aware data access used by commands."""

from __future__ import annotations

import sqlite3

from ..schema import SchemaFamily, SchemaInfo, detect_schema
from .base import BaseStore
from .v1 import V1Store
from .v2 import V2Store

__all__ = ["BaseStore", "V1Store", "V2Store", "open_store"]


def open_store(conn: sqlite3.Connection, schema: SchemaInfo | None = None) -> BaseStore:
    """Return the store matching the actual database schema."""
    info = schema or detect_schema(conn)
    if info.family is SchemaFamily.V2:
        return V2Store(conn, info)
    return V1Store(conn, info)
