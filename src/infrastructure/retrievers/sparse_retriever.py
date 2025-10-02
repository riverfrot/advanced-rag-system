from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
import numpy as np
import re


class SparseRetriever:
    def __init__(self, documents: List[str]):
        self.tokenized_docs = [self._tokenize(doc) for doc in documents]
        self.bm25 = BM25Okapi(self.tokenized_docs)
        self.documents = documents

    async def search(self, query: str, k: int) -> List[Dict[str, Any]]:
        tokenized_query = self._tokenize(query)

        scores = self.bm25.get_scores(tokenized_query)
        top_k_indices = np.argsort(scores)[::-1][:k]

        results = []

        for idx in top_k_indices:
            if scores[idx] > 0:
                results.append(
                    {
                        "page_content": self.documents[idx],
                        "metadata": {"index": idx},
                        "score": scores[idx],
                        "source": "sparse",
                    }
                )
        return results

    def _tokenize(self, text: str) -> List[str]:
        # 코드 토큰 (함수명, 클래스명) 보존
        code_tokens = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", text)
        # 그외 토큰
        word_tokens = text.lower().split()
        return list(set(code_tokens + word_tokens))
