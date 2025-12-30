"""
Viral Analyzer Service

Analyzes content for viral potential based on:
- Hook strength and retention prediction
- Dissonance (familiar + unexpected) detection  
- Engagement probability prediction

Philosophy:
- 바이럴은 "운"이 아니라 "설계"의 영역
- 측정되지 않으면 최적화할 수 없다
- A/B 테스트로 검증하고 개선한다

License: arkain.info@gmail.com
"""

from typing import Dict, List, Optional, Any
import logging
import re
from datetime import datetime

from app.schemas.viral_metrics import (
    HookRetentionScore,
    DissonanceScore,
    EngagementPrediction,
    ViralAnalysisReport,
    ViralPotential,
    RiskLevel,
    DissonanceType,
    calculate_viral_potential,
    get_platform_benchmark,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Keywords for Analysis
# =============================================================================

# 강한 훅 키워드
STRONG_HOOK_KEYWORDS = {
    "ko": [
        "충격", "반전", "놀라운", "믿기 힘든", "폭발", "갑자기",
        "대박", "미친", "소름", "경악", "충격적", "역대급",
        "레전드", "진짜", "실화", "ㅋㅋ", "ㅎㅎ",
    ],
    "en": [
        "shocking", "unbelievable", "insane", "crazy", "explosive",
        "sudden", "unexpected", "mind-blowing", "legendary", "epic",
        "wait for it", "you won't believe",
    ],
}

# 호기심 유발 키워드
CURIOSITY_KEYWORDS = {
    "ko": [
        "왜", "어떻게", "비밀", "진실", "숨겨진", "알고 보니",
        "사실은", "결국", "드디어", "finally",
    ],
    "en": [
        "why", "how", "secret", "truth", "hidden", "revealed",
        "actually", "finally", "turns out", "discover",
    ],
}

# 부조화 패턴 (익숙함 vs 낯섦)
DISSONANCE_PATTERNS = {
    DissonanceType.CLASS_CONTRAST: [
        (r"부자|재벌|상류층|CEO", r"가난|빈민|하층|노숙자"),
        (r"rich|wealthy|CEO|elite", r"poor|homeless|struggling"),
    ],
    DissonanceType.CHARACTER_CONTRADICTION: [
        (r"선수|운동|NBA|축구", r"요리|치킨|음식|장사"),
        (r"athlete|player|sports", r"cooking|chef|restaurant"),
    ],
    DissonanceType.SITUATION_PARADOX: [
        (r"일상|평범|보통", r"좀비|외계인|괴물|재난"),
        (r"normal|ordinary|everyday", r"zombie|alien|monster|disaster"),
    ],
    DissonanceType.TONE_SHIFT: [
        (r"코믹|웃긴|유머", r"심각|진지|어두운"),
        (r"comedy|funny|humor", r"serious|dark|dramatic"),
    ],
}


# =============================================================================
# Viral Analyzer
# =============================================================================

class ViralAnalyzer:
    """바이럴 잠재력 분석기"""
    
    def __init__(self, platform: str = "instagram"):
        self.platform = platform
        self.benchmark = get_platform_benchmark(platform)
    
    def analyze(
        self,
        shots: List[Dict[str, Any]],
        story_pitch: Optional[str] = None,
        target_emotion: Optional[str] = None,
    ) -> ViralAnalysisReport:
        """
        전체 바이럴 분석 수행
        
        Args:
            shots: 샷 계약 리스트
            story_pitch: 스토리 한 줄 피치
            target_emotion: 목표 감정
            
        Returns:
            ViralAnalysisReport
        """
        # 1. Hook 분석
        hook_retention = self.analyze_hook_strength(shots)
        
        # 2. 부조화 분석
        dissonance = None
        if story_pitch:
            dissonance = self.detect_dissonance(shots, story_pitch)
        
        # 3. 참여도 예측
        engagement = self.predict_engagement(
            shots, 
            hook_retention, 
            dissonance,
            target_emotion,
        )
        
        # 4. 종합 점수 계산
        dissonance_tension = dissonance.tension_level if dissonance else 0.5
        overall_score = self._calculate_overall_score(
            hook_retention, engagement, dissonance_tension
        )
        
        # 5. 강점/약점 분석
        strengths, weaknesses = self._analyze_strengths_weaknesses(
            hook_retention, dissonance, engagement
        )
        
        # 6. 추천 사항 생성
        recommendations = self._generate_recommendations(
            hook_retention, dissonance, engagement, weaknesses
        )
        
        # 7. A/B 테스트 제안
        ab_suggestions = self._generate_ab_suggestions(hook_retention, dissonance)
        
        return ViralAnalysisReport(
            content_id=shots[0].get("shot_id", "unknown") if shots else "unknown",
            platform=self.platform,
            analyzed_at=datetime.utcnow().isoformat(),
            hook_retention=hook_retention,
            dissonance=dissonance,
            engagement=engagement,
            overall_viral_score=overall_score,
            overall_potential=calculate_viral_potential(
                hook_retention.t_1_5s,
                engagement.engagement_score,
                dissonance_tension,
            ),
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            ab_test_suggestions=ab_suggestions,
        )
    
    def analyze_hook_strength(
        self,
        shots: List[Dict[str, Any]],
    ) -> HookRetentionScore:
        """훅 강도 및 잔존율 예측"""
        
        if not shots:
            return HookRetentionScore(
                t_1_5s=0.3,
                t_3s=0.2,
                t_10s=0.1,
                hook_strength="weak",
                drop_off_reason="샷 없음",
            )
        
        # 첫 샷(들) 분석
        first_shots = shots[:2]  # 처음 2개 샷
        hook_score = 0.5
        tips = []
        
        for shot in first_shots:
            prompt = shot.get("prompt", "")
            
            # 강한 훅 키워드 체크
            for kw in STRONG_HOOK_KEYWORDS["ko"] + STRONG_HOOK_KEYWORDS["en"]:
                if kw.lower() in prompt.lower():
                    hook_score += 0.1
            
            # 호기심 키워드 체크
            for kw in CURIOSITY_KEYWORDS["ko"] + CURIOSITY_KEYWORDS["en"]:
                if kw.lower() in prompt.lower():
                    hook_score += 0.05
            
            # 시각적 강도 체크
            visual_intensity_keywords = ["wide shot", "close-up", "dramatic", "explosive", "빠른", "강렬"]
            for kw in visual_intensity_keywords:
                if kw.lower() in prompt.lower():
                    hook_score += 0.05
        
        hook_score = min(1.0, hook_score)
        
        # 잔존율 예측 (훅 강도 기반)
        t_1_5s = min(0.95, 0.4 + hook_score * 0.5)
        t_3s = t_1_5s * 0.85
        t_10s = t_3s * 0.75
        
        # 훅 강도 분류
        if hook_score >= 0.8:
            strength = "explosive"
        elif hook_score >= 0.6:
            strength = "strong"
        elif hook_score >= 0.4:
            strength = "moderate"
        else:
            strength = "weak"
            tips.append("💡 첫 샷에 더 강렬한 시각적 요소를 추가하세요")
            tips.append("💡 호기심을 유발하는 질문이나 반전을 넣어보세요")
        
        # 이탈 원인 분석
        drop_off_reason = None
        if hook_score < 0.5:
            drop_off_reason = "훅이 약함 - 시작이 평이함"
        elif t_10s < 0.3:
            drop_off_reason = "10초 전 이탈 가능 - 전개가 느림"
        
        return HookRetentionScore(
            t_1_5s=round(t_1_5s, 3),
            t_3s=round(t_3s, 3),
            t_10s=round(t_10s, 3),
            hook_strength=strength,
            drop_off_reason=drop_off_reason,
            improvement_tips=tips,
        )
    
    def detect_dissonance(
        self,
        shots: List[Dict[str, Any]],
        story_pitch: str,
    ) -> Optional[DissonanceScore]:
        """부조화 요소 탐지"""
        
        # 전체 텍스트 수집
        all_text = story_pitch + " " + " ".join(
            shot.get("prompt", "") for shot in shots
        )
        
        # 부조화 패턴 매칭
        detected_type = None
        familiar = None
        unexpected = None
        
        for dissonance_type, patterns in DISSONANCE_PATTERNS.items():
            for pattern_pair in patterns:
                familiar_pattern, unexpected_pattern = pattern_pair
                familiar_match = re.search(familiar_pattern, all_text, re.IGNORECASE)
                unexpected_match = re.search(unexpected_pattern, all_text, re.IGNORECASE)
                
                if familiar_match and unexpected_match:
                    detected_type = dissonance_type
                    familiar = familiar_match.group()
                    unexpected = unexpected_match.group()
                    break
            if detected_type:
                break
        
        if not detected_type:
            # 기본값 반환 (부조화 없음)
            return DissonanceScore(
                familiar_element="일반적 상황",
                unexpected_element="특별한 요소 없음",
                dissonance_type=DissonanceType.SITUATION_PARADOX,
                tension_level=0.3,
                curiosity_level=0.3,
                risk_level=RiskLevel.SAFE,
                predicted_effect="평범한 반응",
            )
        
        # 긴장도 계산
        tension = 0.6  # 부조화 발견 시 기본값
        curiosity = 0.7
        
        # 유형별 조정
        if detected_type == DissonanceType.CLASS_CONTRAST:
            tension = 0.8
            curiosity = 0.75
        elif detected_type == DissonanceType.CHARACTER_CONTRADICTION:
            tension = 0.7
            curiosity = 0.85
        elif detected_type == DissonanceType.TONE_SHIFT:
            tension = 0.65
            curiosity = 0.6
        
        # 리스크 평가
        risk = RiskLevel.MODERATE
        risk_factors = []
        
        if tension > 0.8:
            risk = RiskLevel.BOLD
            risk_factors.append("강한 부조화 - 일부 시청자에게 불편할 수 있음")
        
        return DissonanceScore(
            familiar_element=familiar,
            unexpected_element=unexpected,
            dissonance_type=detected_type,
            tension_level=round(tension, 2),
            curiosity_level=round(curiosity, 2),
            risk_level=risk,
            risk_factors=risk_factors,
            predicted_effect="호기심 유발" if curiosity > 0.6 else "흥미 유발",
        )
    
    def predict_engagement(
        self,
        shots: List[Dict[str, Any]],
        hook_retention: HookRetentionScore,
        dissonance: Optional[DissonanceScore],
        target_emotion: Optional[str] = None,
    ) -> EngagementPrediction:
        """참여도 예측"""
        
        # 기본값
        share = 0.02
        save = 0.04
        comment = 0.03
        like = 0.10
        
        # Hook 강도 반영
        if hook_retention.hook_strength == "explosive":
            share *= 2.5
            save *= 2.0
            comment *= 2.0
        elif hook_retention.hook_strength == "strong":
            share *= 1.8
            save *= 1.5
            comment *= 1.5
        
        # 부조화 반영
        if dissonance and dissonance.tension_level > 0.5:
            share *= 1.0 + dissonance.tension_level
            comment *= 1.0 + dissonance.curiosity_level
        
        # 감정 반영
        if target_emotion:
            emotion_lower = target_emotion.lower()
            if emotion_lower in ["놀람", "충격", "surprise", "shock"]:
                share *= 1.5
            elif emotion_lower in ["웃음", "유머", "funny", "humor"]:
                share *= 1.3
                comment *= 1.4
            elif emotion_lower in ["감동", "눈물", "emotional", "touching"]:
                save *= 1.5
        
        # 범위 제한
        share = min(0.15, share)
        save = min(0.20, save)
        comment = min(0.15, comment)
        like = min(0.30, like)
        
        # 종합 점수
        engagement_score = (share * 0.3 + save * 0.3 + comment * 0.2 + like * 0.2) * 10
        engagement_score = min(1.0, engagement_score)
        
        # 바이럴 잠재력
        if engagement_score >= 0.7:
            potential = ViralPotential.VIRAL
        elif engagement_score >= 0.5:
            potential = ViralPotential.HIGH
        elif engagement_score >= 0.3:
            potential = ViralPotential.MODERATE
        else:
            potential = ViralPotential.LOW
        
        return EngagementPrediction(
            share_probability=round(share, 4),
            save_probability=round(save, 4),
            comment_probability=round(comment, 4),
            like_probability=round(like, 4),
            engagement_score=round(engagement_score, 3),
            viral_potential=potential,
            likely_comment_themes=self._predict_comment_themes(target_emotion, dissonance),
            best_fit_audience=self._predict_audience(shots, target_emotion),
        )
    
    def _calculate_overall_score(
        self,
        hook_retention: HookRetentionScore,
        engagement: EngagementPrediction,
        dissonance_tension: float,
    ) -> float:
        """종합 바이럴 점수 계산"""
        return round(
            hook_retention.t_1_5s * 0.35 +
            engagement.engagement_score * 0.40 +
            dissonance_tension * 0.25,
            3
        )
    
    def _analyze_strengths_weaknesses(
        self,
        hook: HookRetentionScore,
        dissonance: Optional[DissonanceScore],
        engagement: EngagementPrediction,
    ) -> tuple:
        """강점/약점 분석"""
        strengths = []
        weaknesses = []
        
        # Hook 분석
        if hook.hook_strength in ["strong", "explosive"]:
            strengths.append(f"🔥 강력한 훅 ({hook.hook_strength})")
        else:
            weaknesses.append("⚠️ 훅이 약함 - 시작을 강화하세요")
        
        # 잔존율 분석
        if hook.t_1_5s >= self.benchmark.avg_retention_1_5s:
            strengths.append(f"✅ 1.5초 잔존율 우수 ({hook.t_1_5s:.0%})")
        else:
            weaknesses.append(f"📉 1.5초 잔존율 저조 ({hook.t_1_5s:.0%} < 기준 {self.benchmark.avg_retention_1_5s:.0%})")
        
        # 부조화 분석
        if dissonance and dissonance.tension_level > 0.5:
            strengths.append(f"🎭 효과적인 부조화 감지 ({dissonance.dissonance_type.value})")
        else:
            weaknesses.append("💡 부조화 요소 부족 - 익숙함+낯섦 조합을 고려하세요")
        
        # 참여도 분석
        if engagement.viral_potential in [ViralPotential.HIGH, ViralPotential.VIRAL]:
            strengths.append(f"🚀 높은 바이럴 잠재력 ({engagement.viral_potential.value})")
        
        return strengths, weaknesses
    
    def _generate_recommendations(
        self,
        hook: HookRetentionScore,
        dissonance: Optional[DissonanceScore],
        engagement: EngagementPrediction,
        weaknesses: List[str],
    ) -> List[str]:
        """개선 추천 생성"""
        recs = []
        
        if hook.hook_strength in ["weak", "moderate"]:
            recs.append("💡 첫 1.5초에 시각적 충격 요소 추가 (클로즈업, 빠른 움직임)")
            recs.append("💡 호기심 유발 질문이나 미스터리 요소로 시작")
        
        if hook.improvement_tips:
            recs.extend(hook.improvement_tips)
        
        if not dissonance or dissonance.tension_level < 0.5:
            recs.append("🎭 익숙한 요소 + 예상치 못한 반전 조합 시도")
        
        if engagement.share_probability < 0.03:
            recs.append("📤 공유하고 싶은 '와' 포인트 추가")
        
        return recs[:5]  # 최대 5개
    
    def _generate_ab_suggestions(
        self,
        hook: HookRetentionScore,
        dissonance: Optional[DissonanceScore],
    ) -> List[str]:
        """A/B 테스트 제안 생성"""
        suggestions = []
        
        suggestions.append("🅰️ vs 🅱️ 훅 변형: 충격형 vs 호기심형")
        
        if hook.hook_strength != "explosive":
            suggestions.append("🅰️ vs 🅱️ 첫 샷: 와이드 vs 클로즈업")
        
        if dissonance:
            suggestions.append(f"🅰️ vs 🅱️ 부조화 강도: {dissonance.tension_level:.0%} vs {min(1.0, dissonance.tension_level + 0.2):.0%}")
        
        suggestions.append("🅰️ vs 🅱️ 템포: 빠른 컷 vs 여유로운 빌드업")
        
        return suggestions[:4]
    
    def _predict_comment_themes(
        self,
        target_emotion: Optional[str],
        dissonance: Optional[DissonanceScore],
    ) -> List[str]:
        """예상 댓글 주제"""
        themes = []
        
        if target_emotion:
            emotion_lower = target_emotion.lower()
            if "웃" in emotion_lower or "funny" in emotion_lower:
                themes.extend(["웃음 반응", "ㅋㅋㅋ"])
            if "놀" in emotion_lower or "shock" in emotion_lower:
                themes.extend(["충격 반응", "대박"])
            if "감동" in emotion_lower or "touch" in emotion_lower:
                themes.extend(["공감", "눈물"])
        
        if dissonance and dissonance.tension_level > 0.6:
            themes.append("논란 가능성")
        
        return themes[:4] if themes else ["일반 반응"]
    
    def _predict_audience(
        self,
        shots: List[Dict[str, Any]],
        target_emotion: Optional[str],
    ) -> List[str]:
        """타겟 오디언스 예측"""
        # 간단한 휴리스틱
        return ["MZ세대", "SNS 사용자", "숏폼 소비자"]


# =============================================================================
# Factory Function
# =============================================================================

def analyze_viral_potential(
    shots: List[Dict[str, Any]],
    story_pitch: Optional[str] = None,
    target_emotion: Optional[str] = None,
    platform: str = "instagram",
) -> ViralAnalysisReport:
    """
    바이럴 잠재력 분석 (편의 함수)
    
    사용 예:
    ```python
    report = analyze_viral_potential(
        shots=shot_contracts,
        story_pitch="NBA 스타가 치킨집을 차린다",
        target_emotion="놀람",
        platform="instagram",
    )
    print(f"바이럴 점수: {report.overall_viral_score}")
    print(f"잠재력: {report.overall_potential}")
    ```
    """
    analyzer = ViralAnalyzer(platform=platform)
    return analyzer.analyze(shots, story_pitch, target_emotion)
