# Data Governance Policy

<details open>
<summary>한국어</summary>

버전: 0.1
최종 업데이트: 2026-01-15
상태: Draft
담당: Data Protection Lead (TBD)

## 1. 목적
Vivid가 데이터를 분류, 저장, 처리, 폐기하는 방식을 정의한다.

## 2. 범위
- 사용자 데이터, 콘텐츠 입력/출력
- RAG 데이터(문서, 임베딩, 인덱스, 증거 참조)
- 로그, 메트릭, 감사 추적
- 시크릿, 자격 증명, 설정 데이터

## 3. 데이터 분류
| 등급 | 설명 | 예시 |
| --- | --- | --- |
| Public | 공개를 전제로 한 정보 | 마케팅 페이지, 공개 문서 |
| Internal | 내부 전용, 저위험 | 비민감 운영 데이터 |
| Confidential | 민감한 비즈니스 또는 사용자 데이터 | 사용자 입력, 출력, 계정 데이터 |
| Restricted | 고위험 데이터 또는 시크릿 | 토큰, API 키, 서명 키 |

## 4. 데이터 처리 원칙
- 최소 수집 원칙을 준수한다.
- 인제스트 시 분류와 메타데이터 태깅을 수행한다.
- 전송/저장 시 암호화를 적용한다.
- 최소 권한과 역할 기반 접근을 적용한다.
- Sealed capsule 정책 적용 시 raw prompt와 내부 체인은 저장하지 않는다.
- 로그와 분석 데이터는 PII를 레드랙션 또는 토큰화한다.

## 5. 데이터 라이프사이클
1) 수집 -> 2) 처리 -> 3) 저장 -> 4) 보존 -> 5) 삭제

## 6. 보존 일정(템플릿)
| 데이터 유형 | 위치 | 보존 기간 | 삭제 방법 |
| --- | --- | --- | --- |
| L0 캐시 | Memory/Redis | 1 hour | TTL 만료 |
| L1 임베딩 | Qdrant | 7-30 days | TTL 또는 리인덱싱 정리 |
| NotebookLM 데이터 | 외부 벤더 | 계약 기준 | 벤더 삭제 프로세스 |
| 사용자 입력/출력 | Postgres | 30-180 days | 작업 기반 삭제 |
| 로그(마스킹) | 로그 스토어 | 30-90 days | 로그 보존 정책 |
| 감사 로그 | 로그 스토어 | 1-3 years | 아카이브 저장 |

## 7. 접근 통제
- Restricted 데이터는 명시적 승인과 감사 로그가 필요하다.
- 접근은 역할, 작업, 기간 기준으로 부여한다.
- 서비스 계정은 범위를 최소화하고 정기적으로 교체한다.

## 8. 데이터 레지던시
- 지역별 데이터 레지던시 요구사항을 문서화한다.
- 국외 이전은 승인과 보호 조치를 필요로 한다.

## 9. 정보주체 요청
- 열람, 정정, 삭제, 내보내기 절차를 문서화한다.
- 응답 SLA: TBD days.

## 10. 제3자 처리
- 벤더는 최소 보안 요구사항을 충족해야 한다.
- 벤더 접근은 로깅과 정기 리뷰가 필요하다.

## 11. 검토 주기
- 분기별 및 주요 데이터 파이프라인 변경 후 검토.

</details>

<details>
<summary>English</summary>

Version: 0.1
Last Updated: 2026-01-15
Status: Draft
Owner: Data Protection Lead (TBD)

## 1. Purpose
Define how Vivid classifies, stores, processes, and retires data across all systems.

## 2. Scope
- User data, content inputs/outputs
- RAG data (documents, embeddings, indices, evidence refs)
- Logs, metrics, and audit trails
- Secrets, credentials, and configuration data

## 3. Data Classification
| Level | Description | Examples |
| --- | --- | --- |
| Public | Intended for public release | Marketing pages, public docs |
| Internal | Internal use, low risk | Non-sensitive operational data |
| Confidential | Sensitive business or user data | User inputs, outputs, account data |
| Restricted | High-risk data or secrets | Tokens, API keys, signing keys |

## 4. Data Handling Rules
- Collect only required data (data minimization).
- Classify data at ingestion and tag metadata.
- Encrypt in transit and at rest.
- Restrict access by least privilege and role.
- Do not store raw prompts or internal chain data when sealed capsule policy applies.
- Redact or tokenize PII in logs and analytics.

## 5. Data Lifecycle
1) Collection -> 2) Processing -> 3) Storage -> 4) Retention -> 5) Deletion

## 6. Retention Schedule (Template)
| Data Type | Location | Retention | Deletion Method |
| --- | --- | --- | --- |
| L0 cache | Memory/Redis | 1 hour | TTL expiration |
| L1 embeddings | Qdrant | 7-30 days | TTL or reindex purge |
| NotebookLM data | External provider | Per contract | Provider deletion process |
| User inputs/outputs | Postgres | 30-180 days | Job-based purge |
| Logs (redacted) | Log store | 30-90 days | Log retention policy |
| Audit logs | Log store | 1-3 years | Archived storage |

## 7. Access Control
- Restricted data requires explicit approval and audit logging.
- Access is granted by role, task, and time-bound need.
- Service accounts are scoped and rotated regularly.

## 8. Data Residency
- Data residency requirements are documented per region and customer.
- Cross-border transfers require approval and documented safeguards.

## 9. Data Subject Requests
- Provide a documented process for access, correction, deletion, and export.
- Response SLA: TBD days.

## 10. Third-Party Data Processing
- Vendors must meet minimum security requirements and DPAs.
- Vendor access to data is logged and reviewed periodically.

## 11. Review Cadence
- Review quarterly and after major data pipeline changes.

</details>
