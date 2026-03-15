"""
Local SQLite Database for Offline Operation
Location: backend/src/offline/local_db.py
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
from ..utils.logger import get_logger
from ..config.settings import config

logger = get_logger(__name__)

class LocalDB:
    """
    SQLite database for offline storage
    """
    
    def __init__(self):
        self.db_path = Path(config.DATA_DIR) / "local.db"
        self._init_db()
        
    def _init_db(self) -> None:
        """Initialize database tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create textbooks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS textbooks (
                    id TEXT PRIMARY KEY,
                    subject TEXT,
                    grade INTEGER,
                    title TEXT,
                    content TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP,
                    last_accessed TIMESTAMP
                )
            """)
            
            # Create queries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS queries (
                    id TEXT PRIMARY KEY,
                    student_id TEXT,
                    query TEXT,
                    response TEXT,
                    model_used TEXT,
                    tokens_saved INTEGER,
                    created_at TIMESTAMP,
                    synced INTEGER DEFAULT 0
                )
            """)
            
            # Create cache table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP
                )
            """)
            
            # Create sync_queue table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_queue (
                    id TEXT PRIMARY KEY,
                    item_type TEXT,
                    item_data TEXT,
                    attempts INTEGER DEFAULT 0,
                    created_at TIMESTAMP,
                    last_attempt TIMESTAMP
                )
            """)
            
            conn.commit()
            
        logger.info("Local database initialized")
    
    @contextmanager
    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def save_textbook(self, textbook_id: str, data: Dict[str, Any]) -> None:
        """Save textbook to local DB"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO textbooks 
                (id, subject, grade, title, content, metadata, created_at, last_accessed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                textbook_id,
                data.get('subject'),
                data.get('grade'),
                data.get('title'),
                json.dumps(data.get('content')),
                json.dumps(data.get('metadata', {})),
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat()
            ))
            conn.commit()
    
    def get_textbook(self, textbook_id: str) -> Optional[Dict[str, Any]]:
        """Get textbook from local DB"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM textbooks WHERE id = ?",
                (textbook_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def save_query(self, query_data: Dict[str, Any]) -> None:
        """Save query to local DB"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO queries 
                (id, student_id, query, response, model_used, tokens_saved, created_at, synced)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                query_data.get('id'),
                query_data.get('student_id'),
                query_data.get('query'),
                json.dumps(query_data.get('response')),
                query_data.get('model_used'),
                query_data.get('tokens_saved', 0),
                datetime.utcnow().isoformat(),
                0
            ))
            conn.commit()
    
    def get_unsynced_queries(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get queries that haven't been synced"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM queries 
                WHERE synced = 0 
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_as_synced(self, query_ids: List[str]) -> None:
        """Mark queries as synced"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ','.join(['?'] * len(query_ids))
            cursor.execute(f"""
                UPDATE queries 
                SET synced = 1 
                WHERE id IN ({placeholders})
            """, query_ids)
            conn.commit()
    
    def cache_get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT value FROM cache 
                WHERE key = ? AND expires_at > ?
            """, (key, datetime.utcnow().isoformat()))
            
            row = cursor.fetchone()
            if row:
                return json.loads(row['value'])
            return None
    
    def cache_set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set item in cache"""
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO cache (key, value, expires_at, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                key,
                json.dumps(value),
                expires_at.isoformat(),
                datetime.utcnow().isoformat()
            ))
            conn.commit()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Count textbooks
            cursor.execute("SELECT COUNT(*) FROM textbooks")
            stats['textbooks'] = cursor.fetchone()[0]
            
            # Count queries
            cursor.execute("SELECT COUNT(*) FROM queries")
            stats['total_queries'] = cursor.fetchone()[0]
            
            # Count unsynced
            cursor.execute("SELECT COUNT(*) FROM queries WHERE synced = 0")
            stats['unsynced_queries'] = cursor.fetchone()[0]
            
            # Count cache items
            cursor.execute("SELECT COUNT(*) FROM cache")
            stats['cache_items'] = cursor.fetchone()[0]
            
            # Database size
            stats['db_size_mb'] = self.db_path.stat().st_size / (1024 * 1024)
            
            return stats