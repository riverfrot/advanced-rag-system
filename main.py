"""
RAG System Main MCP 서버
통합 MCP 서버로 추후 멀티 에이전트에게 도구를 제공하는 역할로써 사용 예정
"""

from fastmcp import FastMCP


def create_mcp_server() -> FastMCP:
    """RAG MCP 서버 생성 및 구성"""

    # MCP 서버 생성
    server = FastMCP("advanced-rag-server")

    return server


if __name__ == "__main__":
    server = create_mcp_server()
    server.run()
