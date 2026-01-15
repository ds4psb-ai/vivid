# Deploy Command

입력: $ARGUMENTS (환경: staging, production)

---

## 목적
배포 전 체크리스트를 실행하고 배포 준비 상태를 확인합니다.

---

## 배포 전 체크리스트

### 1. 코드 품질 검증

```bash
# Backend 린트/타입체크
cd /Users/ted/vivid/backend && source venv/bin/activate
ruff check .
pyright

# Frontend 빌드
cd /Users/ted/vivid/frontend
npm run lint
npm run build
```

### 2. 테스트 실행

```bash
# Backend 테스트
cd /Users/ted/vivid/backend && pytest --tb=short -q

# Frontend E2E (주요 플로우만)
cd /Users/ted/vivid/frontend
npm run test:e2e -- e2e/dimension.spec.ts e2e/credits.spec.ts
```

### 3. DB 마이그레이션 확인

```bash
cd /Users/ted/vivid/backend && source venv/bin/activate

# 대기 중인 마이그레이션
alembic current
alembic history

# 마이그레이션 SQL 미리보기 (dry-run)
alembic upgrade head --sql
```

### 4. 환경 변수 확인

```bash
# 필수 환경 변수 존재 여부
env | grep -E '^(GEMINI_|POSTGRES_|REDIS_|GOOGLE_)'
```

### 5. Docker 이미지 빌드

```bash
# Backend
docker build -t vivid-backend:latest ./backend

# Frontend
docker build -t vivid-frontend:latest ./frontend
```

---

## 체크리스트 출력

```markdown
# 배포 준비 체크: $ARGUMENTS

## 1. 코드 품질
- [ ] Backend Lint: ✅/❌
- [ ] Backend Type Check: ✅/❌
- [ ] Frontend Lint: ✅/❌
- [ ] Frontend Build: ✅/❌

## 2. 테스트
- [ ] Backend Tests: X passed, X failed
- [ ] Frontend E2E: X passed, X failed

## 3. 데이터베이스
- [ ] 현재 리비전: xxx
- [ ] 대기 마이그레이션: X개
- [ ] 마이그레이션 SQL 리뷰: ✅/❌
- [ ] 롤백 가능: ✅/❌

## 4. 환경 변수
- [ ] GEMINI_API_KEY: ✅/❌
- [ ] POSTGRES_*: ✅/❌
- [ ] REDIS_URL: ✅/❌
- [ ] GOOGLE_CLIENT_*: ✅/❌

## 5. Docker
- [ ] Backend 이미지 빌드: ✅/❌
- [ ] Frontend 이미지 빌드: ✅/❌

## 6. 배포 영향도
- [ ] Breaking API 변경: 있음/없음
- [ ] 다운타임 예상: X분
- [ ] 롤백 계획: 준비됨/필요

## 결론
- 배포 준비 상태: ✅ Ready / ❌ Not Ready
- 차단 이슈: [설명]
```

---

## 배포 명령 (수동)

### Staging
```bash
# 1. 이미지 태그
docker tag vivid-backend:latest registry/vivid-backend:staging
docker tag vivid-frontend:latest registry/vivid-frontend:staging

# 2. 이미지 푸시
docker push registry/vivid-backend:staging
docker push registry/vivid-frontend:staging

# 3. 배포 트리거 (예: GitHub Actions)
gh workflow run deploy-staging
```

### Production
```bash
# 1. 최종 확인
/deploy production --confirm

# 2. 배포 실행
gh workflow run deploy-production
```

---

## 롤백

```bash
# 이전 버전으로 롤백
gh workflow run rollback --input version=X.Y.Z

# DB 롤백
cd backend && alembic downgrade -1
```

---

## 주의사항

- Production 배포는 항상 staging 검증 후 진행
- 다운타임이 필요한 마이그레이션은 사전 공지
- 롤백 계획 없이 배포 금지
- 주말/야간 배포 지양
