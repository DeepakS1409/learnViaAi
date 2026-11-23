import sqlite3
import os
from contextlib import contextmanager
from app.config import Config

def get_db_connection():
    """Returns a connection to the SQLite database with Row factory."""
    conn = sqlite3.connect(Config.DATABASE_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

@contextmanager
def get_db():
    """Context manager for safe database operations with auto commit/rollback."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def query_one(query, params=()):
    """Helper to query a single row."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None

def query_all(query, params=()):
    """Helper to query multiple rows."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def execute_insert(query, params=()):
    """Helper to execute an INSERT and return the last row ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.lastrowid

def execute_write(query, params=()):
    """Helper to execute UPDATE or DELETE and return rowcount."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.rowcount

