# Pattern Promotion Criteria v1

**작성**: 2025-12-24  
**대상**: Product / Data / Ops  
**목표**: LLM 후보 패턴을 검증된 “공식”으로 승격하기 위한 기준

---

## 1) 상태 정의

- **proposed**: NotebookLM/Opal이 제안한 후보 (자동)
- **validated**: 근거/재현성 확인 완료 (사람 검수)
- **promoted**: 다중 사례에서 Lift 확인, 캡슐에 반영 가능

---

## 2) 승격 체크리스트 (validated 기준)

필수:
- source_id + evidence_ref 존재
- 패턴 설명이 **행동/시각적 단위**로 명확함
- pattern_name이 `15_PATTERN_TAXONOMY_V1.md` 네이밍 규칙을 따름
- 최소 2개 이상 소스에서 반복 확인
- rights_status가 restricted가 아님

권장:
- confidence ≥ 0.6
- 동일 패턴이 **다른 거장/유사 작품**에서도 재현됨

---

## 3) promoted 기준 (Evidence Loop)

필수:
- Pattern Trace 누적 ≥ 5
- 최소 2개 parent 계보에서 반복
- **Pattern Lift 평균 ≥ 0.10** (초기 기준, 추후 조정)
- 반례/실패 사례가 과도하지 않음

권장:
- Evidence Coverage ≥ 0.6
- 사용자 피드백(선택률/완주율) 개선이 관찰됨

---

## 4) 실패/보류 조건

- 근거 링크/구간이 불명확
- 다른 패턴과 중복되어 구분 불가
- Lift가 음수이거나 표본 부족
- 권리/출처 문제가 있는 경우

---

## 5) 승격 이후 액션

- Pattern Library에 `promoted` 상태로 등록
- `patternVersion` 스냅샷 버전 증가
- 캡슐 스펙/템플릿에 반영
- 변경 내역을 Release Note로 기록
