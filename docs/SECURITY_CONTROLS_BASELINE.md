# Security Controls Baseline

<details open>
<summary>한국어</summary>

버전: 0.1
최종 업데이트: 2026-01-15
상태: Draft
담당: Security Lead (TBD)

## 1. 목적
모든 Vivid 시스템과 릴리스에 필요한 최소 보안 통제를 정의한다. 이 문서는 감사 및 변경 리뷰의 기준이다.

## 2. 범위
모든 운영 서비스, 파이프라인, 데이터 저장소, CI/CD 시스템. 개발 환경도 가능한 한 동일 기준을 따른다.

## 3. 최소 통제(MUST)
| ID | 통제 | 요구사항 | 증빙 |
| --- | --- | --- | --- |
| SEC-AC-01 | 인증 필요 | 상태 변경 엔드포인트는 인증이 필요하다. | API 인증 테스트 |
| SEC-AC-02 | 관리자 RBAC | 관리자 작업은 검증된 관리자 권한이 필요하다. | 접근 로그 |
| SEC-AC-03 | 내부 mTLS | 내부 S2S 엔드포인트는 mTLS를 요구한다. | mTLS 감사 로그 |
| SEC-SESS-01 | 서명 세션 | 세션 토큰은 매 요청마다 서명 검증을 수행한다. | 토큰 검증 테스트 |
| SEC-CR-01 | Run-token 게이팅 | 실행 엔드포인트는 크레딧 예약이 포함된 유효 run-token이 필요하다. | Run-token 테스트 |
| SEC-RATE-01 | 레이트 리밋 | 공용 엔드포인트에 레이트 리밋과 오용 방지를 적용한다. | 레이트 리밋 설정 |
| SEC-LOG-01 | 로그 마스킹 | PII와 시크릿을 로그/트레이스에서 마스킹한다. | 로그 샘플 |
| SEC-LOG-02 | 감사 추적 | 관리자 작업은 감사 이벤트를 남긴다. | 감사 로그 |
| SEC-DATA-01 | 전송 중 암호화 | 모든 클라이언트 및 S2S 연결에서 TLS 1.2+를 사용한다. | TLS 설정 |
| SEC-DATA-02 | 저장 시 암호화 | 데이터 저장소는 at-rest 암호화를 사용한다. | 스토리지 설정 |
| SEC-DATA-03 | 보존 정책 | 데이터 보존 및 삭제 정책을 TTL 또는 작업으로 강제한다. | 보존 작업 로그 |
| SEC-RAG-01 | 안전한 인제스트 | RAG 인제스트는 허용 목록과 PII 스크러빙을 적용한다. | 인제스트 테스트 |
| SEC-RAG-02 | 안전한 검색 | 검색은 ACL 필터와 증거 참조를 강제한다. | RAG 테스트 케이스 |
| SEC-SUP-01 | 공급망 보안 | 의존성은 고정하고 SBOM을 생성한다. | SBOM 산출물 |
| SEC-SDLC-01 | 보안 SDLC | 코드 리뷰, SAST, 시크릿 스캔을 필수화한다. | CI 리포트 |
| SEC-IR-01 | 사고 대응 | IR 런북은 최소 연 1회 테스트한다. | 모의훈련 리포트 |
| SEC-BCP-01 | 백업/DR | 백업을 검증하고 RTO/RPO를 정의한다. | DR 리포트 |

## 4. 통제 매핑(템플릿)
감사 목적의 외부 프레임워크 매핑.

| 통제 ID | NIST 800-53 | ISO 27001:2022 | CIS v8 | OWASP API 2023 | OWASP LLM Top 10 |
| --- | --- | --- | --- | --- | --- |
| SEC-AC-01 | TBD | TBD | TBD | TBD | TBD |
| SEC-AC-02 | TBD | TBD | TBD | TBD | TBD |
| SEC-AC-03 | TBD | TBD | TBD | TBD | TBD |
| SEC-SESS-01 | TBD | TBD | TBD | TBD | TBD |
| SEC-CR-01 | TBD | TBD | TBD | TBD | TBD |
| SEC-RATE-01 | TBD | TBD | TBD | TBD | TBD |
| SEC-LOG-01 | TBD | TBD | TBD | TBD | TBD |
| SEC-LOG-02 | TBD | TBD | TBD | TBD | TBD |
| SEC-DATA-01 | TBD | TBD | TBD | TBD | TBD |
| SEC-DATA-02 | TBD | TBD | TBD | TBD | TBD |
| SEC-DATA-03 | TBD | TBD | TBD | TBD | TBD |
| SEC-RAG-01 | TBD | TBD | TBD | TBD | TBD |
| SEC-RAG-02 | TBD | TBD | TBD | TBD | TBD |
| SEC-SUP-01 | TBD | TBD | TBD | TBD | TBD |
| SEC-SDLC-01 | TBD | TBD | TBD | TBD | TBD |
| SEC-IR-01 | TBD | TBD | TBD | TBD | TBD |
| SEC-BCP-01 | TBD | TBD | TBD | TBD | TBD |

## 5. 증빙 산출물
- 각 릴리스의 SBOM
- SLSA provenance attestation
- 취약점 스캔 리포트
- 모의침투 테스트 리포트(연 1회 또는 큰 변경 시)
- 접근/감사 로그 내보내기

## 6. 통제 상태 트래커(템플릿)
| 컴포넌트 | 통제 범위 | 상태 | 비고 |
| --- | --- | --- | --- |
| Backend API | SEC-AC, SEC-CR, SEC-LOG | Not Started | TBD |
| RAG Pipeline | SEC-RAG, SEC-DATA | Not Started | TBD |
| MCP Tools | SEC-AC, SEC-RATE | Not Started | TBD |
| Frontend | SEC-AC, SEC-SESS | Not Started | TBD |
| Infrastructure | SEC-DATA, SEC-BCP | Not Started | TBD |

## 7. 검토 주기
- 분기별 및 주요 릴리스 전 검토.

</details>

<details>
<summary>English</summary>

Version: 0.1
Last Updated: 2026-01-15
Status: Draft
Owner: Security Lead (TBD)

## 1. Purpose
Define the minimum security controls required for all Vivid systems and releases. This is the baseline for audits and change reviews.

## 2. Scope
All production services, pipelines, data stores, and CI/CD systems. Development environments should align when feasible.

## 3. Baseline Controls (MUST)
| ID | Control | Requirement | Evidence |
| --- | --- | --- | --- |
| SEC-AC-01 | Auth required | All state-changing endpoints require authenticated identity. | API auth tests |
| SEC-AC-02 | Admin RBAC | Admin actions require verified admin role. | Access logs |
| SEC-AC-03 | Internal mTLS | Internal S2S endpoints require mTLS when enabled. | mTLS audit logs |
| SEC-SESS-01 | Signed sessions | Session tokens are signed and validated on every request. | Token validation tests |
| SEC-CR-01 | Run-token gating | Execution endpoints require valid run-token with credit reservation. | Run-token tests |
| SEC-RATE-01 | Rate limits | Public endpoints have rate limits and abuse protections. | Rate limit config |
| SEC-LOG-01 | Redacted logs | PII and secrets are masked in logs and traces. | Log samples |
| SEC-LOG-02 | Audit trails | Admin actions emit audit events with actor and request ID. | Audit logs |
| SEC-DATA-01 | Encryption in transit | TLS 1.2+ on all client and S2S connections. | TLS config |
| SEC-DATA-02 | Encryption at rest | Datastores use at-rest encryption or volume encryption. | Storage config |
| SEC-DATA-03 | Retention enforcement | Data retention and deletion policies are enforced by TTL or job. | Retention job logs |
| SEC-RAG-01 | Safe ingest | RAG ingestion enforces allowlist and PII scrubbing. | Ingest pipeline tests |
| SEC-RAG-02 | Safe retrieval | Retrieval enforces ACL filters and evidence references. | RAG test cases |
| SEC-SUP-01 | Supply chain | Dependencies are pinned and SBOMs generated. | SBOM artifact |
| SEC-SDLC-01 | Secure SDLC | Code review, SAST, and secret scanning are required. | CI reports |
| SEC-IR-01 | Incident response | IR runbook is tested at least annually. | Exercise report |
| SEC-BCP-01 | Backups and DR | Backups verified; RTO/RPO defined and tested. | DR report |

## 4. Control Mapping (Template)
Map internal controls to external frameworks for audits.

| Control ID | NIST 800-53 | ISO 27001:2022 | CIS v8 | OWASP API 2023 | OWASP LLM Top 10 |
| --- | --- | --- | --- | --- | --- |
| SEC-AC-01 | TBD | TBD | TBD | TBD | TBD |
| SEC-AC-02 | TBD | TBD | TBD | TBD | TBD |
| SEC-AC-03 | TBD | TBD | TBD | TBD | TBD |
| SEC-SESS-01 | TBD | TBD | TBD | TBD | TBD |
| SEC-CR-01 | TBD | TBD | TBD | TBD | TBD |
| SEC-RATE-01 | TBD | TBD | TBD | TBD | TBD |
| SEC-LOG-01 | TBD | TBD | TBD | TBD | TBD |
| SEC-LOG-02 | TBD | TBD | TBD | TBD | TBD |
| SEC-DATA-01 | TBD | TBD | TBD | TBD | TBD |
| SEC-DATA-02 | TBD | TBD | TBD | TBD | TBD |
| SEC-DATA-03 | TBD | TBD | TBD | TBD | TBD |
| SEC-RAG-01 | TBD | TBD | TBD | TBD | TBD |
| SEC-RAG-02 | TBD | TBD | TBD | TBD | TBD |
| SEC-SUP-01 | TBD | TBD | TBD | TBD | TBD |
| SEC-SDLC-01 | TBD | TBD | TBD | TBD | TBD |
| SEC-IR-01 | TBD | TBD | TBD | TBD | TBD |
| SEC-BCP-01 | TBD | TBD | TBD | TBD | TBD |

## 5. Evidence Artifacts
- SBOMs for each release
- SLSA provenance attestations
- Vulnerability scan reports
- Penetration test reports (annual or major change)
- Access and audit log exports

## 6. Control Status Tracker (Template)
| Component | Control Coverage | Status | Notes |
| --- | --- | --- | --- |
| Backend API | SEC-AC, SEC-CR, SEC-LOG | Not Started | TBD |
| RAG Pipeline | SEC-RAG, SEC-DATA | Not Started | TBD |
| MCP Tools | SEC-AC, SEC-RATE | Not Started | TBD |
| Frontend | SEC-AC, SEC-SESS | Not Started | TBD |
| Infrastructure | SEC-DATA, SEC-BCP | Not Started | TBD |

## 7. Review Cadence
- Baseline reviewed quarterly and prior to major releases.

</details>
