from ..services.repository_service import RepositoryService

# 아래 내용은 추후 어느정도 프로젝트 다듬은뒤에 dtoclass로 변경 필요
from ..models.repository_model import RepositoryMetadata


class RepositoryController:
    """Repository 관련 MCP 도구 호출 endpoint

    추후 authorization 추가 필요 외부 인가 되지 않은 사용자가 접근 못하게 나머지 단순 조회가 아닌
        llm call또는 내부 private정보가 노출 되는 내용은 authorization 구성필요"""

    def __init__(self, repository_service: RepositoryService = None):
        self.repository_service = repository_service or RepositoryService()

    async def crawl_repository(
        self,
        repository_metadata: RepositoryMetadata,
    ) -> dict:
        """외부 Repository를 크롤링하여 벡터 DB에 저장

        추후 내부 private repo도 접근 가능하게끔 access_token 받는 부분도 추가 필요
        """
        try:
            result = await self.repository_service.create_crawl_repository(
                repository_metadata
            )
            return {
                "success": True,
                "message": "Repository crawled successfully",
                "data": result,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def analyze_repository_structure(
        self, repository_metadata: RepositoryMetadata
    ) -> dict:
        """Repository 구조 분석 및 메타데이터 추출 함수"""
        try:
            result = await self.repository_service.analyze_repository_structure(
                repository_metadata
            )
            return {
                "success": True,
                "message": "Repository structure analyzed successfully",
                "data": result,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
