---
name: vivid-ad-studio-future
description: Use when upgrading Vivid AD Studio (Assistant Director) workflows, prompt generation, or orchestration, especially for scenario decomposition, multi-engine output, continuity quality, evidence traceability, and release verification.
---

# Vivid AD Studio Future Ops

## Overview

AD Studio(조감독 AI)를 "2026 하반기 기준 실전형 미래 앱"으로 유지/고도화하기 위한 운영 스킬이다.

이 스킬은 세 가지를 강제한다.

1. 코드 변경 전에 AD Studio 경계(입력/출력/비용/증거)를 먼저 확인한다.
2. 변경을 한 뒤에는 조감독 전용 검증 루틴을 실행한다.
3. 트렌드 반영 시에는 근거 링크를 남기고, 추정과 사실을 분리한다.

## Trigger

- `backend/app/routers/dimension/ad_studio.py`를 수정할 때
- `backend/app/services/ad_brain.py` 또는 프롬프트 엔진을 수정할 때
- `frontend/src/components/dimension/ADStudioPanel.tsx` UX/입출력 계약을 바꿀 때
- Kling/Seedance/Veo 엔진 라우팅 정책을 바꿀 때
- 조감독 결과 품질(연속성/구도/감정선) 회귀를 디버깅할 때

## Kimoring Pattern Applied

`codefactory-co/kimoring-ai-skills`의 운영 패턴을 AD Studio에 맞게 축소 적용한다.

1. 변경 파일 수집
2. 변경 파일과 검증 항목 매핑
3. 미커버 항목 탐지
4. 검증 실행
5. 리포트 출력

실행 스크립트:

```bash
bash scripts/verify_ad_studio_future.sh
```

테스트 포함:

```bash
bash scripts/verify_ad_studio_future.sh --with-tests
```

## Local Ground Truth

먼저 아래 기준 파일을 읽고 시작한다.

- `backend/app/routers/dimension/ad_studio.py`
- `backend/app/services/ad_brain.py`
- `backend/app/services/ad_prompt_engine.py`
- `frontend/src/components/dimension/ADStudioPanel.tsx`
- `backend/tests/routers/test_ad_studio.py`

세부 맵은 `docs/skills/vivid-ad-studio-future/local-audit-map.md`를 참조한다.

## 2026 Future Upgrade Lanes

아래 레인을 동시에 다 잡으려 하지 말고, 1~2개 레인씩 고정해 진행한다.

1. Continuity Lane
- 시퀀스 단위 앵커(캐릭터/조명/스타일) 회귀 방지
- scene 간 카메라 거리/템포 변화가 결과에 일관되게 반영되는지 검증

2. Engine Lane
- 엔진별 프롬프트 계약(Kling/Seedance/Veo) 분리를 유지
- 엔진 추가 시에도 `target_engines` 검증과 UI 토글이 깨지지 않게 유지

3. Trust Lane
- evidence_refs 누락 금지
- 워터마크/콘텐츠 출처 정책(C2PA/SynthID 등)과 충돌하는 출력 방지

4. Eval Lane
- 품질 기준을 "감"이 아닌 테스트/측정 항목으로 관리
- 변경 전/후 비교 지표를 남긴다

## Workflow

1. Scope 확정
- 어떤 레인을 개선할지 먼저 선언
- 영향 파일을 5개 이내로 제한

2. Test first
- `backend/tests/routers/test_ad_studio.py`에서 실패하는 테스트를 먼저 만든다
- 최소 수정으로 GREEN을 만든다

3. Implement
- Router: 입력 검증/모델 허용/엔진 허용 범위
- Brain: decomposition 품질 + evidence refs
- Panel: 입력 UX + 크레딧/에러 처리

4. Verify
- 아래 검증 커맨드를 실행하고 결과를 기록한다

```bash
cd /Users/ted/vivid/backend && pytest -q tests/routers/test_ad_studio.py
```

필요 시:

```bash
cd /Users/ted/vivid/backend && pytest -q tests/agents/test_vivid_agent_integration.py tests/routers/test_agent_streaming.py
cd /Users/ted/vivid/frontend && npm run test:e2e -- e2e/agent-chat.spec.ts e2e/flow.spec.ts
```

5. Evidence note
- 어떤 근거(문서/테스트/지표)로 변경을 정당화했는지 남긴다

## 2026 Research Guardrails

- 웹/시장 근거는 `docs/skills/vivid-ad-studio-future/market-2026-web-research.md`에 링크와 함께 업데이트한다.
- "확정 사실"과 "전략 추정"을 분리한다.
- 모델/플랫폼의 최신 상태는 릴리즈 시점마다 재확인한다.

## Output Contract

최종 보고에는 최소 아래를 포함한다.

1. 변경 레인 (Continuity/Engine/Trust/Eval 중 무엇인지)
2. 영향 파일 목록
3. 실행한 검증 명령과 통과 여부
4. 외부 근거 링크
5. 남은 리스크
