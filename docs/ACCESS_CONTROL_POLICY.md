# Access Control Policy

<details open>
<summary>한국어</summary>

버전: 0.1
최종 업데이트: 2026-01-15
상태: Draft
담당: Security Lead (TBD)

## 1. 목적
Vivid의 인증, 인가, 접근 통제 요구사항을 정의한다.

## 2. 범위
- 사용자 인증과 세션
- 관리자 접근과 권한 작업
- 서비스 간 접근
- 툴 실행과 run-token

## 3. 아이덴티티와 인증
- 사용자 세션은 서명된 토큰으로 인증한다.
- 운영 환경에서 세션 쿠키는 Secure와 HttpOnly를 사용한다.
- 관리자 계정은 MFA를 요구한다(지원 시).

## 4. 인가
- 모든 접근은 최소 권한 기반 RBAC를 적용한다.
- 관리자 작업은 명시적 관리자 권한을 요구한다.
- 민감 작업은 추가 검증을 요구할 수 있다.

## 5. 서비스 계정
- 서비스 계정은 서비스 단위로 분리하고 범위를 최소화한다.
- 자격 증명은 정의된 주기로 교체한다.

## 6. Run-token 및 실행 통제
- 실행 엔드포인트는 유효 run-token이 필요하다.
- run-token 발급은 크레딧 예약과 신원 검증이 필요하다.
- run-token 사용은 레이트 리밋과 감사 로깅을 적용한다.

## 7. 세션 관리
- 세션 TTL을 정의하고 강제한다.
- 계정 침해 시 세션 취소를 지원한다.

## 8. 접근 리뷰
- 분기별로 접근 권한을 리뷰한다.
- 관리자 접근은 매 리뷰마다 재검증한다.

## 9. 예외
- 예외는 승인과 만료일이 필요하다.

</details>

<details>
<summary>English</summary>

Version: 0.1
Last Updated: 2026-01-15
Status: Draft
Owner: Security Lead (TBD)

## 1. Purpose
Define authentication, authorization, and access control requirements for all Vivid systems.

## 2. Scope
- User authentication and sessions
- Admin access and privileged actions
- Service-to-service access
- Tool execution and run-tokens

## 3. Identity and Authentication
- User sessions are authenticated using signed tokens.
- Session cookies are secure and HttpOnly in production.
- MFA is required for admin accounts (if supported).

## 4. Authorization
- All access is role-based with least privilege.
- Admin actions require explicit admin role checks.
- Sensitive actions require additional verification where applicable.

## 5. Service Accounts
- Service accounts are unique per service and scoped to minimal permissions.
- Credentials are rotated on a defined schedule.

## 6. Run-Token and Execution Controls
- Execution endpoints require a valid run-token.
- Run-token issuance requires credit reservation and identity verification.
- Run-token usage is rate-limited and audited.

## 7. Session Management
- Session TTL is defined and enforced.
- Session revocation is supported for compromised accounts.

## 8. Access Reviews
- Access reviews are conducted quarterly.
- Admin access is revalidated at each review.

## 9. Exceptions
- Exceptions require documented approval and expiration.

</details>
