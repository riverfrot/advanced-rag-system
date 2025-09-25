import dataclass
from typing import List, Dict, datetime


@dataclass
class RepositoryMetadata:
    url: str
    persist_dir: str = "./chroma_db"
    vector_db_type: str = "chroma"
    last_crawled: datetime
    file_count: int
    chunk_count: int
    supported_languages: List[str]
    dependencies: Dict[str, str]
