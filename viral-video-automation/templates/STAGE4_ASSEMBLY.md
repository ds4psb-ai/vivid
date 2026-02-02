# 🎬 Stage 4: Assembly Template

> **Purpose**: 최종 영상 조립 및 마무리
> **Tools**: 편집 소프트웨어 (Premiere Pro, DaVinci, CapCut 등)

---

## 🎯 이 단계의 목표

1. 생성된 씬들을 타이밍에 맞게 조립
2. 오디오 싱크 (BGM, 효과음)
3. 컬러 그레이딩 통일
4. 최종 렌더링

---

## 📋 조립 순서

### Step 1: 타임라인 구성

```
1. 편집 소프트웨어에서 9:16 시퀀스 생성
2. selected/ 폴더의 영상들을 순서대로 배치
3. 각 씬 길이를 타임코드에 맞게 조절
```

### Step 2: 트랜지션 적용

| 전환 유형 | 사용 시점 |
|----------|----------|
| Hard Cut | 대부분의 씬 전환 |
| Dissolve | 시간 경과 표현 |
| Glitch/Datamosh | 과거→현재 전환 |

### Step 3: 오디오 작업

```
1. 원본 영상 오디오 추출 (필요시)
2. BGM 배치
3. 효과음 추가
4. 오디오 레벨 조정 (-6dB peak 권장)
```

### Step 4: 컬러 그레이딩

| Phase | 색감 |
|-------|------|
| 과거 (Scene 1-7) | Warm (3200K), 높은 Saturation |
| 현재 (Scene 9-10) | Cold (6500K), 낮은 Saturation |

### Step 5: 렌더링

| 항목 | 권장값 |
|------|--------|
| Resolution | 1080x1920 (9:16) |
| Frame Rate | 30fps |
| Codec | H.264 / HEVC |
| Bitrate | 15-25 Mbps |

---

## ✅ 최종 체크리스트

### 타이밍/편집

- [ ] 모든 씬이 타임코드에 맞게 배치됨
- [ ] 전환이 자연스러움
- [ ] 필요한 씬이 누락되지 않음

### 시각

- [ ] 씬 간 색감 일관성
- [ ] 화질 저하 없음
- [ ] 워터마크/아티팩트 없음

### 오디오

- [ ] BGM/효과음 싱크 맞음
- [ ] 오디오 레벨 적절
- [ ] 클리핑 없음

### 기술

- [ ] 올바른 해상도 (9:16)
- [ ] 충분한 비트레이트
- [ ] 파일 크기 적절

---

## 📁 최종 파일 저장

```bash
# 최종 렌더링 저장
cp ~/Desktop/final.mp4 projects/[project]/generated/videos/selected/FINAL.mp4

# 프로젝트 파일 저장 (선택)
cp ~/Documents/project.prproj projects/[project]/
```

---

## 🎉 프로젝트 완료!

```
projects/[project]/
├── generated/videos/selected/FINAL.mp4  ← 최종본
└── brief.md  ← Status: ✅ Complete
```
