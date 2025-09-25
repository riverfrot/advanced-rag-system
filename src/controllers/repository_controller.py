from fastmcp import mcp_tool
from services.repository_service import RepositoryClass

# 아래 내용은 추후 어느정도 프로젝트 다듬은뒤에 dtoclass로 변경 필요
from domain.entities.repository import RepositoryMetadata


class RepositoryController:
    """Repostiory 관련 MCP 도구 호출 endpoint

    추후 authorization 추가 필요 외부 인가 되지 않은 사용자가 점근 못하게 나머지 단순 조회가 아닌
        llm call또는 내부 private정보가 노출 되는 내용은 authorization 구성필요"""

    @mcp_tool()
    async def crawl_repository(
        self,
        repositoryMetadata: RepositoryMetadata,  # chroma, 추후 pinecone, faiss 추가옞정
    ) -> dict:
        """외부 Repository를 크롤링하여 벡터 DB에 저장

        음.. 추후 내부 private repo도 접근 가능하게끔 access_token 받는 부분도 추가 필요
        """
        return RepositoryClass().create_crawl_repository(repositoryMetadata)

    @mcp_tool()
    async def analyze_repository_structure(
        self, repositoryMetadata: RepositoryMetadata
    ) -> dict:
        """Repository 구조 분석 및 메타데이터 추출 함수"""
        return RepositoryClass().update_repository_structure(repositoryMetadata)
