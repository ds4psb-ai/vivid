# AI and RAG Security Policy

<details open>
<summary>한국어</summary>

버전: 0.1
최종 업데이트: 2026-01-15
상태: Draft
담당: AI Security Lead (TBD)

## 1. 목적
AI, RAG, 툴 실행 시스템의 보안 요구사항을 정의한다. 본 정책은 프롬프트 인젝션, 데이터 유출, 위험한 툴 사용을 방지하면서 evidence-first 출력을 유지한다.

## 2. 범위
- RAG 인제스트, 인덱싱, 검색, 생성
- 모델 선택과 프롬프트 패키징
- MCP 툴과 외부 모델 벤더
- 증거 참조와 출처

## 3. 위협 모델(예시)
- 프롬프트 인젝션과 데이터 유출
- 검색 데이터 중독 또는 악성 문서
- 툴 오용 또는 의도치 않은 부작용
- 증거 없는 출력 생성
- 모델 인버전 또는 데이터 유출

## 4. 단계별 보안 통제
### 4.1 인제스트
- 소스 허용 목록과 라이선스 검증
- PII 및 시크릿 탐지와 레드랙션
- 콘텐츠 정규화 및 메타데이터 태깅

### 4.2 인덱싱
- 인덱스 메타데이터에 소스/소유자/분류 포함
- 임베딩과 인덱스는 접근 통제 적용

### 4.3 검색
- ACL 및 분류 기반 필터링
- 리랭킹 시 안전 및 출처 신호 반영
- 저신뢰 결과는 명시적 폴백 규칙 적용

### 4.4 생성
- 프롬프트에 안전 지시와 구조화 출력 스키마 포함
- 출력 검증 및 스키마 강제
- 사실 주장에는 증거 참조 포함

### 4.5 후처리
- 출력과 로그에서 민감 정보 레드랙션
- 정책 위반 툴 요청은 차단 또는 무해화

## 5. Sealed Capsule 및 NotebookLM 규칙
- raw prompt, 체인, 노트북은 사용자에게 노출하지 않는다.
- 요약, 증거 참조, 승인된 파라미터만 제공한다.

## 6. 툴 안전 및 MCP
- 모든 툴은 입력/출력 스키마와 부작용을 명시한다.
- 툴 호출은 인증과 레이트 리밋을 적용한다.
- 고위험 툴은 사용자 확인 또는 관리자 승인이 필요하다.

## 7. 평가 및 레드팀
- 프롬프트 인젝션, 데이터 유출용 적대적 테스트 셋을 유지한다.
- RAG 파이프라인에 정기적인 레드팀을 수행한다.
- 안전 지표(거절률, 증거 커버리지, 환각률)를 추적한다.

## 8. 모니터링 및 사고 대응
- 검색 이상치와 툴 실행 이상을 경보한다.
- 정책 거부 및 증거 불일치 이벤트를 로깅한다.
- AI 관련 사고는 IR 런북으로 에스컬레이션한다.

## 9. 참고 문서
- docs/RAG_ARCHITECTURE.md
- docs/RAG_RELIABILITY.md
- 15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md
- OWASP LLM Top 10
- NIST AI RMF 1.0

</details>

<details>
<summary>English</summary>

Version: 0.1
Last Updated: 2026-01-15
Status: Draft
Owner: AI Security Lead (TBD)

## 1. Purpose
Define security requirements for AI, RAG, and tool execution systems. This policy prevents prompt injection, data leakage, and unsafe tool use while preserving evidence-first outputs.

## 2. Scope
- RAG ingestion, indexing, retrieval, and generation
- Model selection and prompt packaging
- MCP tools and external model providers
- Evidence references and provenance

## 3. Threat Model (Non-Exhaustive)
- Prompt injection and data exfiltration
- Retrieval poisoning or malicious documents
- Tool misuse or unintended side effects
- Output fabrication without evidence
- Model inversion or data leakage

## 4. Security Controls by Phase
### 4.1 Ingestion
- Source allowlist and license verification
- PII and secret detection and redaction
- Content normalization and metadata tagging

### 4.2 Indexing
- Index metadata includes source, owner, and classification
- Embeddings and indices are access-controlled

### 4.3 Retrieval
- Retrieval filtering by ACL and data classification
- Reranking includes safety and provenance signals
- Low-confidence retrievals require explicit fallback rules

### 4.4 Generation
- Prompts include safety instructions and structured output schemas
- Output validation and schema enforcement
- Evidence references are required when claiming facts

### 4.5 Post-Processing
- Redact sensitive content in outputs and logs
- Reject or neutralize tool requests that violate policy

## 5. Sealed Capsule and NotebookLM Rules
- Raw prompts, chains, and notebooks are never exposed to end users.
- Only derived summaries, evidence references, and approved parameters are surfaced.

## 6. Tool Safety and MCP
- Tools must declare input/output schemas and side effects.
- Tool calls are authenticated and rate-limited.
- High-risk tools require explicit user confirmation or admin approval.

## 7. Evaluation and Red Teaming
- Maintain adversarial test sets for prompt injection and data leakage.
- Run periodic red team exercises on RAG pipelines.
- Track safety metrics (refusal rate, evidence coverage, hallucination rate).

## 8. Monitoring and Incident Response
- Alert on anomaly spikes in retrieval or tool execution.
- Log all policy denials and evidence mismatches.
- Escalate AI incidents via the IR playbook.

## 9. References
- docs/RAG_ARCHITECTURE.md
- docs/RAG_RELIABILITY.md
- 15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md
- OWASP LLM Top 10
- NIST AI RMF 1.0

</details>
