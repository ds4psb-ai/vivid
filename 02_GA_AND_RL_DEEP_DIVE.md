# GA & RL Deep Dive (2025-12 정본)

**작성**: 2025-12-24  
**대상**: ML Engineer / Data Scientist  
**목표**: 스펙 최적화 로직의 구현 기준 명확화  

---

## 1) Genetic Algorithm (GA) 설계

### 1.1 유전자 표현

```
Gene = 영상 스펙 파라미터
예: hue, saturation, tempo, camera_angle, pacing, cut_duration
```

### 1.2 적합도(Fitness)

- **거장 스타일 유사도** (30)
- **감정 일관성** (30)
- **기술적 완성도** (20)
- **창의성/차별성** (20)
- **패턴 증거 점수** (Pattern Lift / Evidence Coverage)
- **비용/지연 제약** (Preview vs Final)

### 1.3 GA 프로세스

```python
population = initialize(current_spec, size=50)
for gen in range(10):
    scores = evaluate(population)
    elite = select_top(population, scores, k=5)
    offspring = crossover(elite, n=40)
    population = mutate(elite + offspring, rate=0.1)
return top_k(population, k=3)
```

### 1.4 개선 포인트 (2025)

- **Adaptive Mutation**: 세대 진행에 따른 변화 폭 감소
- **Multi-objective**: 품질 + 비용 + 생성 시간 동시 최적화
- **Early Stopping**: 개선 폭이 작으면 조기 종료

구현 노트:
- `/api/v1/spec/optimize`는 `objective`(balanced/quality/efficient/cost/latency)와 `weights`를 지원한다.
- 비용/지연은 파라미터 기반의 **complexity proxy**로 계산되며, 품질 점수와 함께 결합된다.

---

## 2) Reinforcement Learning (RL) 설계

### 2.1 목표

- 유저가 선호하는 조합을 학습해 **추천 정확도**를 높임

### 2.2 상태/행동/보상

```
State  = (emotion, color_palette, music_tempo, composition)
Action = 특정 조합 추천
Reward = 사용자 별점/선택율/완주율
```

### 2.3 Bandit + RL 혼합 전략

- **Bandit**: 즉각 반응 (실시간 추천)
- **RL**: 장기 만족도 최적화 (누적 피드백)

### 2.4 학습 루프

1. 캔버스 수정 → GA 후보 생성
2. 유저 선택/평가 로그 저장
3. Bandit 업데이트 + 주간 RL 재학습

### 2.5 데이터 전제 조건

- **Pattern Library/Trace**가 누적되어야 안정적 보상 설계 가능
- NotebookLM 결과는 **Derived**로만 사용, DB SoR에 승격된 패턴만 학습
- 모델/프롬프트 버전 고정으로 재현성 확보

---

## 3) Online + Offline 학습

- **Online**: 클릭/선택/평점 실시간 업데이트
- **Offline**: 주간 집계 → 모델 재학습
- **데이터 스냅샷**: 학습에 사용한 패턴/증거 버전 기록

---

## 4) 안전장치

- 지나치게 유사한 결과 반복 방지
- 저작권/출처 메타데이터 고려
- 낮은 품질 조합 필터링

---

## 5) 운영 지표

- 추천 채택률 (Acceptance Rate)
- 평균 품질 점수 (Avg Fitness)
- 유저 재사용률 (Retention)
- Pattern Lift 평균
- Evidence Coverage (근거 보유율)
