# Secure SDLC Policy

<details open>
<summary>한국어</summary>

버전: 0.1
최종 업데이트: 2026-01-15
상태: Draft
담당: Engineering Lead (TBD)

## 1. 목적
NIST SSDF에 맞춘 보안 SDLC 요구사항을 정의한다.

## 2. 범위
Backend, frontend, 데이터 파이프라인의 모든 코드, IaC, 설정 변경.

## 3. SSDF 기반 요구사항
### PO: 조직 준비
- 보안 책임과 교육을 문서화한다.
- 승인된 보안 도구를 유지하고 버전 관리한다.
- 시크릿 관리를 중앙화하고 감사를 수행한다.

### PS: 소프트웨어 보호
- 보호 브랜치와 필수 리뷰를 적용한다.
- 빌드 파이프라인을 격리하고 서명한다.
- 각 릴리스마다 SBOM을 생성한다.

### PW: 안전한 소프트웨어 생산
- 모든 변경은 코드 리뷰를 요구한다.
- SAST, 의존성 스캔, 시크릿 스캔을 필수화한다.
- 중요 변경은 위협 모델링과 보안 리뷰를 요구한다.
- 보안 케이스를 포함한 테스트를 작성한다.

### RV: 취약점 대응
- 취약점 접수 및 분류 프로세스를 문서화한다.
- 심각도별 패치 SLA를 정의한다.
- 보안 사고는 설계 및 테스트에 반영한다.

## 4. 공급망 보안
- 의존성 버전을 고정한다.
- 신뢰 가능한 레지스트리를 사용한다.
- SLSA provenance를 생성한다.

## 5. 릴리스 게이트(최소)
- 의존성에 치명 취약점이 없을 것.
- 보안 테스트(SAST/DAST/시크릿 스캔)를 통과할 것.
- run-token과 인증 경로를 테스트할 것.

## 6. 시크릿 및 키 관리
- 시크릿은 소스 컨트롤에 저장하지 않는다.
- 키 회전 주기를 문서화한다.
- 운영 시크릿은 최소 권한으로 접근한다.

## 7. 문서화
- 보안 관련 변경은 정책 문서와 00_DOCS_INDEX.md에 반영한다.

## 8. 예외
- 예외는 위험 수용과 만료일을 문서화한다.

## 9. 검토 주기
- 분기별 및 보안 사고 이후 재검토.

</details>

<details>
<summary>English</summary>

Version: 0.1
Last Updated: 2026-01-15
Status: Draft
Owner: Engineering Lead (TBD)

## 1. Purpose
Define secure software development lifecycle requirements aligned with NIST SSDF.

## 2. Scope
All code, infrastructure-as-code, and configuration changes across backend, frontend, and data pipelines.

## 3. SSDF-Aligned Requirements
### PO: Prepare the Organization
- Security ownership and training are documented.
- Approved security tooling is maintained and versioned.
- Secrets management is centralized and audited.

### PS: Protect the Software
- Source control uses protected branches and required reviews.
- Build pipelines are isolated and signed.
- SBOMs are generated for each release.

### PW: Produce Well-Secured Software
- Code review is required for all changes.
- SAST, dependency scanning, and secret scanning are mandatory.
- Critical changes require threat modeling and security review.
- Unit and integration tests include security cases where applicable.

### RV: Respond to Vulnerabilities
- Vulnerability intake and triage process is documented.
- Patch SLAs are defined by severity.
- Security incidents feed back into design and testing.

## 4. Supply Chain Security
- Dependencies are pinned or locked.
- Use trusted registries and verified sources.
- SLSA provenance is generated for releases.

## 5. Release Gates (Minimum)
- No critical vulnerabilities in dependencies.
- Security tests pass (SAST/DAST/secret scan).
- Run-token and auth flows are tested for critical paths.

## 6. Secrets and Key Management
- Secrets are not stored in source control.
- Key rotation schedules are documented.
- Production secrets require least-privilege access.

## 7. Documentation
- Security-relevant changes update policy docs and 00_DOCS_INDEX.md.

## 8. Exceptions
- Exceptions require documented risk acceptance and expiration.

## 9. Review Cadence
- Review quarterly and after security incidents.

</details>
