# Test Command

입력: $ARGUMENTS (테스트 범위: all, backend, frontend, 또는 특정 파일 경로)

---

## 목적
지정된 범위의 테스트를 실행하고 결과를 분석합니다.

---

## 테스트 실행

### 전체 테스트 (기본값)

```bash
# Backend
cd /Users/ted/vivid/backend && source venv/bin/activate && pytest --tb=short -q

# Frontend Build (타입 체크 포함)
cd /Users/ted/vivid/frontend && npm run build
```

### Backend 테스트

```bash
cd /Users/ted/vivid/backend && source venv/bin/activate

# 전체
pytest --tb=short -q

# 상세 출력
pytest -v

# 특정 파일
pytest -v tests/path/to/test.py

# 특정 테스트 함수
pytest -v tests/path/to/test.py::test_function_name

# 커버리지
pytest --cov=app --cov-report=term-missing
```

### Frontend 테스트

```bash
cd /Users/ted/vivid/frontend

# 빌드 (타입 체크 + 번들링)
npm run build

# 린트
npm run lint

# E2E 전체
npm run test:e2e

# 특정 E2E
npm run test:e2e -- e2e/specific.spec.ts
```

---

## SSoT 테스트 매트릭스

| 변경 영역 | Backend 스모크 | Frontend 스모크 |
|-----------|----------------|-----------------|
| Dimension/AppRegistry | `pytest -v tests/routers/test_dimension_sse.py` | `npm run test:e2e -- e2e/dimension.spec.ts` |
| Credits/Run-token | `pytest -v tests/test_kelly_credit_service.py` | `npm run test:e2e -- e2e/credits.spec.ts` |
| Agent/Flow | `pytest -v tests/agents/test_vivid_agent_integration.py` | `npm run test:e2e -- e2e/agent-chat.spec.ts e2e/flow.spec.ts` |

---

## 결과 분석

### 실패 시 분석 프로세스
1. 에러 메시지 및 스택 트레이스 확인
2. 실패한 테스트 파일의 관련 소스 코드 확인
3. 최근 변경사항과의 연관성 분석
4. 수정 방안 제시

### 출력 형식

```markdown
# 테스트 결과

## 실행 환경
- 시간: YYYY-MM-DD HH:MM
- 범위: $ARGUMENTS

## 결과 요약
| 영역 | 통과 | 실패 | 스킵 |
|------|------|------|------|
| Backend | X | X | X |
| Frontend | ✅/❌ | - | - |

## 실패 테스트 상세

### test_name
- **파일**: `path/to/test.py:line`
- **에러**: 에러 메시지
- **원인 추정**: 분석 내용
- **수정 제안**:
  ```python
  # 수정 코드
  ```

## 다음 단계
- [ ] 수정 필요 사항
```

---

## 빠른 명령

| 목적 | 명령 |
|------|------|
| 전체 테스트 | `/test` |
| Backend만 | `/test backend` |
| Frontend만 | `/test frontend` |
| 특정 파일 | `/test tests/routers/test_dimension_sse.py` |
| 실패만 재실행 | `/test --failed` |
