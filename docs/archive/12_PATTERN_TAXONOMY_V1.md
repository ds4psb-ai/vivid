# Pattern Taxonomy v1 (Seed)

**작성**: 2025-12-24  
**대상**: Product / Data Curation / Engineering  
**목표**: 초기 Pattern Library에 들어갈 최소 분류/패턴명 표준화

---

## 1) 네이밍 규칙

- `snake_case` 고정
- `pattern_type`는 `hook | scene | subtitle | audio | pacing`
- 모호한 감상어 대신 **관찰 가능한 구조**로 표현

---

## 2) Seed 패턴 목록 (v1)

| pattern_name | type | description | evidence signal | notes |
| --- | --- | --- | --- | --- |
| cold_open_shock | hook | 시작 1~3초에 강한 반전/충격 제시 | 0~3초 retention 급상승 | 스포일러 최소화 |
| question_tease | hook | 질문형 내레이션/텍스트로 호기심 유도 | 3~5초 dwell 증가 | 질문은 단문 권장 |
| mismatch_situation | hook | 상황-의미 불일치로 웃음/긴장 유도 | 초반 replay 증가 | 대비가 선명해야 함 |
| countdown_promise | hook | “3가지/5초 후 공개” 구조 | 초반 completion 상승 | 숫자-약속 일치 |
| blocked_symmetry | scene | 인물/오브젝트가 대칭으로 배치된 구도 | 스틸 구간 유지율 상승 | 정면/중앙 정렬 |
| threshold_reveal | scene | 문/창/커튼 등 경계 넘어 등장 | 특정 컷 저장/공유 증가 | 진입 순간 강조 |
| micro_isolation | scene | 좁은 프레임에 단독 인물 배치 | 정서 구간 유지율 상승 | 주변 정보 최소화 |
| layered_foreground | scene | 전경-중경-후경 레이어 강조 | 시선 이동 지표 상승 | 전경 흐림 효과 |
| timed_punchline | subtitle | 컷 전환 직후 자막으로 반전 | 웃음/댓글 급증 구간 | 타이밍 0.3~0.8s |
| contrast_caption | subtitle | 자막이 화면 내용과 반대 의미 | 재시청/댓글 증가 | 과도하면 신뢰 하락 |
| karaoke_emphasis | subtitle | 키워드 단위 색/리듬 강조 | 완주율 상승 | 강조는 1~2회 |
| drop_to_silence | audio | 직전 소리 제거 후 정적 강조 | 주목/전환율 상승 | 다음 컷 대비 필요 |
| sync_hit | audio | 컷/액션과 사운드가 정확히 일치 | 공유/좋아요 증가 | 1~2회만 사용 |
| looped_motif | audio | 동일 리듬/모티프가 반복 | 브랜딩/기억 증가 | 과다 반복 주의 |
| accel_after_hook | pacing | 훅 직후 컷 전환 가속 | 중반 이탈 감소 | 과속 시 피로 증가 |
| breath_hold | pacing | 정지/고정샷으로 긴장 유지 | 긴장 구간 유지율 상승 | 1~2초 권장 |
| burst_cluster | pacing | 짧은 컷을 연속 배치 | 자극 구간 완주 상승 | 정보 과밀 주의 |
| stair_step | pacing | 점진적 속도 변화 (느림→빠름) | 클라이맥스 도달률 상승 | 계단 단계 3~4 |

---

## 3) 운영 가이드

- v1 패턴은 **시드**이며, 우선 **Pattern Candidate**에 등록
- `confidence >= 0.6` + 반복 근거 확보 시 `validated` 승격
- 표준명 충돌 시 **동의어는 description**으로만 기록

