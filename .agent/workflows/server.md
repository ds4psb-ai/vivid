---
description: Vivid 백엔드/프론트엔드 서버 시작 또는 재시작
---

# Vivid 서버 시작/재시작

// turbo-all

> **포트**: Backend 8100, Frontend 3100
> **런타임**: Frontend는 Bun 사용
> **대상**: /Users/ted/vivid 프로젝트만

## 1. Colima (Docker) 상태 확인 및 시작
```bash
colima status 2>/dev/null || colima start
```

## 2. Docker 서비스 확인 및 시작 (PostgreSQL, Redis, Qdrant)
```bash
# 컨테이너가 없거나 중지되어 있으면 docker-compose up
if ! docker ps --format '{{.Names}}' | grep -q crebit-postgres; then
    docker-compose -f /Users/ted/vivid/docker-compose.yml up -d
else
    docker start crebit-postgres crebit-redis crebit-qdrant 2>/dev/null || true
fi
```

## 3. 백엔드 서버 종료 및 재시작 (강건한 버전)
```bash
# 1. 기존 Vivid 백엔드 프로세스 종료 (uvicorn vivid 또는 포트 8100)
pkill -f "uvicorn.*vivid" 2>/dev/null || true
lsof -ti :8100 | xargs -r kill -9 2>/dev/null || true
sleep 1

# 2. venv 활성화 확인 후 서버 시작
cd /Users/ted/vivid/backend
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8100 --reload > /tmp/vivid-backend.log 2>&1 &
    echo "Backend starting... (PID: $!)"
else
    echo "ERROR: venv not found at /Users/ted/vivid/backend/venv"
fi
```

## 4. 백엔드 Health Check (최대 10초 대기)
```bash
for i in {1..10}; do
    if curl -s http://localhost:8100/health > /dev/null 2>&1; then
        echo "✅ Backend (8100): healthy"
        break
    fi
    [ $i -eq 10 ] && echo "❌ Backend (8100): failed to start - check /tmp/vivid-backend.log"
    sleep 1
done
```

## 5. 프론트엔드 서버 종료 및 재시작
```bash
# 1. 기존 Vivid 프론트엔드 종료 + lock 파일 제거
pkill -9 -f "bun.*vivid" 2>/dev/null || true
pkill -9 -f "next.*vivid" 2>/dev/null || true
lsof -ti :3100 | xargs -r kill -9 2>/dev/null || true
rm -rf /Users/ted/vivid/frontend/.next/dev/lock 2>/dev/null || true
sleep 1

# 2. 프론트엔드 시작 (Bun)
cd /Users/ted/vivid/frontend && nohup bun run dev > /tmp/vivid-frontend.log 2>&1 &
echo "Frontend starting... (PID: $!)"
```

## 6. 프론트엔드 Health Check (최대 15초 대기 - 빌드 시간)
```bash
for i in {1..15}; do
    if curl -s http://localhost:3100 > /dev/null 2>&1; then
        echo "✅ Frontend (3100): ready"
        break
    fi
    [ $i -eq 15 ] && echo "❌ Frontend (3100): failed to start - check /tmp/vivid-frontend.log"
    sleep 1
done
```

## 7. 전체 상태 요약
```bash
echo ""
echo "=== Vivid Server Status ==="
curl -s http://localhost:8100/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"Backend: {d['status']} (DB: {d['checks']['database']['status']}, Redis: {d['checks']['redis']['status']})\")" 2>/dev/null || echo "Backend: ❌ not responding"
curl -s -o /dev/null -w "Frontend: HTTP %{http_code}\n" http://localhost:3100/ 2>/dev/null || echo "Frontend: ❌ not responding"
curl -s -o /dev/null -w "Qdrant: HTTP %{http_code}\n" http://localhost:6333/ 2>/dev/null || echo "Qdrant: (optional) not running"
echo ""
echo "Logs: /tmp/vivid-backend.log, /tmp/vivid-frontend.log"
```

## 참고사항
- 이 워크플로우는 `/Users/ted/vivid` 경로의 프로세스만 대상으로 합니다
- Health Check 루프로 서버 시작 완료를 확실히 확인
- `pkill` + `lsof`로 이중 종료 보장 (좀비 프로세스 방지)
- Frontend는 **Bun** 사용 (`bun run dev`)
- 로그 위치: `/tmp/vivid-backend.log`, `/tmp/vivid-frontend.log`
- **Qdrant 없이도 서버 정상 동작** (RAG 기능만 비활성화됨)
