---
description: 파이프라인 역추적, 중복 발견, 안전한 통합/정리를 위한 체계적 워크플로우
---

> ⚠️ **WARNING**: 기존 파이프라인 손상 시 서비스 장애 발생 - 모든 단계 신중히 진행

## Phase 1: 엔드포인트 매핑 (Endpoint Discovery)

1. **대상 파이프라인 식별**
   ```bash
   # 사용자가 지정한 파이프라인 키워드로 검색
   grep -rn "<PIPELINE_KEYWORD>" backend/app/routers/*.py --include="*.py"
   ```

2. **모든 관련 엔드포인트 추출**
   ```bash
   for f in backend/app/routers/*.py; do 
     echo "=== $f ===" && grep -n "@router\." "$f" | head -20
   done
   ```

3. **호출 체인 역추적** (endpoint → service → pipeline)
   - 각 엔드포인트의 함수 본문 확인
   - import문 추적하여 서비스 레이어 매핑
   - 서비스에서 실제 파이프라인 호출 지점 확인

## Phase 2: 중복 발견 (Duplicate Detection)

> **핵심 원칙**: 하나 찾았다고 멈추지 말고 같은 계열 모두 찾기

4. **서비스 레이어 중복 검사**
   ```bash
   # 동일 기능의 다른 구현 찾기
   grep -rn "<FUNCTION_NAME>" backend/app/services/*.py
   ```

5. **분류표 작성**
   | 파일 | 함수 | 호출자 | 고유기능 | 중복여부 |
   |------|------|--------|----------|----------|
   | (분석 결과 기록) | | | | |

6. **Dead Code 확인**
   ```bash
   # 호출자가 없는 함수/파일 검색
   grep -rn "<SUSPECTED_DEAD_CODE>" backend/app/ --include="*.py" | grep -v "def \|class "
   ```

## Phase 3: 부분 중복 분석 (Critical Step)

> **⚠️ 가장 중요**: 부분 중복 시 통합 없이 삭제 금지

7. **코드 비교 매트릭스**
   - 두 버전의 함수를 line-by-line 비교
   - 고유 로직(fallback, edge case 처리) 식별
   - 더 완전한 버전 결정

8. **통합 결정**
   | 함수 | 버전A 고유기능 | 버전B 고유기능 | 통합 방향 |
   |------|----------------|----------------|-----------|
   | | | | A → B / B → A / 병합 |

## Phase 4: 안전한 실행 (Safe Execution)

9. **더 완전한 버전으로 통합**
   - 고유 기능을 canonical 파일에 merge
   - 기존 import path 유지 (alias 사용)

10. **중복 코드 삭제**
    - 통합 완료 후에만 삭제
    - 삭제 전 주석으로 이전 위치 표시

11. **Dead Code 삭제**
    ```bash
    # 호출자 0개 확인 후에만 삭제
    rm <DEAD_CODE_FILE>
    ```

## Phase 5: 전수검사 (Full Verification)

// turbo-all

12. **Import 테스트**
    ```bash
    cd backend && source venv/bin/activate && python3 -c "from app.routers.<ROUTER> import router; print('✅ OK')"
    ```

13. **기능 테스트** (Legacy fallback 포함)
    ```python
    # 모든 schema 버전에 대해 테스트
    test_cases = [
        {"v2_format": {...}},
        {"v1_legacy": {...}},
    ]
    for tc in test_cases:
        result = <FUNCTION>(tc)
        assert result is not None
    ```

14. **API 엔드포인트 테스트**
    ```bash
    curl -s "http://localhost:8100/api/v1/<ENDPOINT>" | python3 -c "import sys,json; print(json.load(sys.stdin))"
    ```

## Phase 6: Git 복구 준비

15. **삭제 전 Git 상태 확인**
    ```bash
    git status --short
    git diff HEAD --name-only
    ```

16. **실수 시 복구**
    ```bash
    git checkout HEAD -- <DELETED_FILE>
    ```

---

## 사용법

```
/dedupe <파이프라인_키워드>
```

예시:
- `/dedupe dimension` - Dimension 도구 파이프라인 역추적
- `/dedupe singularity` - 특이점 템플릿 파이프라인 역추적
- `/dedupe teaching` - Teaching Capsule 파이프라인 역추적
- `/dedupe vdg` - VDG 분석 파이프라인 역추적
- `/dedupe agent` - Agent Chat 파이프라인 역추적
- `/dedupe credits` - 크레딧/결제 파이프라인 역추적
- `/dedupe affiliate` - 제휴/리퍼럴 파이프라인 역추적

---

## 체크리스트

- [ ] Phase 1: 모든 엔드포인트 매핑 완료
- [ ] Phase 2: 같은 계열 중복 **모두** 발견
- [ ] Phase 3: 부분 중복 분석 및 통합 방향 결정
- [ ] Phase 4: 통합 후 삭제 (순서 엄수)
- [ ] Phase 5: 전수검사 통과
- [ ] Phase 6: Git 상태 확인
