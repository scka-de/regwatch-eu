"""SQLite cache for classified regulatory changes."""

import sqlite3
from datetime import date

from regwatch.models import ClassifiedChange

CURRENT_SCHEMA_VERSION = 1

_CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS changes (
    id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    title TEXT NOT NULL,
    regulation TEXT,
    type TEXT NOT NULL,
    urgency TEXT NOT NULL,
    source TEXT NOT NULL,
    url TEXT NOT NULL,
    summary TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_changes_regulation ON changes(regulation);
CREATE INDEX IF NOT EXISTS idx_changes_date ON changes(date);
CREATE INDEX IF NOT EXISTS idx_changes_source ON changes(source);
"""


class Cache:
    """SQLite-backed cache for classified regulatory changes."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(_CREATE_TABLES)
        # Set version if not present
        row = self._conn.execute("SELECT version FROM schema_version").fetchone()
        if row is None:
            self._conn.execute(
                "INSERT INTO schema_version (version) VALUES (?)",
                (CURRENT_SCHEMA_VERSION,),
            )
            self._conn.commit()

    def upsert(self, changes: list[ClassifiedChange]) -> int:
        """Insert or update changes. Returns count of items processed."""
        cursor = self._conn.cursor()
        new_count = 0
        for change in changes:
            cursor.execute(
                """INSERT OR REPLACE INTO changes
                   (id, date, title, regulation, type, urgency, source, url, summary)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    change.id,
                    change.date.isoformat(),
                    change.title,
                    change.regulation,
                    change.type,
                    change.urgency,
                    change.source,
                    change.url,
                    change.summary,
                ),
            )
            new_count += cursor.rowcount
        self._conn.commit()
        return new_count

    def query(
        self,
        regulations: list[str] | None = None,
        since: date | None = None,
        types: list[str] | None = None,
        sources: list[str] | None = None,
    ) -> list[ClassifiedChange]:
        """Query changes with optional filters."""
        conditions: list[str] = []
        params: list[str] = []

        if regulations:
            placeholders = ",".join("?" for _ in regulations)
            conditions.append(f"regulation IN ({placeholders})")
            params.extend(regulations)

        if since:
            conditions.append("date >= ?")
            params.append(since.isoformat())

        if types:
            placeholders = ",".join("?" for _ in types)
            conditions.append(f"type IN ({placeholders})")
            params.extend(types)

        if sources:
            placeholders = ",".join("?" for _ in sources)
            conditions.append(f"source IN ({placeholders})")
            params.extend(sources)

        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        columns = "id, date, title, regulation, type, urgency, source, url, summary"
        sql = f"SELECT {columns} FROM changes{where} ORDER BY date DESC"

        rows = self._conn.execute(sql, params).fetchall()
        return [
            ClassifiedChange(
                id=row["id"],
                title=row["title"],
                date=date.fromisoformat(row["date"]),
                url=row["url"],
                source=row["source"],
                regulation=row["regulation"],
                type=row["type"],
                urgency=row["urgency"],
                summary=row["summary"],
            )
            for row in rows
        ]

    def last_update(self, source: str) -> date | None:
        """Return the most recent date for a given source, or None."""
        row = self._conn.execute(
            "SELECT MAX(date) as max_date FROM changes WHERE source = ?",
            (source,),
        ).fetchone()
        if row and row["max_date"]:
            return date.fromisoformat(row["max_date"])
        return None

    def schema_version(self) -> int:
        """Return the current schema version."""
        row = self._conn.execute("SELECT version FROM schema_version").fetchone()
        return row["version"]

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
