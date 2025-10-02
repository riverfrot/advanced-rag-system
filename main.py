"""
RAG System Main MCP 서버
통합 MCP 서버로 추후 멀티 에이전트에게 도구를 제공하는 역할로써 사용 예정
"""

from fastmcp import FastMCP
from src.controllers.repository_controller import RepositoryController
from src.controllers.memory_controller import MemoryController
from src.controllers.ensemble_controller import EnsembleRetrievalController
from src.services.repository_service import RepositoryService
from src.services.memory_service import MemoryService
from src.services.ensemble_service import EnsembleRetrievalService
from src.infrastructure.retrievers.dense_retriever import DenseReriever
from src.infrastructure.retrievers.sparse_retriever import SparseRetriever
from src.infrastructure.memory.conversation_store import ConversationStore
from src.config import settings


# Global services and controllers initialization
config = settings.load_config()
repo_service = RepositoryService()

# 벡터스토어와 문서 로드 (없으면 None으로 초기화)
try:
    vector_store = repo_service.load_vector_store(config.persist_directory)
    documents = repo_service.load_crawled_documents(config.persist_directory)

    dense_retriever = DenseReriever(vector_store)
    sparse_retriever = SparseRetriever(documents) if documents else None

    print(f"벡터스토어 로드 완료: {len(documents)} 문서")
except Exception as e:
    #이부분 크롤링 없어도 뜨게끔 하고 
    #추후 멀티에이전트에서 먼저 백터스토어에 해당내용이 존재하는지 먼저 확인하는 로직이 개발필요할듯
    print(f"벡터스토어 로드 실패 크롤링이 필요: {e}")
    vector_store = None
    dense_retriever = None
    sparse_retriever = None
    documents = []

# Services 초기화
ensemble_service = EnsembleRetrievalService(dense_retriever, sparse_retriever)
conversation_store = ConversationStore(config.memory_db_path)
memory_service = MemoryService(conversation_store)

# Controllers 초기화
repo_controller = RepositoryController(repo_service)
memory_controller = MemoryController(memory_service)
ensemble_controller = EnsembleRetrievalController(ensemble_service)

# MCP 서버 생성
mcp = FastMCP(name="advanced-rag-server")


# Repository Tools
@mcp.tool
def crawl_repository(repository_url: str, persist_dir: str = None) -> dict:
    """GitHub 레포지토리를 크롤링하여 벡터스토어에 저장"""
    return repo_controller.crawl_repository(repository_url, persist_dir)


@mcp.tool
def analyze_repository_structure(repository_url: str) -> dict:
    """레포지토리 구조를 분석"""
    return repo_controller.analyze_repository_structure(repository_url)


@mcp.tool
def search_code(query: str, query_type: str = "general", top_k: int = 5) -> dict:
    """코드 검색 (dense + sparse 앙상블)"""
    return ensemble_controller.search(query, query_type, top_k)


@mcp.tool
def search_with_weights(
    query: str, dense_weight: float = 0.6, sparse_weight: float = 0.4, top_k: int = 5
) -> dict:
    """가중치를 지정한 앙상블 검색"""
    return ensemble_controller.search_with_weights(
        query, dense_weight, sparse_weight, top_k
    )


@mcp.tool
def save_conversation(
    user_id: str, conversation_id: str, message: str, response: str
) -> dict:
    """대화 내용 저장"""
    return memory_controller.save_conversation(
        user_id, conversation_id, message, response
    )


@mcp.tool
def get_conversation_history(user_id: str, conversation_id: str) -> dict:
    """대화 히스토리 조회"""
    return memory_controller.get_conversation_history(user_id, conversation_id)


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8080,
        path="/",
        log_level="debug",
    )
