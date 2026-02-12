# Server Command

입력: $ARGUMENTS (start, stop, restart, status — 비어있으면 start)

---

## 핵심 원칙

1. **항상 의존성 순서**: Colima → Docker containers → PostgreSQL ready → Backend → Frontend
2. **포트 충돌 자동 해결**: 시작 전 stale 프로세스 kill
3. **Health check 확인 후 완료 보고**: 추측이 아닌 실제 응답 기반

---

## 명령어 실행

### start (기본값) / restart

`restart`는 stop → start와 동일. 첫 시작이든 재시작이든 이 워크플로우를 따른다.

#### Step 1: 기존 프로세스 정리

```bash
# Backend/Frontend stale 프로세스 종료
lsof -t -i :8100 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -t -i :3100 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 1
```

#### Step 2: Docker (Colima) 확인 및 시작

```bash
# Docker 데몬 확인
docker ps > /dev/null 2>&1
```

- 성공하면 → Step 3으로
- 실패하면 → Colima 시작:

```bash
colima start  # 최대 2분 대기
```

- Colima 시작 후 `docker ps`로 재확인. 여전히 실패하면 `colima stop && colima start` 재시도.

#### Step 3: Docker 컨테이너 시작

```bash
docker-compose up -d 2>&1
```

#### Step 4: PostgreSQL 준비 대기

```bash
# 최대 30초 대기, 5초 간격 재시도
docker exec crebit-postgres pg_isready -U crebit
```

- `accepting connections` 확인될 때까지 반복 (최대 6회)
- 실패 시 `docker logs crebit-postgres --tail 20` 출력 후 중단

#### Step 5: Backend 시작 (background)

```bash
cd /Users/ted/vivid/backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8100
```

- **반드시 `run_in_background: true`로 실행** (`&` 사용 금지)
- 출력에서 `Application startup complete` 또는 `Application startup failed` 확인 (최대 20초 대기)
- 실패 시 로그 출력 후 중단

#### Step 6: Backend health check

```bash
curl -s http://localhost:8100/health
```

- `"status":"healthy"` 확인

#### Step 7: Frontend 시작 (background)

```bash
cd /Users/ted/vivid/frontend && npm run dev
```

- **반드시 `run_in_background: true`로 실행**
- `Ready in` 메시지 확인 (최대 15초 대기)

#### Step 8: 최종 상태 보고

모든 서비스 상태를 테이블로 출력:

```
| 서비스     | URL                    | 상태    |
|------------|------------------------|---------|
| Frontend   | http://localhost:3100  | Ready   |
| Backend    | http://localhost:8100  | Healthy |
| PostgreSQL | localhost:5433         | OK      |
| Redis      | localhost:6380         | OK      |
| Qdrant     | localhost:6333         | OK      |
```

---

### stop

```bash
# 1. Frontend 종료
lsof -t -i :3100 2>/dev/null | xargs kill -9 2>/dev/null || true

# 2. Backend 종료
lsof -t -i :8100 2>/dev/null | xargs kill -9 2>/dev/null || true

# 3. Docker 컨테이너 종료 (Colima는 유지)
docker-compose down
```

---

### status

상태만 확인하고 프로세스를 시작/종료하지 않는다.

```bash
# 병렬 실행:
docker-compose ps 2>&1
lsof -i :8100 -P -n 2>/dev/null | head -3
lsof -i :3100 -P -n 2>/dev/null | head -3
curl -s http://localhost:8100/health
```

결과를 테이블로 보고.

---

## 서비스 포트

| 서비스 | 포트 | 설명 |
|--------|------|------|
| Frontend | 3100 | Next.js dev server |
| Backend | 8100 | FastAPI server |
| PostgreSQL | 5433 | Database |
| Redis | 6380 | Cache/Queue |
| Qdrant | 6333 | Vector DB |

---

## 알려진 함정

| 문제 | 원인 | 해결 |
|------|------|------|
| `Address already in use` | stale 프로세스가 포트 점유 | `lsof -t -i :PORT \| xargs kill -9` |
| `Connection refused` (DB) | Docker/Colima 미실행 | Step 2부터 재시작 |
| Colima `docker.sock` 불통 | Colima 소켓 포워딩 실패 | `colima stop && colima start` |
| Backend `startup failed` | PG 아직 준비 안 됨 | `pg_isready` 대기 후 재시작 |
| OTEL 무한 재시도 hang | `OTEL_ENABLED` 미설정 | config.py에서 `OTEL_ENABLED=False` 확인 |
