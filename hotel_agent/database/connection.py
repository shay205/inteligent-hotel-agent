"""The only place that opens SQLite connections.

Every method opens a short-lived connection. This is simple, thread-safe
(Streamlit runs scripts in different threads) and means data is committed
immediately, so it survives closing and reopening the app.
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence

from hotel_agent.config import DB_PATH
from hotel_agent.database.schema import SCHEMA_STATEMENTS


class Database:
    def __init__(self, path=DB_PATH):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def _connect(self) -> sqlite3.Connection:
        # isolation_level=None -> autocommit; we start transactions ourselves.
        conn = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self) -> None:
        conn = self._connect()
        try:
            for statement in SCHEMA_STATEMENTS:
                conn.execute(statement)
        finally:
            conn.close()

    def execute(self, sql: str, params: Sequence[Any] = ()) -> int:
        """Run one write statement (auto-committed). Returns the new row id."""
        conn = self._connect()
        try:
            cursor = conn.execute(sql, params)
            return cursor.lastrowid
        finally:
            conn.close()

    def query(self, sql: str, params: Sequence[Any] = ()) -> List[Dict[str, Any]]:
        conn = self._connect()
        try:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]
        finally:
            conn.close()

    def query_one(self, sql: str, params: Sequence[Any] = ()) -> Optional[Dict[str, Any]]:
        rows = self.query(sql, params)
        return rows[0] if rows else None

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """All-or-nothing block.

        BEGIN IMMEDIATE takes the write lock straight away, so two people
        booking at the same moment are processed one after the other. This is
        what makes the double-booking check safe.
        """
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.execute("COMMIT")
        except BaseException:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()