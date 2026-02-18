# Auth Coverage Draft (2026-01-17)

> 자동 스캔: router 소스에서 Depends(require_*, get_current_user*) 패턴을 grep 기반으로 집계한 **1차 초안**입니다.
> 라우터 내부에서 직접 auth 체크를 수행하는 경우는 이 목록에 반영되지 않을 수 있습니다.

## 요약
- 총 라우터: 39개
- 명시적 auth 의존성 존재: 28개
- **명시적 auth 의존성 없음**: 11개

## 명시적 auth 의존성 없음 (우선 검토 필요)
| Router | 비고 |
| --- | --- |
| auth.py | 인증 관련 공개 엔드포인트 (정상) |
| crebit.py | 의존성 미탐지 (직접 체크 가능성) |
| db_optimizer.py | 의존성 미탐지 (직접 체크 가능성) |
| health.py | 공개 헬스체크 가능성 |
| intent.py | 의존성 미탐지 (직접 체크 가능성) |
| intent_helpers.py | 의존성 미탐지 (직접 체크 가능성) |
| internal.py | ⚠️ 고위험/민감 영역 — mTLS(require_permission) 사용 여부 확인 필요 |
| mcp.py | ⚠️ 고위험/민감 영역 — 보호 메커니즘 재확인 필요 |
| payment.py | ⚠️ 고위험/민감 영역 — 보호 메커니즘 재확인 필요 |
| tools.py | ⚠️ 고위험/민감 영역 — 보호 메커니즘 재확인 필요 |
| uqsl.py | ⚠️ 고위험/민감 영역 — 보호 메커니즘 재확인 필요 |

## 라우터별 의존성 히트 요약
| Router | Router-level auth | Endpoint auth hits | require_admin | require_user_id | get_current_user | get_current_user_optional | get_optional_user_id |
| --- | --- | --- | --- | --- | --- | --- | --- |
| admin.py | — | 21 | 20 | 1 | 0 | 0 | 0 |
| affiliate.py | — | 4 | 0 | 4 | 0 | 0 | 0 |
| agent.py | — | 5 | 0 | 0 | 5 | 0 | 0 |
| auth.py | — | 0 | 0 | 0 | 0 | 0 | 0 |
| batch.py | — | 8 | 0 | 0 | 0 | 8 | 0 |
| capsules.py | — | 7 | 0 | 0 | 7 | 0 | 0 |
| constellation.py | — | 9 | 0 | 0 | 0 | 0 | 9 |
| content_metrics.py | — | 1 | 0 | 0 | 1 | 0 | 0 |
| context.py | — | 4 | 0 | 0 | 4 | 0 | 0 |
| crebit.py | — | 0 | 0 | 0 | 0 | 0 | 0 |
| credits.py | — | 3 | 0 | 3 | 0 | 0 | 0 |
| dashboard.py | — | 2 | 0 | 0 | 2 | 0 | 0 |
| db_optimizer.py | — | 0 | 0 | 0 | 0 | 0 | 0 |
| feedback.py | — | 4 | 2 | 0 | 2 | 0 | 0 |
| fork.py | — | 10 | 0 | 0 | 10 | 0 | 0 |
| health.py | — | 0 | 0 | 0 | 0 | 0 | 0 |
| humancloud.py | — | 11 | 0 | 0 | 11 | 0 | 0 |
| intent.py | — | 0 | 0 | 0 | 0 | 0 | 0 |
| intent_helpers.py | — | 0 | 0 | 0 | 0 | 0 | 0 |
| internal.py | — | 0 | 0 | 0 | 0 | 0 | 0 |
| mcp.py | — | 0 | 0 | 0 | 0 | 0 | 0 |
| mcp_v2.py | — | 14 | 3 | 11 | 0 | 0 | 0 |
| miniapps.py | — | 2 | 0 | 0 | 2 | 0 | 0 |
| monitor.py | — | 3 | 0 | 0 | 0 | 3 | 0 |
| payment.py | — | 0 | 0 | 0 | 0 | 0 | 0 |
| rag.py | — | 1 | 1 | 0 | 0 | 0 | 0 |
| rag_admin.py | — | 18 | 0 | 0 | 18 | 0 | 0 |
| rag_feedback.py | — | 2 | 0 | 0 | 0 | 2 | 0 |
| reviews.py | — | 10 | 0 | 0 | 10 | 0 | 0 |
| run_token.py | — | 1 | 0 | 1 | 0 | 0 | 0 |
| sandbox.py | — | 6 | 0 | 0 | 6 | 0 | 0 |
| settlements.py | — | 11 | 0 | 0 | 11 | 0 | 0 |
| singularity.py | — | 4 | 1 | 0 | 3 | 0 | 0 |
| teaching.py | — | 6 | 0 | 0 | 6 | 0 | 0 |
| telemetry.py | — | 8 | 0 | 0 | 8 | 0 | 0 |
| tools.py | — | 0 | 0 | 0 | 0 | 0 | 0 |
| uqsl.py | — | 0 | 0 | 0 | 0 | 0 | 0 |
| user_settings.py | — | 3 | 0 | 0 | 3 | 0 | 0 |
| workflow.py | — | 6 | 0 | 0 | 4 | 2 | 0 |

## 다음 액션 (전수조사계획 연동)
1. 위 **명시적 auth 미적용 라우터**에 대해 실제 보호 메커니즘(내부 토큰, mTLS, run-token, IP allowlist) 여부 점검
2. 공용 엔드포인트 허용 범위 정의 및 위험도 라벨링 (P0/P1/P2)
3. GraphQL 및 MCP 경로는 별도 심층 검사 (Context auth/role 확인)
