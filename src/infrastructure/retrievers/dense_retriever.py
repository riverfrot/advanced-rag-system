from typing import List, Dict, Any
import asyncio


class DenseReriever:
    def __init__(self, vector_store):
        self.vector_store = vector_store

    async def search(self, query: str, k: int) -> List[Dict[str, Any]]:
        results = await asyncio.to_thread(
            self.vector_store.similarity_search_with_score, query, k
        )

        return [
            {
                "page_content": doc.page_content,
                "metadata": doc.metadata,
                "score": score,
                "source": "dense",
            }
            for doc, score in results
        ]
