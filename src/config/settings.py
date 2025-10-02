import os
from dataclasses import dataclass


@dataclass
class Config:
    vector_db_host: str
    vector_db_port: int
    vector_db_collection: str

    embedding_model: str
    embedding_dimension: int

    persist_directory: str
    memory_db_path: str


def load_config() -> Config:
    """환경변수에서 설정 로드"""
    return Config(
        vector_db_host=os.getenv("VECTOR_DB_HOST", "localhost"),
        vector_db_port=int(os.getenv("VECTOR_DB_PORT", "8080")),
        vector_db_collection=os.getenv("VECTOR_DB_COLLECTION", "code_collection"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        embedding_dimension=int(os.getenv("EMBEDDING_DIMENSION", "1536")),
        persist_directory=os.getenv("PERSIST_DIRECTORY", "./chroma_db"),
        memory_db_path=os.getenv("MEMORY_DB_PATH", "conversations.db"),
    )
