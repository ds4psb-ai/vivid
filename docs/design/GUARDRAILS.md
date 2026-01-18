# Design Guardrails

> 목적: UI 테마/디자인 시스템 개선 중 **하드코딩 색상**이 재발하는 것을 자동으로 차단한다.

## 1) Guardrail 스캐너

- 스캐너: `scripts/design_guardrail.py`
- 기본 스캔 대상: `frontend/src`
- 감지 패턴: `#hex`, `rgb/rgba`, `hsl/hsla`, `oklch/oklab`
- 결과: `docs/design/design_guardrail_baseline.json`

## 2) 실행 방법

```bash
python scripts/design_guardrail.py --root frontend/src --baseline docs/design/
```

### 기준 갱신 (의도된 변경일 때만)

```bash
python scripts/design_guardrail.py --root frontend/src --baseline docs/design/ --update-baseline
```

## 3) 적용 원칙

- 신규 색상은 **반드시 토큰**으로 추가한다.
- 하드코딩이 필요한 경우:
  1) 토큰으로 추가 가능한지 먼저 검토
  2) 불가피하면 **명시적인 이유**를 기록
  3) baseline 업데이트와 함께 PR에 근거 포함

## 4) 실패 시 대응

- 신규 하드코딩이 발견되면 **빌드/PR에서 실패**하도록 한다.
- 기본 원칙: **새 하드코딩 금지 → 토큰화 우선**

---

### 출력 예시

```
python scripts/design_guardrail.py --root frontend/src --baseline docs/design/
PASSED
```
