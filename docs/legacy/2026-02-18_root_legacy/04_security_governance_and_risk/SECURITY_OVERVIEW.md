# Security Overview

<details open>
<summary>한국어</summary>

버전: 0.1
최종 업데이트: 2026-01-15
상태: Draft
담당: Security Lead (TBD)

## 1. 목적
Vivid의 보안 태세, 목표, 공통 가정을 정의한다. 이 문서는 상위 보안 요약이며 상세 정책과 통제 기준을 참조한다.

## 2. 범위
포함:
- Backend API 서비스, 잡 러너, 내부 S2S 엔드포인트
- Frontend 웹 앱과 클라이언트-API 상호작용
- RAG 파이프라인(인제스트, 인덱싱, 검색, 생성) 및 증거 출력
- MCP 통합과 툴 실행
- 데이터 저장소(Postgres, Redis, Qdrant, 오브젝트 스토리지)
- 시크릿, 자격 증명, CI/CD 파이프라인

제외(벤더 또는 고객 계약에서 정의):
- 사용자 디바이스 보안
- 제3자 SaaS 보안 통제
- Vivid가 운영하지 않는 파트너 네트워크

## 3. 보안 원칙
- Sealed capsule 설계: 내부 체인과 프롬프트는 노출하지 않고 승인된 입력/출력과 파라미터만 제공한다.
- Run-token 게이팅: 실행은 크레딧 예약과 검증이 포함된 run-token을 요구한다.
- MTLS 활성화 시 내부 S2S 엔드포인트는 mTLS를 강제한다.
- Evidence-first: 가능한 경우 증거 참조를 출력에 포함한다.
- 사용자, 서비스, 데이터 계층 전반에서 최소 권한과 제로 트러스트를 적용한다.
- 인증, 크레딧, 정책 체크는 Fail closed로 처리한다.
- 설정과 배포에서 보안 기본값을 우선한다.

## 4. 시스템 컨텍스트
상위 데이터 흐름과 신뢰 경계:

```
[User] -> [Frontend] -> [Public API]
                         | \
                         |  +--> [RAG Pipeline] -> [Vector DB]
                         |  +--> [MCP Tools]
                         +--> [Internal S2S] (mTLS)

Trust boundaries:
- Public edge boundary: Internet to Public API
- Internal boundary: Public API to Internal S2S
- Data boundary: Services to data stores
- Provider boundary: Services to external model vendors
```

## 5. 자산 인벤토리(요약)
- 사용자 데이터: 계정 식별자, 환경설정, 입력/출력
- 프롬프트/컨텍스트 데이터: RAG 쿼리, 검색 컨텍스트, 툴 입력
- 증거 데이터: 참조, 인용, 라인리지 메타데이터
- 시크릿: API 키, 서명 키, DB 자격 증명
- 운영 데이터: 로그, 메트릭, 트레이스, 감사 이벤트

## 6. 신뢰 경계 및 접근 경로
- Public API: 인증, 레이트 리밋, 명시적 입력 검증
- Internal S2S: mTLS + 서비스 아이덴티티, 외부 공개 금지
- 데이터 저장소: 프라이빗 네트워크, 최소 권한 자격 증명
- 외부 벤더: 명시적 허용 목록과 이그레스 통제

## 7. 위협 모델 요약(STRIDE)
| 위협 | 예시 | 주요 통제 |
| --- | --- | --- |
| Spoofing | 토큰 탈취 또는 신원 위조 | 강력한 인증, 토큰 바인딩, mTLS |
| Tampering | 요청 페이로드 변조 | 입력 검증, 무결성 체크 |
| Repudiation | 민감 행위 추적 불가 | 감사 로그, 요청 ID |
| Information disclosure | 프롬프트/데이터 유출 | Sealed capsule, 레드랙션, 접근 통제 |
| Denial of service | API 폭주 | 레이트 리밋, 서킷 브레이커 |
| Elevation of privilege | 권한 상승 | RBAC, 최소 권한, 리뷰 |

## 8. 보안 목표
- 기밀성: 사용자 입력, 노트북, 프롬프트, 증거 보호
- 무결성: 데이터와 출력의 무단 변경 방지
- 가용성: 안정적 서비스 운영과 우아한 실패
- 안전/신뢰: 오용, 환각 증폭, 툴 남용 방지

## 9. 컴플라이언스 및 참고 문서
내부 참조:
- 15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md
- docs/RAG_ARCHITECTURE.md
- docs/AI_RAG_SECURITY_POLICY.md
- docs/SECURITY_CONTROLS_BASELINE.md

외부 참조(베이스라인):
- NIST SP 800-218 (SSDF)
- NIST SP 800-207 (Zero Trust)
- NIST AI RMF 1.0
- OWASP API Security Top 10 (2023)
- OWASP LLM Top 10
- CIS Controls v8
- ISO/IEC 27001:2022 and 27701

## 10. 예외
- 예외는 기간 제한과 위험 수용 문서가 필요하다.
- 예외 승인자는 Security Lead와 Product Owner이다.

## 11. 검토 주기
- 분기별 또는 중대한 아키텍처 변경 후 검토한다.

</details>

<details>
<summary>English</summary>

Version: 0.1
Last Updated: 2026-01-15
Status: Draft
Owner: Security Lead (TBD)

## 1. Purpose
Define the security posture, goals, and shared assumptions for Vivid. This document is the top-level security summary and points to detailed policies and control baselines.

## 2. Scope
In scope:
- Backend API services, job runners, and internal S2S endpoints
- Frontend web application and client-to-API interactions
- RAG pipelines (ingest, index, retrieve, generate) and evidence outputs
- MCP integrations and tool execution
- Data stores (Postgres, Redis, Qdrant, object storage)
- Secrets, credentials, and CI/CD pipelines

Out of scope (documented in vendor or customer contracts):
- End-user device security
- Third-party SaaS security controls
- Partner networks not operated by Vivid

## 3. Guiding Principles
- Sealed capsule design: internal chains and prompts are never exposed; only approved inputs/outputs and parameters are surfaced.
- Run-token gating: execution requires run-token with credit reservation and verification.
- mTLS for internal service-to-service endpoints when MTLS is enabled.
- Evidence-first outputs: responses must include evidence references when available.
- Least privilege and zero trust across users, services, and data layers.
- Fail closed for auth, credit, and policy checks.
- Security by default in configuration and deployment.

## 4. System Context
High-level data flow and trust boundaries:

```
[User] -> [Frontend] -> [Public API]
                         | \
                         |  +--> [RAG Pipeline] -> [Vector DB]
                         |  +--> [MCP Tools]
                         +--> [Internal S2S] (mTLS)

Trust boundaries:
- Public edge boundary: Internet to Public API
- Internal boundary: Public API to Internal S2S
- Data boundary: Services to data stores
- Provider boundary: Services to external model vendors
```

## 5. Asset Inventory (Summary)
- User data: account identifiers, preferences, content inputs, outputs
- Prompt and context data: RAG queries, retrieved context, tool inputs
- Evidence data: references, citations, lineage metadata
- Secrets: API keys, signing keys, database credentials
- Operational data: logs, metrics, traces, audit events

## 6. Trust Boundaries and Access Paths
- Public API: authenticated, rate-limited, explicit input validation
- Internal S2S: mTLS + service identity, no public access
- Data stores: private networks, strict credentials, least privilege
- External providers: explicit allowlist and egress controls

## 7. Threat Model Summary (STRIDE)
| Threat | Example | Primary Controls |
| --- | --- | --- |
| Spoofing | Token theft or forged identity | Strong auth, token binding, mTLS |
| Tampering | Request payload manipulation | Input validation, integrity checks |
| Repudiation | Untracked sensitive actions | Audit logs, request IDs |
| Information disclosure | Prompt/data leakage | Sealed capsules, redaction, access controls |
| Denial of service | API flooding | Rate limiting, circuit breakers |
| Elevation of privilege | Unauthorized admin actions | RBAC, least privilege, reviews |

## 8. Security Objectives
- Confidentiality: protect user inputs, notebooks, prompts, and evidence.
- Integrity: prevent unauthorized modification of data and outputs.
- Availability: ensure resilient service operation and graceful degradation.
- Safety and trust: prevent misuse, hallucination amplification, and tool abuse.

## 9. Compliance and References
Internal references:
- 15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md
- docs/RAG_ARCHITECTURE.md
- docs/AI_RAG_SECURITY_POLICY.md
- docs/SECURITY_CONTROLS_BASELINE.md

External references (baseline):
- NIST SP 800-218 (SSDF)
- NIST SP 800-207 (Zero Trust)
- NIST AI RMF 1.0
- OWASP API Security Top 10 (2023)
- OWASP LLM Top 10
- CIS Controls v8
- ISO/IEC 27001:2022 and 27701

## 10. Exceptions
- Exceptions must be time-bound and documented with risk acceptance.
- All exceptions require approval from Security Lead and Product Owner.

## 11. Review Cadence
- Quarterly review or after material architecture changes.

</details>
