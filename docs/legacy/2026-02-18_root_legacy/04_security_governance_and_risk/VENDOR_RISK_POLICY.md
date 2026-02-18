# Vendor Risk Management Policy

<details open>
<summary>한국어</summary>

버전: 0.1
최종 업데이트: 2026-01-15
상태: Draft
담당: Security Lead (TBD)

## 1. 목적
Vivid 데이터를 처리하거나 접근하는 제3자 벤더의 평가 및 관리 요구사항을 정의한다.

## 2. 범위
모든 벤더(모델 제공사, 분석, 인프라 포함)에 적용한다.

## 3. 벤더 분류
| 등급 | 기준 | 예시 |
| --- | --- | --- |
| Tier 1 | Restricted 데이터 또는 핵심 워크로드 처리 | 모델 벤더, 결제 벤더 |
| Tier 2 | Confidential 데이터 처리 | 분석 도구, 지원 플랫폼 |
| Tier 3 | 저위험 서비스 | 공개 문서 도구 |

## 4. 사전 평가 요구사항
- 보안 설문과 증빙 검토
- 데이터 처리 계약(DPA)
- 사고 통지 의무
- 서브프로세서 공개 및 승인

## 5. 계약 요구사항
- 기밀 유지 및 데이터 보호 조항
- 감사 권한(필요 시)
- 계약 종료 시 데이터 삭제/반환

## 6. 지속 모니터링
- Tier 1 벤더는 연 1회 재평가
- 벤더 보안 권고사항 모니터링
- 범위 변경 시 재평가

## 7. 오프보딩
- 데이터 삭제/반환을 검증한다.
- 자격 증명과 접근 경로를 철회한다.

## 8. 예외
- 예외는 승인과 만료일이 필요하다.

</details>

<details>
<summary>English</summary>

Version: 0.1
Last Updated: 2026-01-15
Status: Draft
Owner: Security Lead (TBD)

## 1. Purpose
Define requirements for evaluating and managing third-party vendors that process or access Vivid data.

## 2. Scope
Applies to all vendors, including model providers, analytics, and infrastructure services.

## 3. Vendor Classification
| Tier | Criteria | Examples |
| --- | --- | --- |
| Tier 1 | Processes Restricted data or core workloads | Model providers, payment processors |
| Tier 2 | Processes Confidential data | Analytics tools, support platforms |
| Tier 3 | Low-risk services | Public documentation tools |

## 4. Due Diligence Requirements
- Security questionnaire and evidence review
- Data processing agreement (DPA) for data access
- Incident notification requirements
- Subprocessor disclosure and approval

## 5. Contract Requirements
- Confidentiality and data protection clauses
- Right to audit (as applicable)
- Data deletion and return on termination

## 6. Ongoing Monitoring
- Annual review for Tier 1 vendors
- Monitor vendor security advisories
- Re-evaluate on major scope changes

## 7. Offboarding
- Ensure data deletion or return is verified.
- Revoke credentials and access paths.

## 8. Exceptions
- Exceptions require documented approval and expiration.

</details>
