# RAG System for Issue Resolution 
Git Repo 를 기준으로 RAG 시스템을 구축 추후 멀티 agent 시스템에서 MCP서버로 이용할 예정
이 프로젝트는 특정 레포지토리에서 이슈를 자동으로 해결하는 RAG (Retrieval-Augmented Generation) 시스템입니다.
현재는 https://github.com/riverfrot/sample-spring 기준이나 추후 변경 예정 입니다.

## 시스템 구조

```
Repository → Ingestion → Chunking → Embedding → VectorStore
                                                      ↓
User Query → Vector Search → Context Retrieval → LLM → Response
        ↓
 External Research (Tavily API)
```

## 설치 및 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정
`.env.sample` 파일을  기준으로  `.env` 파일에 필요한 API 키들이 설정되어 있는지 확인:

```env
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
CHROMA_PERSIST_DIRECTORY=./chroma_db
```

### 3. 실행 명령어 예시 
예시:
  # Repository Crawling
  python main.py crawling --repo https://github.com/riverfrot/sample-spring
  
  # Issue resolution
  python main.py query --issue "ISSUE-2: 데이터 영속성 문제"
  
  # Custom persist directory
  python main.py crawling --repo https://github.com/riverfrot/sample-spring --persist-dir ./custom_db
  python main.py query --issue "ISSUE-2: 데이터 영속성 문제" --persist-dir ./custom_db


### 4. 서버 구동 예시
예시:
  # MCP서버 8080포트로 구동
  python main.py

**TODO:**
- [ ] Vector Database 성능 최적화 (Pinecone/Chroma) #멀티에이전트 작업 후 추가 진행 예정 production에 배포 진행시
- [v] Memory 관리 및 conversation chain 고도화 #작업 완료
- [ ] API 응답 시간 모니터링 추가 #멀티에이전트 작업 후 추가 진행 예정 production에 배포 진행시
- [v] FastMCP를 사용하여 MCP 서버로 전환 예정 #작업 완료
- [ ] 멀티 에이전트 서비스들을 통해 해당 MCP서버를 tool로서 사용 가능하게끔 고도화 # 별도 repository에서 진행 예정

## 라이선스

MIT License
