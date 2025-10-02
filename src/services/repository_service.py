"""
Repository Crawling Pipeline
Repo 클론 후 코드 파일 수집 → 청킹 & 임베딩 → VectorStore 저장
"""

import os
import git
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

from datetime import datetime
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings
from ..models.repository_model import RepositoryMetadata

load_dotenv()

# LangSmith 추적 활성화
os.environ["LANGCHAIN_TRACING_V2"] = "true"
if os.getenv("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "rag-system")


class RepositoryService:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        # OpenAI text-embedding-3-small 사용
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small", api_key=self.openai_api_key
        )

        # 텍스트 스플리터 설정 (코드에 최적화??)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""],
            length_function=len,
        )

        self.chroma_persist_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")

    def _clone_repository(
        self,
        repository_metadata: RepositoryMetadata,
        local_path: str = "./temp_repo",
    ) -> str:
        """GitHub 레포지토리 클론"""
        print(f"Cloning repository: {repository_metadata.url}")

        # 기존 디렉토리가 있다면 삭제
        if os.path.exists(local_path):
            shutil.rmtree(local_path)

        try:
            git.Repo.clone_from(repository_metadata.url, local_path)
            print(f"Repository cloned to: {local_path}")
            return local_path
        except Exception as e:
            print(f"Error cloning repository: {e}")
            raise

    def _extract_code_files(self, repo_path: str) -> List[str]:
        """코드 파일 추출 기능 함수

        현재는 (.kt, .java, .md 등) 파일들만 존재하지만 추후
        (.ts,.js,.py,package.json..) 등 범용적으로 사용 할 수 있게끔 구조 변경해야함...
        """
        print(f"Extracting code files from: {repo_path}")

        # 지원하는 파일 확장자
        code_extensions = {
            ".kt",
            ".java",
            ".py",
            ".js",
            ".ts",
            ".md",
            ".txt",
            ".yml",
            ".yaml",
            ".json",
            ".xml",
            ".gradle",
            ".properties",
        }

        files = []
        ignored_dirs = {
            ".git",
            "node_modules",
            "__pycache__",
            ".gradle",
            "build",
            "target",
        }

        for root, dirs, filenames in os.walk(repo_path):
            # 무시할 디렉토리 제외
            dirs[:] = [
                d for d in dirs if d not in ignored_dirs and not d.startswith(".")
            ]

            for filename in filenames:
                file_path = os.path.join(root, filename)
                file_ext = Path(filename).suffix.lower()

                if file_ext in code_extensions:
                    files.append(file_path)

        return files

    def _process_files_to_chunks(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """파일을 청크로 분할하고 메타데이터 추가"""
        print(f"Processing {len(file_paths)} files into chunks...")

        documents = []

        for file_path in file_paths:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                if not content.strip():
                    continue

                # 파일 내용을 청크로 분할
                chunks = self.text_splitter.split_text(content)
                for i, chunk in enumerate(chunks):
                    documents.append(
                        {
                            "content": chunk,
                            "metadata": {
                                "source": file_path,
                                "chunk_index": i,
                                "total_chunks": len(chunks),
                                "file_type": Path(file_path).suffix,
                                "file_name": Path(file_path).name,
                                "relative_path": str(
                                    Path(file_path).relative_to(
                                        Path(file_path).parts[0]
                                    )
                                ),
                            },
                        }
                    )

            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                continue

        print(f"{len(documents)} document chunks 생성완료")
        return documents

    def _create_vector_store(
        self, documents: List[Dict[str, Any]], persist_dir: str = None
    ) -> None:
        """ChromaDB 벡터스토어 생성 및 저장

        추후 ChromaDB 뿐만아니라 다른 vectorDB도 범용적으로 사용 가능하게끔 변경 필요
        Faiss, Pinecone 등...
        """
        print(f"Creating vector store with {len(documents)} chunks...")

        texts = [doc["content"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]

        # ChromaDB 벡터스토어 생성
        persist_directory = persist_dir or self.chroma_persist_dir
        vectorstore = Chroma.from_texts(
            texts=texts,
            metadatas=metadatas,
            embedding=self.embeddings,
            persist_directory=persist_directory,
        )

        # 벡터스토어 저장
        vectorstore.persist()
        print(f"Vector store created and saved to: {persist_directory}")

    def load_vector_store(self, persist_dir: str):
        """기존 벡터스토어 로드"""
        persist_directory = persist_dir or self.chroma_persist_dir

        vectorstore = Chroma(
            persist_directory=persist_directory, embedding_function=self.embeddings
        )

        return vectorstore

    def load_crawled_documents(self, persist_dir: str) -> List[Dict[str, Any]]:
        """크롤링된 문서 로드 (sparse retriever용)"""
        vectorstore = self.load_vector_store(persist_dir)

        # ChromaDB에서 모든 문서 가져오기
        collection = vectorstore._collection
        all_docs = collection.get()

        documents = []
        for i, (doc_id, content, metadata) in enumerate(
            zip(all_docs["ids"], all_docs["documents"], all_docs["metadatas"])
        ):
            documents.append(
                {"id": doc_id, "content": content, "metadata": metadata or {}}
            )

        return documents

    async def create_crawl_repository(
        self, repository_metadata: RepositoryMetadata
    ) -> dict:
        """전체 crawling 파이프라인 실행

        현재는 일단 main 브랜치 기준인데 다른 브랜치 타겟으로 하려면 어떻게해야하지,
        추후 main 브랜치가 업데이트되면..? 전체다 다시 crawl해야하나"""
        print("Starting repository crawling pipeline...")

        try:
            # 1. 레포지토리 클론
            repo_path = self._clone_repository(repository_metadata)

            # 2. 코드 파일 추출
            file_paths = self._extract_code_files(repo_path)

            # 3. 파일을 청크로 분할
            documents = self._process_files_to_chunks(file_paths)

            # 4. 벡터스토어 생성
            self._create_vector_store(documents, repository_metadata.persist_dir)

            # 5. 결과 반환
            repository_metadata.last_crawled = datetime.now()
            repository_metadata.file_count = len(file_paths)
            repository_metadata.chunk_count = len(documents)

            # 지원하는 언어 분석
            extensions = set(Path(f).suffix.lower() for f in file_paths)
            language_map = {
                ".py": "Python",
                ".js": "JavaScript",
                ".ts": "TypeScript",
                ".java": "Java",
                ".kt": "Kotlin",
                ".md": "Markdown",
            }
            repository_metadata.supported_languages = [
                language_map.get(ext, ext) for ext in extensions if ext in language_map
            ]

            return {
                "repository_url": repository_metadata.url,
                "file_count": repository_metadata.file_count,
                "chunk_count": repository_metadata.chunk_count,
                "supported_languages": repository_metadata.supported_languages,
                "persist_directory": repository_metadata.persist_dir,
                "crawled_at": repository_metadata.last_crawled.isoformat(),
            }

        except Exception as e:
            print(f"Crawling failed: {e}")
            raise

    async def analyze_repository_structure(
        self, repository_metadata: RepositoryMetadata
    ) -> dict:
        """기존 crawling한 repository 구조 분석 파이프라인 실행"""
        print("Starting repository structure analysis...")

        try:
            # 1. 레포지토리 클론
            repo_path = self._clone_repository(repository_metadata)

            # 2. 코드 파일 추출 및 구조 분석
            file_paths = self._extract_code_files(repo_path)

            # 3. 디렉토리 구조 분석
            directory_structure = self._analyze_directory_structure(repo_path)

            # 4. 파일 유형별 통계
            file_stats = self._analyze_file_statistics(file_paths)

            # 5. 의존성 분석 (package.json, requirements.txt 등)
            dependencies = self._analyze_dependencies(repo_path)

            return {
                "repository_url": repository_metadata.url,
                "total_files": len(file_paths),
                "directory_structure": directory_structure,
                "file_statistics": file_stats,
                "dependencies": dependencies,
                "analyzed_at": datetime.now().isoformat(),
            }

        except Exception as e:
            print(f"Structure analysis failed: {e}")
            raise

    def _analyze_directory_structure(self, repo_path: str) -> dict:
        """디렉토리 구조 분석"""
        structure = {}
        for root, dirs, files in os.walk(repo_path):
            # .git 등 숨김 디렉토리 제외
            dirs[:] = [d for d in dirs if not d.startswith(".")]

            rel_path = os.path.relpath(root, repo_path)
            if rel_path == ".":
                rel_path = "root"

            structure[rel_path] = {"directories": dirs, "files": len(files)}

        return structure

    def _analyze_file_statistics(self, file_paths: List[str]) -> dict:
        """파일 유형별 통계 분석"""
        stats = {}
        for file_path in file_paths:
            ext = Path(file_path).suffix.lower()
            if ext not in stats:
                stats[ext] = 0
            stats[ext] += 1

        return stats

    def _analyze_dependencies(self, repo_path: str) -> dict:
        """의존성 파일 분석"""
        dependencies = {}

        # package.json 분석
        package_json = os.path.join(repo_path, "package.json")
        if os.path.exists(package_json):
            try:
                with open(package_json, "r") as f:
                    data = json.load(f)
                    dependencies["npm"] = {
                        "dependencies": data.get("dependencies", {}),
                        "devDependencies": data.get("devDependencies", {}),
                    }
            except Exception as e:
                print(f"Error reading package.json: {e}")

        # requirements.txt 분석
        requirements_txt = os.path.join(repo_path, "requirements.txt")
        if os.path.exists(requirements_txt):
            try:
                with open(requirements_txt, "r") as f:
                    dependencies["python"] = [
                        line.strip()
                        for line in f
                        if line.strip() and not line.startswith("#")
                    ]
            except Exception as e:
                print(f"Error reading requirements.txt: {e}")

        # build.gradle 분석 (DSL)
        build_gradle = os.path.join(repo_path, "build.gradle")
        if os.path.exists(build_gradle):
            try:
                with open(build_gradle, "r") as f:
                    content = f.read()
                    dependencies["gradle"] = self._parse_gradle_dependencies(content)
            except Exception as e:
                print(f"Error reading build.gradle: {e}")

        # build.gradle.kts 분석 (Kotlin DSL)
        build_gradle_kts = os.path.join(repo_path, "build.gradle.kts")
        if os.path.exists(build_gradle_kts):
            try:
                with open(build_gradle_kts, "r") as f:
                    content = f.read()
                    dependencies["gradle_kts"] = self._parse_gradle_dependencies(
                        content
                    )
            except Exception as e:
                print(f"Error reading build.gradle.kts: {e}")

        # pom.xml 분석 (Maven)
        pom_xml = os.path.join(repo_path, "pom.xml")
        if os.path.exists(pom_xml):
            try:
                import xml.etree.ElementTree as ET

                tree = ET.parse(pom_xml)
                root = tree.getroot()
                dependencies["maven"] = self._parse_maven_dependencies(root)
            except Exception as e:
                print(f"Error reading pom.xml: {e}")

        return dependencies

    def _parse_gradle_dependencies(self, content: str) -> dict:
        """Gradle 의존성 파싱"""
        import re

        dependencies = {
            "implementation": [],
            "testImplementation": [],
            "api": [],
            "compileOnly": [],
        }

        # 의존성 패턴 매칭
        patterns = {
            "implementation": r"implementation\s+['\"]([^'\"]+)['\"]",
            "testImplementation": r"testImplementation\s+['\"]([^'\"]+)['\"]",
            "api": r"api\s+['\"]([^'\"]+)['\"]",
            "compileOnly": r"compileOnly\s+['\"]([^'\"]+)['\"]",
        }

        for dep_type, pattern in patterns.items():
            matches = re.findall(pattern, content)
            dependencies[dep_type] = matches

        return dependencies

    def _parse_maven_dependencies(self, root) -> dict:
        """Maven pom.xml 의존성 파싱"""
        dependencies = {"dependencies": [], "plugins": []}

        # XML 네임스페이스 처리
        namespace = {"maven": "http://maven.apache.org/POM/4.0.0"}

        # 의존성 추출
        deps = root.findall(".//maven:dependency", namespace)
        for dep in deps:
            group_id = dep.find("maven:groupId", namespace)
            artifact_id = dep.find("maven:artifactId", namespace)
            version = dep.find("maven:version", namespace)

            if group_id is not None and artifact_id is not None:
                dep_info = f"{group_id.text}:{artifact_id.text}"
                if version is not None:
                    dep_info += f":{version.text}"
                dependencies["dependencies"].append(dep_info)

        # 플러그인 추출
        plugins = root.findall(".//maven:plugin", namespace)
        for plugin in plugins:
            group_id = plugin.find("maven:groupId", namespace)
            artifact_id = plugin.find("maven:artifactId", namespace)
            version = plugin.find("maven:version", namespace)

            if group_id is not None and artifact_id is not None:
                plugin_info = f"{group_id.text}:{artifact_id.text}"
                if version is not None:
                    plugin_info += f":{version.text}"
                dependencies["plugins"].append(plugin_info)

        return dependencies
