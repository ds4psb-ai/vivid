# AD Studio Masterpiece Official Pattern (MOP) - 2026 H2

작성일: 2026-02-14  
결정사항: North Star Metric은 `continuity_score`를 1순위로 고정한다.

## 1. Why This Pattern

조감독(AD Studio)의 실제 품질은 단일 장면 완성도보다 시퀀스 연속성에서 결정된다.  
따라서 2026년 하반기 아키텍처는 "엔진 성능 경쟁"보다 "연속성 회귀 방지 + 근거 추적"을 우선한다.

## 2. MOP-v1 Architecture

1. Contract Layer
- API 응답에 `sequence.continuity_score`를 항상 포함한다.
- 연속성 점수 범위는 `0.0 ~ 1.0`로 정규화한다.

2. Intelligence Layer
- decomposition 결과에서 앵커(캐릭터/스타일/조명/배경/행동)를 추출한다.
- `_calculate_continuity_score`로 시퀀스 단위 품질을 계산한다.

3. Orchestration Layer
- 엔진 선택 정책은 유지하되(예: Kling/Seedance/Veo), 엔진 라우팅의 성공 기준을 "연속성 손상 없음"으로 둔다.

4. Experience Layer
- `SequenceTimeline`에서 연속성 점수를 기본 배지로 노출한다.
- 밴드 정책:
  - `>= 80%`: 초록
  - `60~79%`: 호박
  - `< 60%`: 빨강

5. Trust Layer
- `evidence_refs` 누락 금지.
- provenance 정책(C2PA/SynthID 등)과 충돌 여부를 릴리즈 체크리스트에 포함한다.

## 3. Release Gate Policy (Hard Rule)

1. Gate A (필수): 연속성 점수
- `>= 0.80`: 정상 배포/확장
- `0.60 ~ 0.79`: 제한 롤아웃 + 보정 태스크
- `< 0.60`: 배포 보류

2. Gate B (보조): 턴어라운드 시간
- Gate A 통과 이후에만 속도 최적화 승인.
- 속도 개선 PR은 연속성 점수 회귀가 0임을 증명해야 한다.

## 4. 2026 H2 Roadmap (Execution Order)

1. 2026-07-01 ~ 2026-07-31: Metric Hardening
- 백엔드/프런트 계약에서 `continuity_score` 누락 불가화
- 스냅샷 회귀 테스트 추가

2. 2026-08-01 ~ 2026-08-31: Continuity Eval Expansion
- 장면 전환 유형별 회귀셋 구축
- 연속성 점수 기반 실험 대시보드 도입

3. 2026-09-01 ~ 2026-10-15: Engine Policy Tuning
- 엔진별 프롬프트 정책을 유지하며 연속성 우선 튜닝
- 엔진 추가/교체 시 동일 연속성 게이트 적용

4. 2026-10-16 ~ 2026-11-30: Trust + Export 강화
- evidence/provenance 출력 계약 고정
- 외부 공유용 결과물에 검증 메타 포함

5. 2026-12-01 ~ 2026-12-31: Scale Readiness
- 대량 시나리오 샘플 회귀 러닝
- 운영 런북/알림 기준 최종 확정

## 5. Immediate Backlog (Now)

1. `scripts/verify_ad_studio_future.sh`에 연속성 패턴 검사를 고정한다.
2. AD Studio 결과 리포트에 `continuity_score` 전/후를 필수 표기한다.
3. 릴리즈 노트 템플릿에 Gate A/B를 기본 섹션으로 추가한다.

## 6. External Evidence (Checked on 2026-02-13)

1. OpenAI Tools Guide: https://platform.openai.com/docs/guides/tools  
2. OpenAI Remote MCP Guide: https://platform.openai.com/docs/guides/tools-remote-mcp  
3. OpenAI Model Optimization Guide: https://platform.openai.com/docs/guides/model-optimization  
4. Google Veo API: https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/veo-video-generation  
5. DeepMind Veo: https://deepmind.google/models/veo/  
6. C2PA Specs: https://c2pa.org/specifications/  
7. DeepMind SynthID: https://deepmind.google/models/synthid/  
8. VGoT (arXiv): https://arxiv.org/abs/2412.02259  
9. GLASS (arXiv): https://arxiv.org/abs/2505.14538
