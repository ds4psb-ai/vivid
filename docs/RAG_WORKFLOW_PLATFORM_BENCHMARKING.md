# RAG 기반 워크플로우 플랫폼 벤치마킹 리포트

## Executive Summary

2025년 트렌드는 **"No-Code + Pro-Code 하이브리드"**입니다. 주요 플랫폼들의 핵심 장점을 분석하고, Vivid/Crebit 플랫폼에 적용 가능한 벤치마킹 포인트를 제시합니다.

---

## 1. 플랫폼별 심층 분석

### Inkeep - "Code Sync의 정석"

**Reference:** https://inkeep.com/blog/AI-Customer-Experience

| 강점 | 설명 |
|------|------|
| **Bi-directional Code Sync** | No-Code UI 변경 ↔ TypeScript SDK 자동 동기화 |
| **24시간 배포** | 콘텐츠 → AI 어시스턴트 24시간 내 배포 |
| **Hybrid Retrieval** | Vector + Keyword + Reranking 조합 |
| **MCP Server** | Claude 등 외부 에이전트에서 RAG API 직접 호출 |
| **Ticket-to-FAQ** | 해결된 티켓에서 자동 FAQ 생성 |

**벤치마킹 포인트:**
- Code Sync: 에이전트 워크플로우 변경 시 코드 자동 생성/동기화
- MCP Server: Vivid Dimension을 MCP로 노출 → 외부 에이전트 연동
- Content Intelligence: 사용자 질의 분석 → 콘텐츠 갭 자동 리포팅

---

### Flowise - "모듈러 아키텍처의 모범"

**Reference:** https://github.com/FlowiseAI/Flowise | https://sider.ai/blog/ai-tools/flowise-ai-review-is-this-the-best-open-source-llm-builder-in-2025

| 강점 | 설명 |
|------|------|
| **3가지 빌더** | Chatflow (단일 에이전트), Agentflow (멀티 에이전트), Assistant |
| **100+ 통합** | LLM, Embeddings, Vector DB 즉시 연결 |
| **Plugin Architecture** | 각 노드가 INode 인터페이스 구현 → 확장 용이 |
| **1000 동시 연결** | 인스턴스당 150ms 오버헤드 |

**벤치마킹 포인트:**
- 노드 플러그인 시스템: 새 차원(Dimension) 추가 시 플러그인 형태로 등록
- Agentflow 개념: 멀티 에이전트 오케스트레이션 UI
- Human-in-the-Loop: 실행 중 사람 개입 포인트 시각화

---

### Dify - "올인원 LLMOps"

**Reference:** https://github.com/langgenius/dify | https://dify.ai/blog/introducing-knowledge-pipeline

| 강점 | 설명 |
|------|------|
| **Knowledge Pipeline** | RAG ETL을 시각적 파이프라인으로 구성 |
| **Logic Control** | if/else, 분기, for 반복, 에러 핸들링 |
| **Backend-as-a-Service** | 모든 워크플로우가 자동으로 API 노출 |
| **Observability** | 토큰 사용량, 지연시간, 버전 관리 대시보드 |

**벤치마킹 포인트:**
- Knowledge Pipeline: 거장 스타일 RAG를 시각적 ETL로 관리
- BaaS 모델: Train 워크플로우 → 자동 API 엔드포인트 생성
- 버전 관리: 워크플로우/프롬프트 히스토리 + 롤백

---

### LangFlow - "RAG 특화 최강"

**Reference:** https://www.zenml.io/blog/langflow-alternatives

| 강점 | 설명 |
|------|------|
| **Astra DB / MongoDB 네이티브** | 벡터 DB 통합 최고 수준 |
| **Visual Debugging** | 문서 처리 병목 시각화 |
| **Datastax 인수** | 기업 안정성 확보 (42K GitHub Stars) |
| **23% 빠른 PDF 처리** | 100+ 페이지 PDF에서 Flowise 대비 우위 |

**벤치마킹 포인트:**
- Visual Debugging: 차원 실행 중 병목/실패 포인트 실시간 시각화
- 문서 처리 성능: 영상 스크립트/시나리오 대용량 처리 최적화

---

### n8n - "422+ 앱 통합의 왕"

**Reference:** https://n8n.io/rag/ | https://blog.n8n.io/ai-agentic-workflows/

| 강점 | 설명 |
|------|------|
| **422+ 앱 연동** | Slack, Teams, Notion, Google Drive 등 |
| **AI Evaluations** | RAG 성능 테스트 데이터셋 자동 실행 |
| **Local LLM 지원** | Ollama 등 프라이버시 중심 배포 |
| **Output Parser** | LLM 응답 구조 강제화 |

**벤치마킹 포인트:**
- 광범위 통합: YouTube, Vimeo, Frame.io 등 영상 플랫폼 연동
- AI Evaluations: 차원별 품질 테스트 자동화 파이프라인
- 행동 경계 설정: LLM 응답이 시스템에 도달하기 전 필터링

---

### RAGFlow - "Deep Document Understanding"

**Reference:** https://github.com/infiniflow/ragflow

| 강점 | 설명 |
|------|------|
| **DeepDoc Parser** | 최고 수준 PDF OCR |
| **구조 인식 청킹** | 표, 차트, 캡션, 각주 별도 인식 |
| **RAPTOR** | 재귀적 요약 → 계층적 트리 구조 |
| **GraphRAG** | 지식 그래프 추출 → 멀티홉 Q&A |
| **청킹 시각화** | 사람이 개입하여 청킹 조정 가능 |

**벤치마킹 포인트:**
- 구조 인식 청킹: 영상 대본의 씬/컷/대사 구조 자동 인식
- GraphRAG: 거장 스타일 간 관계 그래프 → "봉준호 + 웨스 앤더슨" 쿼리 지원
- 청킹 시각화: 사용자가 RAG 소스 직접 검토/수정

---

### Stack AI - "엔터프라이즈 표준"

**Reference:** https://www.stack-ai.com/

| 강점 | 설명 |
|------|------|
| **SOC2 / HIPAA / GDPR** | 엔터프라이즈 컴플라이언스 완비 |
| **워크플로우 스태킹** | 워크플로우를 다른 워크플로우에 중첩 |
| **출시 전 승인** | 관리자가 워크플로우 배포 전 검토 |
| **HP, IBM, MIT 사용** | 대기업 레퍼런스 |

**벤치마킹 포인트:**
- 워크플로우 스태킹: 재사용 가능한 차원 조합 템플릿
- 배포 승인 프로세스: 팀 협업 시 품질 게이트

---

### Vellum - "Bi-directional Sync 선구자"

**Reference:** https://www.vellum.ai/products/workflows-sdk

| 강점 | 설명 |
|------|------|
| **Push/Pull 동기화** | 코드 → UI, UI → 코드 양방향 |
| **실시간 가시성** | 코드 변경이 UI에 즉시 반영 |
| **AI-powered Features** | SDK와 비주얼 빌더 간 협업 최적화 |

**벤치마킹 포인트:**
- Git-like 워크플로우: 차원 조합을 브랜치처럼 관리
- 실시간 미리보기: 코드 수정 시 Train UI 즉시 업데이트

---

## 2. Vivid Train 벤치마킹 우선순위

### Tier 1: 즉시 적용 가능 (1-2주)

| 기능 | 참고 플랫폼 | 구현 방향 |
|------|------------|----------|
| **청킹 시각화** | RAGFlow | 거장 스타일 RAG 소스를 사용자가 검토/편집 |
| **실행 디버깅 UI** | LangFlow | 차원 실행 중 병목/실패 포인트 표시 |
| **Output Parser** | n8n | 각 차원 출력 JSON 스키마 강제화 |

### Tier 2: 중기 로드맵 (1-2개월)

| 기능 | 참고 플랫폼 | 구현 방향 |
|------|------------|----------|
| **Knowledge Pipeline UI** | Dify | RAG ETL(거장 스타일)을 시각적 파이프라인으로 |
| **워크플로우 스태킹** | Stack AI | 자주 쓰는 차원 조합을 템플릿화 |
| **AI Evaluations** | n8n | 차원별 품질 테스트 자동화 |
| **MCP Server** | Inkeep | Vivid Dimension을 MCP로 노출 |

### Tier 3: 장기 비전 (3개월+)

| 기능 | 참고 플랫폼 | 구현 방향 |
|------|------------|----------|
| **Bi-directional Code Sync** | Inkeep/Vellum | No-Code 변경 ↔ Python SDK 자동 동기화 |
| **GraphRAG** | RAGFlow | 거장 스타일 관계 그래프 쿼리 |
| **멀티 에이전트 Agentflow** | Flowise | 병렬 차원 실행 시각적 오케스트레이션 |

---

## 3. 핵심 차별화 전략

### Vivid Train의 현재 강점 (유지/강화)

- **Domain-Specific RAG**: 영상 제작 특화 (거장 스타일, 품질 기준)
- **Agentic 자동화**: compose_smart_workflow (지능형 파이프라이닝)
- **TieredContext**: Plan-Act-Reflect 프레임워크
- **QC 차원**: 내장 품질 게이트

### 벤치마킹으로 추가해야 할 것

- **시각적 투명성**: "에이전트가 왜 이렇게 했는지" 디버깅 UI
- **하이브리드 접근**: 파워 유저용 코드 레벨 커스터마이징
- **통합 생태계**: 영상 플랫폼(YouTube, Vimeo) 네이티브 연동
- **청킹 제어권**: RAG 소스 사용자 편집 기능

---

## 4. 결론

| 질문 | 답변 |
|------|------|
| **가장 참고할 플랫폼?** | **Dify** (Knowledge Pipeline) + **Inkeep** (Code Sync) |
| **즉시 적용할 것?** | 청킹 시각화, 실행 디버깅 UI |
| **장기 목표?** | Bi-directional Code Sync로 "Pro-Code + No-Code" 하이브리드 완성 |
| **Vivid만의 강점?** | **영상 제작 도메인 특화** - 범용 플랫폼이 절대 따라올 수 없는 영역 |

> **핵심 메시지:** 범용 플랫폼들은 "모든 것을 할 수 있다"를 지향하지만, Vivid Train은 **"영상 제작을 가장 잘 한다"**를 지향해야 합니다. 벤치마킹은 UX/기술 패턴만 가져오고, **도메인 깊이**는 더 강화하세요.

---

## Sources

- [Inkeep AI Customer Experience](https://inkeep.com/blog/AI-Customer-Experience)
- [Flowise GitHub](https://github.com/FlowiseAI/Flowise)
- [Dify Knowledge Pipeline](https://dify.ai/blog/introducing-knowledge-pipeline)
- [LangFlow Alternatives](https://www.zenml.io/blog/langflow-alternatives)
- [n8n RAG](https://n8n.io/rag/)
- [RAGFlow GitHub](https://github.com/infiniflow/ragflow)
- [Stack AI](https://www.stack-ai.com/)
- [Vellum Workflows SDK](https://www.vellum.ai/products/workflows-sdk)
- [Dify GitHub](https://github.com/langgenius/dify)
- [Best No-Code AI Builders 2025](https://www.stack-ai.com/blog/best-no-code-ai-builders)

---

*Generated: 2025-01-07*
