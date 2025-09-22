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

import openai
from langchain_community.vectorstores import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from tavily import TavilyClient

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
            model="text-embedding-3-large", api_key=self.openai_api_key
        )

        # Tavily 클라이언트 초기화
        self.tavily_client = TavilyClient(api_key=self.tavily_api_key)

        # ChromaDB 설정
        self.chroma_persist_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
        self.vectorstore = None


def main():
    return


if __name__ == "__main__":
    main()
