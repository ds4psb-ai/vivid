# Server Command

입력: $ARGUMENTS (start, stop, restart, status, 비어있으면 status)

---

## 목적
개발 서버를 관리합니다 (Backend, Frontend, Docker services).

---

## 명령어

### status (기본값)
```bash
# Docker 서비스 상태
docker-compose ps

# Backend 프로세스
lsof -i :8100 2>/dev/null || echo "Backend not running"

# Frontend 프로세스
lsof -i :3100 2>/dev/null || echo "Frontend not running"
```

### start
```bash
# 1. Docker 서비스 시작 (postgres, redis, qdrant)
docker-compose up -d

# 2. Backend 시작
cd /Users/ted/vivid/backend && source venv/bin/activate
uvicorn app.main:app --reload --port 8100 &

# 3. Frontend 시작
cd /Users/ted/vivid/frontend && npm run dev &
```

### stop
```bash
# Frontend 종료
pkill -f "next dev" || true

# Backend 종료
pkill -f "uvicorn app.main:app" || true

# Docker 서비스 종료 (선택)
docker-compose down
```

### restart
```bash
# 1. 기존 프로세스 종료
pkill -f "uvicorn app.main:app" || true
pkill -f "next dev" || true

# 2. 재시작
cd /Users/ted/vivid/backend && source venv/bin/activate
uvicorn app.main:app --reload --port 8100 &
cd /Users/ted/vivid/frontend && npm run dev &
```

---

## 서비스 포트

| 서비스 | 포트 | 설명 |
|--------|------|------|
| Frontend | 3100 | Next.js dev server |
| Backend | 8100 | FastAPI server |
| PostgreSQL | 5433 | Database |
| Redis | 6380 | Cache/Queue |
| Qdrant | 6333 | Vector DB |
| Chrome CDP | 9223 | NotebookLM 자동화 |

---

## 문제 해결

### 포트 충돌
```bash
# 특정 포트 사용 프로세스 확인
lsof -i :8100

# 강제 종료
kill -9 $(lsof -t -i:8100)
```

### Docker 문제
```bash
# 컨테이너 로그 확인
docker-compose logs -f postgres

# 볼륨 초기화 (주의: 데이터 삭제)
docker-compose down -v
docker-compose up -d
```

### Backend 문제
```bash
# 로그 확인
tail -f /Users/ted/vivid/backend/logs/app.log

# 의존성 재설치
cd /Users/ted/vivid/backend
pip install -r requirements.txt
```

### Frontend 문제
```bash
# 캐시 정리
cd /Users/ted/vivid/frontend
rm -rf .next node_modules/.cache
npm run dev
```

---

## 출력 형식

```markdown
# Server Status

## Docker Services
| Service | Status | Port |
|---------|--------|------|
| postgres | ✅ Running | 5433 |
| redis | ✅ Running | 6380 |
| qdrant | ✅ Running | 6333 |

## Application
| Service | Status | Port | PID |
|---------|--------|------|-----|
| Backend | ✅ Running | 8100 | 12345 |
| Frontend | ✅ Running | 3100 | 12346 |

## Health Check
- Backend API: ✅ http://localhost:8100/health
- Frontend: ✅ http://localhost:3100
```
