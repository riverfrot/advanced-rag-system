#!/usr/bin/env python3
"""
Repository Crawling Pipeline
Repo 클론 후 코드 파일 수집 → 청킹 & 임베딩 → VectorStore 저장
"""

import os
import sys
import git
import argparse
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

import openai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings
import chromadb

load_dotenv()

# LangSmith 추적 활성화
os.environ["LANGCHAIN_TRACING_V2"] = "true"
if os.getenv("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "rag-system")


class RepositoryCrawler:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        # OpenAI text-embedding-3-small 사용
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small", api_key=self.openai_api_key
        )

        # 텍스트 스플리터 설정 (코드에 최적화)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""],
            length_function=len,
        )

        self.chroma_persist_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")


def main():
    return


if __name__ == "__main__":
    main()
