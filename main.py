#!/usr/bin/env python3
"""
RAG System Main CLI Interface
통합 CLI 인터페이스로 crawling과 query 기능을 제공
추후 MCP 서버로 전환하여 멀티에이전트에서 tool로써 사용 가능하게끔 전환 예정
"""

import os
import sys
import argparse
from pathlib import Path
from RagPipeline.crawl import RepositoryCrawler
from RagPipeline.query import IssueQuerySystem


def main():
    parser = argparse.ArgumentParser(
        description="RAG System for Issue Resolution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
  예시:
  # Repository Crawling
  python main.py crawling --repo https://github.com/riverfrot/sample-spring
  
  # Issue resolution
  python main.py query --issue "ISSUE-2: 데이터 영속성 문제"
  
  # Custom persist directory
  python main.py crawling --repo https://github.com/riverfrot/sample-spring --persist-dir ./custom_db
  python main.py query --issue "Spring Boot database issue" --persist-dir ./custom_db
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # crawling 서브커맨드
    crawling_parser = subparsers.add_parser(
        "crawling", help="crawling repository into vector database"
    )
    crawling_parser.add_argument(
        "--repo",
        required=True,
        help="Repository URL to crawling (e.g., https://github.com/riverfrot/sample-spring)",
    )
    crawling_parser.add_argument(
        "--persist-dir",
        default="./chroma_db",
        help="ChromaDB persist directory (default: ./chroma_db)",
    )

    # query 서브커맨드
    query_parser = subparsers.add_parser(
        "query", help="Query the system to resolve issues"
    )
    query_parser.add_argument(
        "--issue",
        required=True,
        help='Issue description (e.g., "ISSUE-2: database persistence problem")',
    )
    query_parser.add_argument(
        "--persist-dir",
        default="./chroma_db",
        help="ChromaDB persist directory (default: ./chroma_db)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 환경 변수 설정
    os.environ["CHROMA_PERSIST_DIRECTORY"] = args.persist_dir

    if args.command == "crawling":
        print("Start Repository Crawling...")

        try:
            crawler = RepositoryCrawler()
            crawler.crawl_repository(args.repo)

            print("Crawling completed successfully!")
            print(f"Vector database saved to: {args.persist_dir}")

        except Exception as e:
            print(f"Crawling failed: {e}")
            sys.exit(1)

    elif args.command == "query":
        print("Starting Issue Resolution...")

        try:
            query_system = IssueQuerySystem()
            result = query_system.resolve_issue(args.issue)
            
            # 리포트 생성 및 저장
            query_system.print_resolution_report(result)
            print(f"Issue resolution completed successfully!")

        except Exception as e:
            print(f"Query failed: {e}")
            if "vector store" in str(e).lower():
                print("Make sure you've run Crawling first:")
                print("python main.py crawling --repo <repository_url>")
            sys.exit(1)


if __name__ == "__main__":
    main()
