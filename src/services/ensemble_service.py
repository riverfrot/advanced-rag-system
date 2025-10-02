import asyncio
import time
from typing import List, Dict, Any, Optional
from ..models.search_models import SearchQuery, SearchResult, RetrievalWeights
from ..infrastructure.retrievers.dense_retriever import DenseReriever
from ..infrastructure.retrievers.sparse_retriever import SparseRetriever


class EnsembleRetrievalService:
    def __init__(
        self, dense_retriever: DenseReriever, sparse_retriever: SparseRetriever
    ):
        self.dense_retriever = dense_retriever
        self.sparse_retriever = sparse_retriever

    async def search(
        self, query: SearchQuery, k: int = 5, weights: Optional[RetrievalWeights] = None
    ) -> SearchResult:
        start_time = time.time()

        if weights is None:
            weights = self._get_optimal_wieghts(query)

        dense_task = self.dense_retriever.search(query.text, k)
        sparse_task = self.sparse_retriever.search(query.text, k)

        dense_results, sparse_results = await asyncio.gather(dense_task, sparse_task)

        # RRF
        combined_results = self._combine_with_rrf(
            dense_results, sparse_results, weights, k
        )

        processing_time = time.time() - start_time

        return SearchResult(
            documents=combined_results["documents"],
            scores=combined_results["scores"],
            method="ensemble_rrf",
            weights_used=weights,
            total_time=processing_time,
        )

    def _get_optimal_wieghts(self, query: SearchQuery) -> RetrievalWeights:
        if query.is_code_query:
            return RetrievalWeights.for_code_search()
        return RetrievalWeights.for_semantic_search()

    def _combine_with_rrf(
        self,
        dense_results: List[Dict],
        sparse_results: List[Dict],
        weights: RetrievalWeights,
        k: int = 60,
    ) -> Dict[str, List]:
        doc_scores = {}

        # Dense 가중치 취합 하여 doc_scoredp 저장
        for rank, doc in enumerate(dense_results):
            doc_id = doc.get("id", doc.get("page_content", "")[:50])
            rrf_score = weights.dense / (k + rank + 1)
            doc_scores[doc_id] = {
                "score": doc_scores.get(doc_id, {}).get("score", 0) + rrf_score,
                "document": doc,
            }

        # Sparse 가중취 취합하여 doc_scoredp 저장
        for rank, doc in enumerate(sparse_results):
            doc_id = doc.get("id", doc.get("page_content", "")[:50])
            rrf_score = weights.sparse / (k + rank + 1)
            if doc_id in doc_scores:
                doc_scores[doc_id]["score"] += rrf_score
            else:
                doc_scores[doc_id] = {"score": rrf_score, "document": doc}

        # dense, sparse 중 점수 기준으로 정렬
        sorted_results = sorted(
            doc_scores.values(), key=lambda x: x["score"], reverse=True
        )

        return {
            "documents": [item["document"] for item in sorted_results],
            "scores": [item["score"] for item in sorted_results],
        }
