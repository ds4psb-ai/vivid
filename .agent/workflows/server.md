---
description: Vivid 백엔드/프론트엔드 서버 시작 또는 재시작
---

# Vivid 서버 시작/재시작

// turbo-all

> **포트**: Backend 8100, Frontend 3100
> **대상**: /Users/ted/vivid 프로젝트만

## 1. Colima (Docker) 상태 확인 및 시작
```bash
colima status 2>/dev/null || colima start
```

## 2. Docker 컨테이너 시작 (PostgreSQL, Redis)
```bash
docker start crebit-postgres crebit-redis 2>/dev/null || echo "Containers started or already running"
```

## 3. 포트 8100 사용 프로세스 확인 및 Vivid 백엔드만 종료
```bash
# Vivid 백엔드 디렉토리에서 실행 중인 uvicorn만 종료 (다른 프로젝트 안전)
pgrep -f "uvicorn.*vivid/backend" | xargs -r kill 2>/dev/null || echo "No existing Vivid backend process"
```

## 4. 백엔드 서버 시작 (포트 8100)
```bash
cd /Users/ted/vivid/backend && source .venv/bin/activate && nohup uvicorn app.main:app --host 0.0.0.0 --port 8100 --reload > /tmp/vivid-backend.log 2>&1 &
```

## 5. 백엔드 서버 확인 (3초 대기 후)
```bash
sleep 3 && curl -s -o /dev/null -w "Backend (8100): HTTP %{http_code}\n" http://localhost:8100/ || echo "Backend: Failed to connect"
```

## 6. 포트 3100 Vivid 프론트엔드 확인/시작
```bash
# 3100 포트에서 실행 중인 프로세스가 Vivid인지 확인 후 시작
(lsof -i :3100 | grep -q "node.*vivid" && echo "Frontend already running") || \
(pgrep -f "next.*vivid" | xargs -r kill 2>/dev/null; cd /Users/ted/vivid/frontend && nohup npm run dev > /tmp/vivid-frontend.log 2>&1 &)
```

## 7. 전체 상태 확인
```bash
sleep 2 && echo "=== Vivid Server Status ===" && \
curl -s -o /dev/null -w "Backend (8100): HTTP %{http_code}\n" http://localhost:8100/ && \
curl -s -o /dev/null -w "Frontend (3100): HTTP %{http_code}\n" http://localhost:3100/
```

## 참고사항
- 이 워크플로우는 `/Users/ted/vivid` 경로의 프로세스만 대상으로 합니다
- 다른 프로젝트의 동일 포트 사용 시 충돌 방지를 위해 Vivid 프로세스만 종료합니다
- 로그 위치: `/tmp/vivid-backend.log`, `/tmp/vivid-frontend.log`
