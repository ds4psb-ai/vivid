# AI Auteur Persona Mapping

> **목적**: 법적 안전성을 위한 실제 감독 이름 → AI 페르소나 매핑 표
> **마지막 업데이트**: 2026-01-26

---

## 🎬 매핑 테이블

| Key | 원본 감독 | AI 페르소나 (EN) | AI 페르소나 (KR) | 스타일 특징 |
|-----|-----------|------------------|------------------|-------------|
| `kang` | 봉준호 | Kang Juno | 강주노 | 계층 상징, 장르 믹싱, 계단 모티프 |
| `epoch` | Christopher Nolan | Theo Epoch | 테오 에포크 | 시간 조작, IMAX 촬영, 실용적 효과 |
| `velvet` | 왕가위 (Wong Kar-wai) | Ren Velvet | 렌 벨벳 | 네온 조명, 스텝 프린팅, 멜랑콜리 |
| `voltage` | Quentin Tarantino | Rex Voltage | 렉스 볼티지 | 챕터 구조, 긴 대화, 비선형 서사 |
| `yoon` | 박찬욱 / David Fincher | Yoon Suha | 윤수하 | 대칭 구도, 색채 코드, 복수 서사 |
| `abyss` | Denis Villeneuve | Orion Abyss | 오리온 어비스 | 광활한 공간, 미니멀 대사, 시네마틱 |
| `azure` | 신카이 마코토 | Sora Azure | 소라 아주르 | 빛 표현, 구름 묘사, 거리와 시간 |
| `prism` | Stanley Kubrick | Milo Prism | 마일로 프리즘 | 원포인트 원근법, 대칭, 롱 테이크 |
| `seoyeon` | Steven Spielberg | Min Seoyeon | 민서연 | 핸드헬드, 자연광, 긴박한 편집 |
| `nova` | Martin Scorsese | Nova Scarlet | 노바 스칼렛 | 뉴욕 거리, 음악 몽타주, 종교적 상징 |
| `cipher` | Alfred Hitchcock | Cipher Gray | 사이퍼 그레이 | 서스펜스, 관음증적 시선, 돌리 줌 |
| `legacy` | Francis Ford Coppola | Legacy Dark | 레거시 다크 | 가족 사가, 오페라틱 연출 |
| `ronin` | 구로사와 아키라 | Ronin Hayashi | 로닌 하야시 | 날씨 상징, 앙상블 연출, 휴머니즘 |

---

## 📁 코드 위치

| 파일 | 설명 |
|------|------|
| [`backend/app/services/ai/auteur_matcher.py`](file:///Users/ted/vivid/backend/app/services/ai/auteur_matcher.py) | `AUTEUR_REGISTRY` 정의 |
| [`frontend/src/constants/auteurs.ts`](file:///Users/ted/vivid/frontend/src/constants/auteurs.ts) | 프론트엔드 상수 |

---

## ⚠️ 법적 안전성 노트

- 모든 UI, 로그, API 응답에서 **AI 페르소나 이름만 사용**
- 실제 감독 이름은 내부 개발/테스트 문서에서만 참조
- 사용자에게 노출되는 모든 콘텐츠에서 가상의 AI 페르소나로 표시

---

## 🔄 변환 이력

| 날짜 | 커밋 | 설명 |
|------|------|------|
| 2026-01-26 | `abd3003d` | 초기 AI 페르소나 마이그레이션 (9개) |
| 2026-01-26 | `9138dc80` | 라우터 마운트 + validation 수정 |
| 2026-01-26 | 진행중 | 누락된 4개 페르소나 추가 (nova, cipher, legacy, ronin) |
