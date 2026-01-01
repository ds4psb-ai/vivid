---
description: Vivid 백엔드/프론트엔드 서버 시작 또는 재시작
---

# Vivid 서버 시작/재시작

// turbo-all

## 1. Colima (Docker) 상태 확인 및 시작
```bash
colima status 2>/dev/null || colima start
```

## 2. Docker 컨테이너 시작 (PostgreSQL, Redis)
```bash
docker start crebit-postgres crebit-redis 2>/dev/null || echo "Containers started or already running"
```

## 3. 기존 uvicorn 프로세스 종료 (있으면)
```bash
pkill -f "uvicorn app.main:app" 2>/dev/null || echo "No existing uvicorn process"
```

## 4. 백엔드 서버 시작 (포트 8100)
```bash
cd /Users/ted/vivid/backend && source .venv/bin/activate && nohup uvicorn app.main:app --host 0.0.0.0 --port 8100 --reload > /tmp/vivid-backend.log 2>&1 &
```

## 5. 백엔드 서버 확인 (3초 대기 후)
```bash
sleep 3 && curl -s -o /dev/null -w "Backend: HTTP %{http_code}\n" http://localhost:8100/ || echo "Backend: Failed to connect"
```

## 6. 프론트엔드 서버 확인/시작 (포트 3100)
```bash
lsof -i :3100 | grep LISTEN > /dev/null 2>&1 && echo "Frontend already running" || (cd /Users/ted/vivid/frontend && nohup npm run dev > /tmp/vivid-frontend.log 2>&1 &)
```

## 7. 전체 상태 확인
```bash
sleep 2 && echo "=== Vivid Server Status ===" && curl -s -o /dev/null -w "Backend (8100): HTTP %{http_code}\n" http://localhost:8100/ && curl -s -o /dev/null -w "Frontend (3100): HTTP %{http_code}\n" http://localhost:3100/
```
