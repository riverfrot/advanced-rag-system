"""
대화 메모리 저장소 구현
"""

import sqlite3
import json
from typing import Optional, List
from datetime import datetime
from pathlib import Path
from ...models.memory_models import Conversation, Interaction


class ConversationStore:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def init_database(self):
        conn = self.get_sqlite_connect()
        cursor = conn.cursor()

        # 대화 테이블
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                topic TEXT NOT NULL,
                summary TEXT,
                created_date TEXT NOT NULL,
                update_date TEXT NOT NULL
            )
        """
        )

        # 상호작용 테이블
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                user_message TEXT NOT NULL,
                assistant_response TEXT NOT NULL,
                search_results TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                    ON DELETE CASCADE
            )
        """
        )

        conn.commit()
        conn.close()

    async def save(self, conversation: Conversation) -> None:
        conn = self.get_sqlite_connect()
        cursor = conn.cursor()

        # 대화 정보 저장/업데이트
        cursor.execute(
            """
            INSERT OR REPLACE INTO conversations 
            (id, user_id, topic, summary, created_date, update_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                conversation.id,
                conversation.user_id,
                conversation.topic,
                conversation.summary,
                conversation.created_date.isoformat(),
                conversation.update_date.isoformat(),
            ),
        )

        # 기존 상호작용 삭제
        cursor.execute(
            "DELETE FROM interactions WHERE conversation_id = ?", (conversation.id,)
        )

        # 상호작용 저장
        for interaction in conversation.interactions:
            search_results_json = None
            if interaction.search_results:
                search_results_json = json.dumps(interaction.search_results)

            cursor.execute(
                """
                INSERT INTO interactions 
                (conversation_id, user_message, assistant_response, 
                 search_results, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    conversation.id,
                    interaction.user_message,
                    interaction.assistant_response,
                    search_results_json,
                    interaction.timestamp.isoformat(),
                ),
            )

        conn.commit()
        conn.close()

    async def get(self, conversation_id: str) -> Optional[Conversation]:
        conn = self.get_sqlite_connect()
        cursor = conn.cursor()

        # 대화 정보 조회
        cursor.execute(
            """
            SELECT id, user_id, topic, summary, created_date, update_date
            FROM conversations 
            WHERE id = ?
        """,
            (conversation_id,),
        )

        conv_row = cursor.fetchone()
        if not conv_row:
            conn.close()
            return None

        # 상호작용 조회
        cursor.execute(
            """
            SELECT user_message, assistant_response, search_results, timestamp
            FROM interactions 
            WHERE conversation_id = ?
            ORDER BY timestamp ASC
        """,
            (conversation_id,),
        )

        interaction_rows = cursor.fetchall()
        conn.close()

        # Conversation 객체 재구성
        interactions = []
        for row in interaction_rows:
            search_results = None
            if row[2]:  # search_results
                try:
                    search_results = json.loads(row[2])
                except json.JSONDecodeError:
                    search_results = None

            interaction = Interaction(
                user_message=row[0],
                assistant_response=row[1],
                search_results=search_results,
                timestamp=datetime.fromisoformat(row[3]),
            )
            interactions.append(interaction)

        conversation = Conversation(
            id=conv_row[0],
            user_id=conv_row[1],
            topic=conv_row[2],
            interactions=interactions,
            created_date=datetime.fromisoformat(conv_row[4]),
            update_date=datetime.fromisoformat(conv_row[5]),
            summary=conv_row[3],
        )

        return conversation

    async def get_by_user(
        self, user_id: str, limit: int = 10, offset: int = 0
    ) -> List[Conversation]:
        conn = self.get_sqlite_connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, user_id, topic, summary, created_date, update_date
            FROM conversations 
            WHERE user_id = ?
            ORDER BY update_date DESC
            LIMIT ? OFFSET ?
        """,
            (user_id, limit, offset),
        )

        conversations = []
        for row in cursor.fetchall():
            conversation = Conversation(
                id=row[0],
                user_id=row[1],
                topic=row[2],
                interactions=[],  # 목록에서는 빈 리스트
                created_date=datetime.fromisoformat(row[4]),
                update_date=datetime.fromisoformat(row[5]),
                summary=row[3],
            )
            conversations.append(conversation)

        conn.close()
        return conversations

    async def delete(self, conversation_id: str) -> bool:
        conn = self.get_sqlite_connect()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        deleted_rows = cursor.rowcount

        conn.commit()
        conn.close()

        return deleted_rows > 0

    async def remove_old_conversations(self, user_id: str, days_old: int = 30) -> int:
        cutoff_date = datetime.now().replace(microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_old)

        conn = self.get_sqlite_connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM conversations 
            WHERE user_id = ? AND update_date < ?
        """,
            (user_id, cutoff_date.isoformat()),
        )

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted_count

    def get_sqlite_connect(self):
        return sqlite3.connect(self.db_path)

    def commit(self, conn):
        conn.commit()
