from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum


class QueryType(Enum):
    CODE = "code"
    SEMANTIC = "semantic"
    GENERAL = "general"


@dataclass
class SearchQuery:
    text: str
    query_type: QueryType = QueryType.GENERAL
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None


@dataclass
class RetrievalWeights:
    dense: float = 0.6
    sparse: float = 0.4


@dataclass
class SearchResult:
    documents: List[Dict[str, Any]]
    scores: List[float]
    method: str
    weights_used: RetrievalWeights
    total_time: float

    def to_dict(self) -> Dict[str, Any]:
        """Dict타입으로 변환"""
        return {
            "documents": self.documents,
            "scores": self.scores,
            "method": self.method,
            "weights": {
                "dense": self.weights_used.dense,
                "sparse": self.weights_used.sparse,
            },
            "processing_time": self.total_time,
            "total_results": len(self.documents),
        }
