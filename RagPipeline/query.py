#!/usr/bin/env python3
"""
Issue Query & Resolution Pipeline
Issue 번호 입력 → VectorStore 검색 → Tavily API 리서치 → OpenAI ChatCompletion으로 해결책 생성
"""

import os
import sys
import argparse
from typing import List, Dict, Any
from dotenv import load_dotenv

from langchain_community.vectorstores import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from tavily import TavilyClient
import os
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

# LangSmith 추적 활성화
os.environ["LANGCHAIN_TRACING_V2"] = "true"
if os.getenv("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "rag-system")


class IssueQuerySystem:
    def __init__(self):
        # API 키 확인
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")

        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        if not self.tavily_api_key:
            raise ValueError("TAVILY_API_KEY not found in environment variables")

        # LangChain ChatOpenAI 초기화 (LangSmith 추적 가능)
        self.llm = ChatOpenAI(
            model="gpt-4", temperature=0.7, max_tokens=2000, api_key=self.openai_api_key
        )

        # Embeddings 초기화 (crawl.py와 동일한 모델 사용 해야함 아니면 정상적으로 검색이 되지않음
        # 추후 포스팅 예정)
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small", api_key=self.openai_api_key
        )

        # Tavily 클라이언트 초기화
        self.tavily_client = TavilyClient(api_key=self.tavily_api_key)

        # ChromaDB 설정
        self.chroma_persist_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
        self.vectorstore = None

    def load_vector_store(self) -> None:
        print(f"Get Vector stor: ${self.chroma_persist_dir}")

        try:
            self.vectorstore = Chroma(
                persist_directory=self.chroma_persist_dir,
                embedding_function=self.embeddings,
            )
        except Exception as e:
            print(f" Error vector load : {e}")
            raise

    def search_relevant_context(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """VectorStore에서 관련된 코드 검색"""
        print(f"quety: {query}")

        if not self.vectorstore:
            self.load_vector_store()

            # 기존 로드한 github 대상으로 유사도 검색 수행
            # 현재는 단일 프로젝트로만 가능하나 추후 github를 다중을로 구성하여 쿼리 가능하게끔 구조 개선 필요

            # 디폴트 값으로 5개의 유사도를 가진 내용만 가져오게끔 수정
            # 추후 dense retrival뿐만 아닌, sparse retrival이 가능하게끔 수정
            # 현재는 정확하게 일치되는 내용을 불러오는것에는 한계가 존재...
            result = self.vectorstore.similarity_search_with_score(query, k=k)

            context_docs = []
            for doc, score in result:
                context_docs.append(
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity_score": float(score),
                    }
                )
                print(
                    f"content : {doc.page_content}, metadata: {doc.metadata}, score : {float(score)}"
                )

            print(f"관련 검색 code data {len(context_docs)}")
            print(f"{context_docs}")

            return context_docs

    def tavily_resarch(self, query: str) -> str:
        """Tavily API를 활용한 웹검색"""
        try:
            # Tavily search
            response = self.tavily_client.search(
                query=query, search_depth="advanced", max_results=3, include_answer=True
            )

            print(f"response: {response}")

            research_content = ""

            if response.get("answer"):
                research_content += f"Research Summary: {response['answer']}\n\n"

            for i, result in enumerate(response.get("results", []), 1):
                research_content += f"Result {i}:\n"
                research_content += f"Title: {result.get('title', 'N/A')}\n"
                research_content += f"Content: {result.get('content', 'N/A')}\n"
                research_content += f"URL: {result.get('url', 'N/A')}\n\n"

            return research_content
        except Exception as e:
            print(f"research failed : {e}")
            return "api error"

    def generate_solution(
        self, issue_description: str, context_docs: List[Dict], resarch_content: str
    ) -> str:
        """OpenAI gpt-4 모델로 해결책생성

        기존에 tavily에서 외부 research 한것을 포함하여 이슈 해결 준비"""

        # 코드 질의
        code_context = ""
        for i, doc in enumerate(context_docs, 1):
            code_context += f"Code Snippet {i}:\n"
            code_context += f"File: {doc['metadata'].get('source','Unknown')}\n"
            code_context += (
                f"File Type: {doc['metadata'].get('file_type', 'Unknown')}\n"
            )
            code_context += f"Similarity Score: {doc['similarity_score']:.3f}\n"
            code_context += f"Content:\n{doc['content']}\n"
            code_context += "-" * 50 + "\n"

        # 프롬프트 구성
        system_prompt = """당신은 Spring Boot와 Kotlin에 전문성을 가진 시니어 개발자입니다. 
        주어진 이슈에 대해 코드 분석을 바탕으로 정확하고 실용적인 해결책을 제시해주세요.

        응답 형식:
        1. 문제 분석
        2. 원인 파악  
        3. 해결 방안
        4. 코드 예시 (필요한 경우)
        5. 추가 권장사항

        한국어로 답변해주세요."""

        # 유저 프롬프트
        user_prompt = f"""
        이슈 설명 : 
        {issue_description}
        관련 코드 컨텍스트 :
        {code_context}
        외부 리서치 결과 :
        {resarch_content}

        위 정보를 바탕으로 이슈에 대한 종합적인 해결책을 제시해주세요.
        """

        try:
            # LangChain을 활용하여 추후 LangSmith 추적에 사용
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            response = self.llm.invoke(messages)
            solution = response.content
            return solution
        except Exception as e:
            print(f" Error generate : {e}")
            return f"솔루션 생성중 에러 발생 : {e}"

    def resolve_issue(self, issue_description: str) -> Dict[str, Any]:
        """전체 이슈 해결 파이프라인"""
        print(f"Starting issue resolution for: {issue_description}")

        # 1. 관련 코드 컨텍스트 검색
        context_docs = self.search_relevant_context(issue_description)

        # 2. 외부 리서치 수행
        research_query = f"spring boot kotlin {issue_description} solution"
        research_content = self.tavily_resarch(research_query)

        # 3. 해결책 생성
        solution = self.generate_solution(
            issue_description, context_docs, research_content
        )

        # 결과 정리
        result = {
            "issue": issue_description,
            "relevant_files": [
                doc["metadata"].get("source", "Unknown") for doc in context_docs
            ],
            "context_docs": context_docs,
            "research_content": research_content,
            "solution": solution,
        }

        print("Issue resolution completed!")
        return result

    def print_resolution_report(self, result: Dict[str, Any]) -> None:
        """해결책 리포트를 report/result-query.md 파일에 저장"""

        # report 디렉토리 생성
        os.makedirs("report", exist_ok=True)

        # 리포트 내용 생성
        report_content = f"""# Issue Resolution Report

        **Generated on:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        ## 🎯 Issue
        {result['issue']}

        ## 📁 Relevant Files ({len(result['relevant_files'])})
        """

        for file in result["relevant_files"][:5]:  # 최대 5개만 표시
            report_content += f"- {file}\n"

        report_content += f"\n## 🤖 Solution\n{result['solution']}\n"

        if (
            result["research_content"]
            and "External research unavailable" not in result["research_content"]
        ):
            report_content += f"\n## 🌐 External Research\n"
            research_lines = result["research_content"].split("\n")[:10]  # 처음 10줄만
            report_content += "\n".join(research_lines)
            if len(result["research_content"].split("\n")) > 10:
                report_content += "\n\n... (more research results available)"

        # 파일에 저장
        with open("report/result-query.md", "w", encoding="utf-8") as f:
            f.write(report_content)

        print(f"✅ Resolution report saved to: report/result-query.md")


def main():
    parser = argparse.ArgumentParser(description="Issue Resolve Parser")
    parser.add_argument(
        "--issue", required=True, help="Issue description or issue number save to me"
    )
    parser.add_argument(
        "--persist-dir",
        help="if you need to cetain chromDB check this option",
        default="./chroma_db",
    )

    args = parser.parse_args()

    if args.persist_dir:
        os.environ["CHROMA_PERSIST_DIRECTORY"] = args.persist_dir

    try:
        # 쿼리 초기화
        query_system = IssueQuerySystem()

        # 이슈 해결
        result = query_system.resolve_issue(args.issue)

        # 리포트 생성 및 저장
        query_system.print_resolution_report(result)
        print(f"Issue resolution completed successfully!")

    except Exception as e:
        print(f"Query 실행중 실패 상세 이유: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
