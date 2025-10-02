from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class RepositoryMetadata:
    url: str
    persist_dir: str = "./chroma_db"
    vector_db_type: str = "chroma"
    last_crawled: Optional[datetime] = None
    file_count: Optional[int] = None
    chunk_count: Optional[int] = None
    supported_languages: Optional[List[str]] = None
    dependecies: Optional[Dict[str, str]] = None
