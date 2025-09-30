"""
RAG Query Service
벡터 데이터베이스에서 관련 문서 검색 및 LLM 응답 생성
"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv

from langchain_community.vectorstores import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

load_dotenv()

# LangSmith 추적 활성화
os.environ["LANGCHAIN_TRACING_V2"] = "true"
if os.getenv("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "rag-system")


class RetrievalService:
    """RAG 검색 및 응답 생성 서비스"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # OpenAI 임베딩 모델
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small", 
            api_key=self.openai_api_key
        )
        
        # ChatGPT 모델
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            temperature=0.1,
            api_key=self.openai_api_key
        )
        
        # 기본 프롬프트 템플릿
        self.prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""다음 컨텍스트를 바탕으로 질문에 답해주세요.
            
컨텍스트:
{context}

질문: {question}

답변: 코드베이스의 컨텍스트를 바탕으로 구체적이고 실용적인 답변을 제공해주세요.
코드 예시나 파일 위치가 있다면 함께 제공해주세요."""
        )
    
    def load_vector_store(self, persist_dir: str = "./chroma_db") -> Chroma:
        """벡터 스토어 로드"""
        if not os.path.exists(persist_dir):
            raise ValueError(f"Vector store directory not found: {persist_dir}")
        
        vectorstore = Chroma(
            persist_directory=persist_dir,
            embedding_function=self.embeddings
        )
        
        return vectorstore
    
    async def query_repository(
        self, 
        query: str, 
        persist_dir: str = "./chroma_db",
        k: int = 5
    ) -> Dict[str, Any]:
        """Repository에 대한 질의 처리"""
        try:
            # 벡터 스토어 로드
            vectorstore = self.load_vector_store(persist_dir)
            
            # 유사 문서 검색
            retriever = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": k}
            )
            
            # QA 체인 생성
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=retriever,
                chain_type_kwargs={"prompt": self.prompt_template},
                return_source_documents=True
            )
            
            # 질의 실행
            result = await qa_chain.ainvoke({"query": query})
            
            # 소스 문서 정보 추출
            source_docs = []
            for doc in result.get("source_documents", []):
                source_docs.append({
                    "content": doc.page_content[:200] + "...",  # 처음 200자만
                    "source": doc.metadata.get("source", "Unknown"),
                    "file_name": doc.metadata.get("file_name", "Unknown"),
                    "chunk_index": doc.metadata.get("chunk_index", 0)
                })
            
            return {
                "query": query,
                "answer": result["result"],
                "source_documents": source_docs,
                "total_sources": len(source_docs)
            }
            
        except Exception as e:
            print(f"Query failed: {e}")
            raise
    
    async def search_similar_documents(
        self, 
        query: str, 
        persist_dir: str = "./chroma_db",
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """유사 문서 검색만 수행 (LLM 응답 없이)"""
        try:
            # 벡터 스토어 로드
            vectorstore = self.load_vector_store(persist_dir)
            
            # 유사성 검색
            docs = vectorstore.similarity_search(query, k=k)
            
            similar_docs = []
            for doc in docs:
                similar_docs.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": getattr(doc, 'similarity_score', None)
                })
            
            return similar_docs
            
        except Exception as e:
            print(f"Similarity search failed: {e}")
            raise
    
    async def get_repository_stats(self, persist_dir: str = "./chroma_db") -> Dict[str, Any]:
        """Repository 통계 정보 조회"""
        try:
            # 벡터 스토어 로드
            vectorstore = self.load_vector_store(persist_dir)
            
            # 전체 문서 수 조회
            collection = vectorstore._collection
            total_chunks = collection.count()
            
            # 기본 통계 반환
            return {
                "total_chunks": total_chunks,
                "persist_directory": persist_dir,
                "embedding_model": "text-embedding-3-small",
                "llm_model": "gpt-4o-mini"
            }
            
        except Exception as e:
            print(f"Stats retrieval failed: {e}")
            raise