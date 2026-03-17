# codeguard_pro/database/db.py

import sqlite3
from pathlib import Path

DB_PATH = Path("review_history.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        issues INTEGER,
        quality_score REAL,
        timestamp TEXT
    )
    """)

    conn.commit()
    conn.close()

def save_review(record):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO reviews (filename, issues, quality_score, timestamp)
    VALUES (?, ?, ?, ?)
    """, (
        record["filename"],
        record["issues"],
        record["quality_score"],
        record["timestamp"]
    ))

    conn.commit()
    conn.close()