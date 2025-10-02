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

    @property
    def _is_code_query(self, query_text: str) -> bool:
        """코드 관련 쿼리 판단"""
        code_indicators = [
            "function",
            "class",
            "method",
            "def ",
            "import",
            "async",
            "await",
            "=>",
        ]
        return any(indicator in query_text.lower() for indicator in code_indicators)


@dataclass
class RetrievalWeights:
    dense: float = 0.6
    sparse: float = 0.4

    def __post_init_(self):
        if abs(self.dense + self.sparse - 1.0) > 0.001:
            raise ValueError("가중치 합은 1.0이하여야 합니다")

    @classmethod
    def for_code_search(cls):
        """sparse 기반 가중치 추가

        해당 함수는 sparse 가중치값을 더추가하여 코드기반를 기반으로 파악하는 용도로 사용"""
        return cls(dense=0.4, sparse=0.6)

    @classmethod
    def for_semantic_search(cls):
        """시맨틱 기반 가중치 추가

        해당 함수는 dense 가중치값을 더추가하여 코드기반이 아닌 사용자의 질문의도 또는 주석을 파악하는 용도로 사용"""
        return cls(dense=0.8, sparse=0.2)


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
