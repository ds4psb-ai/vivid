# Incident Response and Business Continuity Plan

<details open>
<summary>한국어</summary>

버전: 0.1
최종 업데이트: 2026-01-15
상태: Draft
담당: Operations Lead (TBD)

## 1. 목적
보안 사고 대응과 업무 연속성 보장을 위한 프로세스를 정의한다.

## 2. 범위
모든 운영 서비스, 데이터 저장소, 인프라.

## 3. 심각도 레벨
| 심각도 | 기준 | 예시 | 초기 대응 |
| --- | --- | --- | --- |
| SEV0 | 치명적 장애 또는 침해 진행 | 데이터 유출, 인증 우회 | 즉시 호출, 임원 통지 |
| SEV1 | 대규모 영향 | 서비스 다운, 결제 실패 | 15분 내 온콜 |
| SEV2 | 부분 장애 | 오류 증가, RAG 지연 | 1시간 내 온콜 |
| SEV3 | 경미한 문제 | 비중요 버그 | 1영업일 내 분류 |

## 4. 역할과 책임
- Incident Commander: 대응 조율 및 커뮤니케이션.
- Security Lead: 침해 분석 및 증거 보존.
- Engineering Lead: 기술적 복구.
- Comms Lead: 내부/외부 커뮤니케이션.

## 5. 사고 대응 단계
1) 탐지 및 확인
2) 분류 및 범위 지정
3) 격리 및 완화
4) 근본 원인 제거
5) 복구 및 검증
6) 사후 리뷰

## 6. 증거 보존
- 로그, 트레이스, 관련 산출물을 보존한다.
- 승인 없이 증거 시스템을 변경하지 않는다.
- 조사 체인 오브 커스터디를 유지한다.

## 7. 커뮤니케이션 계획
- SEV0/SEV1은 60분 내 정기 업데이트.
- 외부 커뮤니케이션은 법무/프라이버시 기준에 따른다.
- 고객 통지는 계약 및 규제 의무를 따른다.

## 8. 업무 연속성
### 8.1 백업 정책
- 핵심 데이터 저장소는 자동 백업과 검증을 수행한다.
- 백업 복구 테스트는 최소 분기 1회.

### 8.2 RTO/RPO 목표(템플릿)
| 시스템 | RTO | RPO | 비고 |
| --- | --- | --- | --- |
| API | TBD | TBD | TBD |
| RAG Pipeline | TBD | TBD | TBD |
| Postgres | TBD | TBD | TBD |
| Qdrant | TBD | TBD | TBD |
| Redis | TBD | TBD | TBD |

### 8.3 재해 복구
- DR 런북을 유지하고 연 1회 테스트한다.
- 페일오버 절차를 문서화하고 검증한다.

## 9. 사후 리뷰
- 사고 종료 5영업일 이내 수행.
- 원인, 타임라인, 조치 항목을 문서화.
- 보안 통제와 테스트에 반영.

## 10. 검토 주기
- 분기별 및 주요 사고 이후 재검토.

</details>

<details>
<summary>English</summary>

Version: 0.1
Last Updated: 2026-01-15
Status: Draft
Owner: Operations Lead (TBD)

## 1. Purpose
Define the process for handling security incidents and ensuring business continuity.

## 2. Scope
All production services, data stores, and supporting infrastructure.

## 3. Severity Levels
| Severity | Criteria | Examples | Initial Response |
| --- | --- | --- | --- |
| SEV0 | Critical outage or active breach | Data exfiltration, auth bypass | Immediate paging, exec notification |
| SEV1 | Major user impact | Service down, payment failure | On-call page within 15 min |
| SEV2 | Partial degradation | Elevated errors, slow RAG | On-call within 1 hour |
| SEV3 | Minor issue | Non-critical bug | Triage within 1 business day |

## 4. Roles and Responsibilities
- Incident Commander: coordinates response and communications.
- Security Lead: breach triage and evidence handling.
- Engineering Lead: technical remediation.
- Comms Lead: internal and external updates.

## 5. Incident Response Phases
1) Detect and validate
2) Triage and scope
3) Contain and mitigate
4) Eradicate root cause
5) Recover and verify
6) Post-incident review

## 6. Evidence Preservation
- Preserve logs, traces, and related artifacts.
- Do not modify evidence systems without approval.
- Maintain chain of custody for investigations.

## 7. Communications Plan
- Internal updates every 60 minutes for SEV0/SEV1.
- External communications per legal and privacy requirements.
- Customer notifications follow contract and regulatory obligations.

## 8. Business Continuity
### 8.1 Backup Policy
- Backups for critical data stores are automated and verified.
- Backup restoration tests run at least quarterly.

### 8.2 RTO/RPO Targets (Template)
| System | RTO | RPO | Notes |
| --- | --- | --- | --- |
| API | TBD | TBD | TBD |
| RAG Pipeline | TBD | TBD | TBD |
| Postgres | TBD | TBD | TBD |
| Qdrant | TBD | TBD | TBD |
| Redis | TBD | TBD | TBD |

### 8.3 Disaster Recovery
- DR runbooks are maintained and tested annually.
- Failover procedures are documented and validated.

## 9. Post-Incident Review
- Conduct within 5 business days.
- Document root cause, timeline, and corrective actions.
- Update security controls and tests.

## 10. Review Cadence
- Review quarterly and after major incidents.

</details>
