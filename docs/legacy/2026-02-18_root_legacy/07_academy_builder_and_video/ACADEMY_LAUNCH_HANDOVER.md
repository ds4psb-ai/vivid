# Academy 런칭 핸드오버 문서

> 작성: 2026-02-06 03:55 KST
> 상태: 배포 진행 중

---

## 완료된 작업

### 1. P0 핫픽스 - 로그인 시 owner_id 자동 연결 ✅

**파일**: `backend/app/routers/auth.py` (라인 212-222)

```python
# 로그인 시 crebit_applications와 자동 연결 (email 매칭)
app_result = await db.execute(
    select(CrebitApplication)
    .where(CrebitApplication.email == email.lower())
    .where(CrebitApplication.owner_id.is_(None))
)
pending_application = app_result.scalar_one_or_none()
if pending_application:
    pending_application.owner_id = account.user_id
    await db.commit()
```

**커밋**: `3f208c40` - fix(academy): 로그인 시 crebit_applications email 매칭으로 owner_id 자동 연결

### 2. 전역 에러 바운더리 추가 ✅

**파일**: `frontend/src/app/error.tsx`

**커밋**: `d897a5a3` - feat(academy): 전역 에러 바운더리 추가

### 3. 테스트 확인 ✅

- Backend: **3477 passed**, 29 skipped
- Frontend: **빌드 성공**

### 4. DB 테스트 수강생 확인 ✅

```
ds4psb@gmail.com | status=paid | cohort=1기 | owner_id=None
```

핫픽스 적용 후 로그인하면 자동으로 owner_id 연결됨

---

## 배포 상태

### Vercel (Frontend) ✅

- **배포 ID**: `dpl_6ctXCzkXkS9EeyybsRWfPF6LNTBw`
- **상태**: INITIALIZING → 빌드 중
- **URL**: https://prompty.co.kr

### Railway (Backend) ⏳

- **배포 ID**: `6d76438f-fbaf-4c0d-ab49-65f05661a5ea`
- **상태**: BUILDING (03:52 시작)
- **빌드 로그**: https://railway.com/project/f1cae798-d860-4817-a48c-047d885e4228/service/74b07bc1-f3f1-492e-af77-1e3e664572b9?id=6d76438f-fbaf-4c0d-ab49-65f05661a5ea

---

## 아침에 확인할 것

### 1. 배포 상태 확인

```bash
# Railway
railway deployment list | head -5

# 예상 결과: 6d76438f... | SUCCESS
```

### 2. 헬스체크

```bash
curl https://api.prompty.co.kr/health
curl https://prompty.co.kr
```

### 3. E2E 테스트 (수동)

1. https://prompty.co.kr 접속
2. 미로그인 상태: EnrollmentRequired 표시 확인
3. ds4psb@gmail.com 으로 Google 로그인
4. Academy 콘텐츠 표시 확인 (수강생 모드)
5. 로그아웃 버튼 동작 확인

### 4. DB 확인 (로그인 후)

```bash
cd backend && source venv/bin/activate && python -c "
from sqlalchemy import create_engine, text
engine = create_engine('postgresql://crebit_user:crebit_dev_only@localhost:5433/crebit_canvas')
with engine.connect() as conn:
    result = conn.execute(text('SELECT email, owner_id, status FROM crebit_applications'))
    for row in result:
        print(row)
"
```

**예상**: ds4psb@gmail.com의 owner_id가 UUID로 채워져 있어야 함

---

## 배포 실패 시 조치

### Railway 실패 시

```bash
# 1. 로그 확인
railway logs | grep -i error | head -30

# 2. backend 폴더에서 재배포
cd /Users/ted/vivid/backend && railway up --service vivid --detach
```

### OTEL 에러 (무시해도 됨)

```
Transient error StatusCode.UNAVAILABLE encountered while exporting traces to localhost:4317
```

이건 OpenTelemetry collector가 없어서 나는 경고. 배포 실패 원인 아님.

**영구 수정하려면**: Railway 환경변수에 `OTEL_SDK_DISABLED=true` 추가

---

## 남은 작업 (P1 - 런칭 후)

| 항목 | 상태 |
|------|------|
| 모바일 네비게이션 (Hamburger 메뉴) | 미완료 |
| 접근성 개선 (aria-label) | 미완료 |
| 로그아웃 토큰 블랙리스트 | 미완료 |

---

## Git 상태

```
Branch: main
Latest commit: d897a5a3
Pushed: ✅
```

---

## 연락처

문제 발생 시 Railway/Vercel 대시보드 확인:
- Railway: https://railway.com/dashboard
- Vercel: https://vercel.com/dashboard
