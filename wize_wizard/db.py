from __future__ import annotations
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / ".local" / "share" / "wize-wizard" / "wize.db"

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS projects (
  id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS strategy (
  id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER NOT NULL, category TEXT NOT NULL, level TEXT NOT NULL,
  as_a TEXT DEFAULT '', need TEXT NOT NULL, so_that TEXT NOT NULL, because TEXT DEFAULT '', priority INTEGER DEFAULT 3,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS clay_tablets (
  id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER NOT NULL, strategy_id INTEGER, text TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
  FOREIGN KEY(strategy_id) REFERENCES strategy(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER NOT NULL, strategy_id INTEGER,
  title TEXT NOT NULL, as_a TEXT DEFAULT '', need TEXT DEFAULT '', so_that TEXT DEFAULT '', because TEXT DEFAULT '',
  source_level TEXT DEFAULT '', priority INTEGER DEFAULT 3, status TEXT DEFAULT 'Backlog', created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE, FOREIGN KEY(strategy_id) REFERENCES strategy(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS pert (
  id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER NOT NULL, task_id INTEGER, unit TEXT NOT NULL,
  optimistic REAL NOT NULL, likely REAL NOT NULL, pessimistic REAL NOT NULL, severity INTEGER DEFAULT 3,
  estimate_mode TEXT DEFAULT '3-point', expected REAL NOT NULL, sigma REAL NOT NULL, low_stress REAL NOT NULL,
  high_stress REAL NOT NULL, derived INTEGER DEFAULT 0, confidence_sentence TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE, FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS communications (
  id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER NOT NULL, people INTEGER NOT NULL, channels INTEGER NOT NULL,
  suggested_group_size INTEGER NOT NULL, groups INTEGER DEFAULT 1, structured_channels INTEGER DEFAULT 0,
  reduction INTEGER DEFAULT 0, reduction_pct REAL DEFAULT 0, report TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS journal (
  id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER NOT NULL, body TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);
"""

MIGRATIONS = {
    "tasks": {"as_a":"TEXT DEFAULT ''", "need":"TEXT DEFAULT ''", "so_that":"TEXT DEFAULT ''", "because":"TEXT DEFAULT ''", "source_level":"TEXT DEFAULT ''"},
    "pert": {"derived":"INTEGER DEFAULT 0", "confidence_sentence":"TEXT DEFAULT ''"},
    "communications": {"groups":"INTEGER DEFAULT 1", "structured_channels":"INTEGER DEFAULT 0", "reduction":"INTEGER DEFAULT 0", "reduction_pct":"REAL DEFAULT 0", "report":"TEXT DEFAULT ''"},
}

def _migrate(con: sqlite3.Connection) -> None:
    for table, cols in MIGRATIONS.items():
        existing = {r[1] for r in con.execute(f"PRAGMA table_info({table})")}
        for name, decl in cols.items():
            if name not in existing:
                con.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")
    con.commit()

def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    _migrate(con)
    return con
