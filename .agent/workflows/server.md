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

## 2. Docker 컨테이너 시작 (PostgreSQL, Redis, Qdrant)
```bash
docker start crebit-postgres crebit-redis crebit-qdrant 2>/dev/null || docker-compose -f /Users/ted/vivid/docker-compose.yml up -d
```

## 3. 포트 8100 사용 프로세스 확인 및 Vivid 백엔드만 종료
```bash
# Vivid 백엔드 디렉토리에서 실행 중인 uvicorn만 종료 (다른 프로젝트 안전)
pgrep -f "uvicorn.*vivid/backend" | xargs -r kill 2>/dev/null || echo "No existing Vivid backend process"
```

## 4. 백엔드 서버 시작 (포트 8100)
```bash
cd /Users/ted/vivid/backend && source venv/bin/activate && nohup uvicorn app.main:app --host 0.0.0.0 --port 8100 --reload > /tmp/vivid-backend.log 2>&1 &
```

## 5. 백엔드 서버 확인 (2초 대기 + 재시도)
```bash
sleep 2 && curl -s -o /dev/null -w "Backend (8100): HTTP %{http_code}\n" http://localhost:8100/ || (sleep 1 && curl -s -o /dev/null -w "Backend (8100): HTTP %{http_code} (retry)\n" http://localhost:8100/) || echo "Backend: Failed to connect"
```

## 6. 포트 3100 Vivid 프론트엔드 확인/시작 (Bun 사용)
```bash
# 1. 포트 3100 점유 프로세스 확인 - Vivid 프로젝트만 종료
if lsof -i :3100 > /dev/null 2>&1; then
    PIDS=$(lsof -ti :3100 2>/dev/null)
    for PID in $PIDS; do
        # /Users/ted/vivid 경로에서 실행 중인 프로세스인지 확인
        PROC_CWD=$(lsof -p $PID 2>/dev/null | grep cwd | awk '{print $9}')
        if [[ "$PROC_CWD" == *"/Users/ted/vivid"* ]]; then
            echo "Stopping Vivid frontend (PID: $PID)..."
            kill $PID 2>/dev/null
        else
            CMD=$(ps -p $PID -o command= 2>/dev/null)
            # bun 또는 next가 vivid 경로에서 실행 중인지 추가 확인
            if [[ "$CMD" == *"vivid"* ]] || [[ "$CMD" == *"/Users/ted/vivid"* ]]; then
                echo "Stopping Vivid frontend (PID: $PID)..."
                kill $PID 2>/dev/null
            fi
        fi
    done
fi

# 2. Vivid 프론트엔드 시작 (Bun 사용)
cd /Users/ted/vivid/frontend && nohup bun run dev > /tmp/vivid-frontend.log 2>&1 &
```

## 7. 전체 상태 확인 (3초 대기 - Bun 빠름)
```bash
sleep 3 && echo "=== Vivid Server Status ===" && \
curl -s -o /dev/null -w "Backend (8100): HTTP %{http_code}\n" http://localhost:8100/ && \
curl -s -o /dev/null -w "Frontend (3100): HTTP %{http_code}\n" http://localhost:3100/ && \
curl -s -o /dev/null -w "Qdrant (6333): HTTP %{http_code}\n" http://localhost:6333/ 2>/dev/null || true
```

## 참고사항
- 이 워크플로우는 `/Users/ted/vivid` 경로의 프로세스만 대상으로 합니다
- 다른 프로젝트의 동일 포트 사용 시 충돌 방지를 위해 Vivid 프로세스만 종료합니다
- Frontend는 **Bun** 사용 (`bun run dev`)
- 로그 위치: `/tmp/vivid-backend.log`, `/tmp/vivid-frontend.log`
- **Qdrant 없이도 서버 정상 동작** (RAG 기능만 비활성화됨)
