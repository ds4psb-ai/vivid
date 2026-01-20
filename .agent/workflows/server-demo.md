---
description: Vivid 투자자 데모용 서버 실행 (포트 8100/3100, 시드된 데모 IP 사용)
---

# Vivid Demo Server (투자자 데모용)

// turbo-all

> **포트**: Backend 8100, Frontend 3100
> **용도**: 투자자 데모용 서버 (DB에 시드된 데모 IP 사용)

이 워크플로우는 DB에 시드된 데모 IP를 사용하여 실제 API가 동작하는 데모 환경을 실행합니다.
- `umbrella-encounter`: 9:16 세로형 숏폼 웹드라마
- `cooking-anime-mv`: 16:9 가로형 애니메이션 MV

## 1. Docker 서비스 확인 및 시작
```bash
colima status 2>/dev/null || colima start
docker start crebit-postgres crebit-redis crebit-qdrant 2>/dev/null || docker-compose -f /Users/ted/vivid/docker-compose.yml up -d
sleep 3
```

## 2. 백엔드 서버 시작
```bash
pkill -f "uvicorn.*vivid" 2>/dev/null || true
lsof -ti :8100 | xargs -r kill -9 2>/dev/null || true
sleep 1
cd /Users/ted/vivid/backend && source venv/bin/activate && nohup uvicorn app.main:app --host 0.0.0.0 --port 8100 --reload > /tmp/vivid-backend.log 2>&1 &
echo "Backend starting... (PID: $!)"
```

## 3. 백엔드 Health Check
```bash
for i in {1..12}; do
    if curl -s http://localhost:8100/health > /dev/null 2>&1; then
        echo "✅ Backend (8100): healthy"
        break
    fi
    [ $i -eq 12 ] && echo "❌ Backend (8100): failed - check /tmp/vivid-backend.log"
    sleep 1
done
```

## 4. 프론트엔드 서버 시작
```bash
# 기존 프로세스 강제 종료
pkill -9 -f "bun.*vivid" 2>/dev/null || true
pkill -9 -f "next.*vivid" 2>/dev/null || true
lsof -ti :3100 | xargs -r kill -9 2>/dev/null || true

# Next.js lock 파일 정리 (중요!)
rm -rf /Users/ted/vivid/frontend/.next/dev/lock 2>/dev/null || true

sleep 1
cd /Users/ted/vivid/frontend && nohup bun run dev > /tmp/vivid-frontend.log 2>&1 &
echo "Frontend starting... (PID: $!)"
```

## 5. 프론트엔드 Health Check
```bash
for i in {1..15}; do
    if curl -s http://localhost:3100 > /dev/null 2>&1; then
        echo "✅ Frontend (3100): ready"
        break
    fi
    [ $i -eq 15 ] && echo "❌ Frontend (3100): failed - check /tmp/vivid-frontend.log"
    sleep 1
done
```

## 6. 데모 IP 확인 및 상태 요약
```bash
echo ""
echo "=== Vivid Demo Server Status ==="
curl -s http://localhost:8100/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"Backend: {d['status']} (DB: {d['checks']['database']['status']})\")" 2>/dev/null || echo "Backend: ❌ not responding"
curl -s http://localhost:8100/api/v1/ip/catalog/umbrella-encounter | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"  → umbrella-encounter: ✅ {d['name_ko']}\")" 2>/dev/null || echo "  → umbrella-encounter: ❌ not found"
curl -s http://localhost:8100/api/v1/ip/catalog/cooking-anime-mv | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"  → cooking-anime-mv: ✅ {d['name_ko']}\")" 2>/dev/null || echo "  → cooking-anime-mv: ❌ not found"
curl -s -o /dev/null -w "Frontend: HTTP %{http_code}\n" http://localhost:3100/
echo ""
echo "📌 Demo URL: http://localhost:3100"
echo "📌 Demo IPs: /ip/umbrella-encounter, /ip/cooking-anime-mv"
echo "📌 Logs: /tmp/vivid-backend.log, /tmp/vivid-frontend.log"
```

## 참고사항
- DB에 시드된 demo IP 사용 (Option B)
- 시드 스크립트: `backend/scripts/seed_demo_ips.py`
- 비디오/썸네일: `frontend/public/demo-video/`
- 전체 서버 재시작 필요 시 `/server` 워크플로우 사용
