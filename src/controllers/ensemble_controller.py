from fastmcp import mcp_tool
from typing import Dict, Any, Optional
from services.ensemble_service import EnsembleRetrievalService
from models.search_models import SearchQuery, RetrievalWeights


class RetrievalController:

    def __init__(self, ensemble_retrieval_service: EnsembleRetrievalService):
        self.ensemble_retrieval_service = ensemble_retrieval_service

    @mcp_tool()
    async def ensemble_search(
        self,
        query: str,
        k: int = 5,
        desne_wieght: float = 0.6,
        sparse_weight: float = 0.4,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """ensemble 검색

        dense, sparse를 가중치에 따라 설정하여 사용"""
        search_query = SearchQuery(text=query, conversation_id=conversation_id)

        weights = RetrievalWeights(dense=desne_wieght, sparse=sparse_weight)

        result = await self.ensemble_retrieval_service.search(search_query, k, weights)
        return result.to_dict()

    @mcp_tool()
    async def adaptive_search(
        self, query: str, k: int = 5, conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """가중치 자동으로 설정하는 방식"""
        search_query = SearchQuery(text=query, conversation_id=conversation_id)
        result = await self.ensemble_retrieval_service.search(search_query, k)

        return {
            **result.to_dict(),
            "auto_optimized": True,
            "query_type": "code" if search_query._is_code_query else "semantic",
        }
