"""
Hook Variants Schema

Defines hook variant types for A/B testing different opening styles.
Each variant represents a different approach to the crucial 1.5 second hook.

Philosophy:
- 같은 스토리, 다른 시작
- A/B 테스트로 최적 훅 발견
- 데이터 기반 훅 최적화

License: arkain.info@gmail.com
"""

from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum


# =============================================================================
# Enums
# =============================================================================

class HookStyle(str, Enum):
    """훅 스타일 유형"""
    SHOCK = "shock"           # 충격형 - 강렬한 시각적 충격
    CURIOSITY = "curiosity"   # 호기심형 - 질문/미스터리 유발
    EMOTION = "emotion"       # 감정형 - 감정적 연결
    QUESTION = "question"     # 의문형 - 직접적 질문
    PARADOX = "paradox"       # 역설형 - 예상을 뒤집는
    TEASE = "tease"           # 티저형 - 결과 먼저 보여주기
    ACTION = "action"         # 액션형 - 바로 행동/움직임
    CALM = "calm"             # 차분형 - 여유롭게 시작 (장편용)


class HookIntensity(str, Enum):
    """훅 강도"""
    SOFT = "soft"       # 부드럽게
    MEDIUM = "medium"   # 보통
    STRONG = "strong"   # 강하게
    EXPLOSIVE = "explosive"  # 폭발적


# =============================================================================
# Hook Variant
# =============================================================================

class HookVariant(BaseModel):
    """단일 훅 변형"""
    
    variant_id: str = Field(description="변형 ID (예: 'hook_v1_shock')")
    style: HookStyle = Field(description="훅 스타일")
    intensity: HookIntensity = Field(default=HookIntensity.MEDIUM)
    
    # 프롬프트 가이드
    prompt_prefix: str = Field(
        description="샷 프롬프트 앞에 붙일 스타일 지시"
    )
    prompt_keywords: List[str] = Field(
        default_factory=list,
        description="포함할 키워드들"
    )
    
    # 시각적 지시
    visual_direction: str = Field(
        default="",
        description="시각적 연출 방향 (카메라, 조명 등)"
    )
    
    # 코칭
    coach_tip: str = Field(
        default="",
        description="이 스타일 사용 시 코칭 팁"
    )
    coach_tip_ko: Optional[str] = Field(default=None)
    
    # A/B 테스트 메타
    is_control: bool = Field(
        default=False,
        description="A/B 테스트 대조군 여부"
    )
    
    class Config:
        use_enum_values = True


class HookVariantSet(BaseModel):
    """훅 변형 세트 (A/B 테스트용)"""
    
    set_id: str = Field(description="세트 ID")
    name: str = Field(description="세트 이름 (예: '숏폼 훅 테스트 v1')")
    
    # 변형들
    variants: List[HookVariant] = Field(
        min_length=2,
        description="최소 2개 변형 (A/B)"
    )
    
    # 기본 선택
    default_variant_id: str = Field(description="기본 사용할 변형 ID")
    
    # 타겟 컨텍스트
    target_context: List[str] = Field(
        default_factory=lambda: ["shortform_start", "sequence_start"],
        description="이 세트가 적용되는 컨텍스트"
    )
    
    # 메타
    created_at: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)


# =============================================================================
# Predefined Hook Variants
# =============================================================================

HOOK_VARIANT_PRESETS: Dict[HookStyle, HookVariant] = {
    HookStyle.SHOCK: HookVariant(
        variant_id="preset_shock",
        style=HookStyle.SHOCK,
        intensity=HookIntensity.EXPLOSIVE,
        prompt_prefix="Shocking, unexpected, visually striking opening.",
        prompt_keywords=["explosion", "sudden", "dramatic", "intense", "unexpected"],
        visual_direction="극적인 클로즈업, 빠른 줌, 강한 대비",
        coach_tip="Start with the most visually striking moment",
        coach_tip_ko="가장 충격적인 순간으로 시작하세요",
    ),
    HookStyle.CURIOSITY: HookVariant(
        variant_id="preset_curiosity",
        style=HookStyle.CURIOSITY,
        intensity=HookIntensity.MEDIUM,
        prompt_prefix="Mysterious, intriguing opening that raises questions.",
        prompt_keywords=["mysterious", "hidden", "secret", "reveal", "discover"],
        visual_direction="부분만 보여주기, 미스터리한 조명, 느린 리빌",
        coach_tip="Show just enough to make them curious, not the full picture",
        coach_tip_ko="전체가 아닌 일부만 보여주어 궁금증을 유발하세요",
    ),
    HookStyle.EMOTION: HookVariant(
        variant_id="preset_emotion",
        style=HookStyle.EMOTION,
        intensity=HookIntensity.STRONG,
        prompt_prefix="Emotionally powerful, touching opening.",
        prompt_keywords=["emotional", "touching", "heartfelt", "powerful", "moving"],
        visual_direction="표정 클로즈업, 따뜻한 조명, 감정적 순간",
        coach_tip="Lead with genuine emotion that creates instant connection",
        coach_tip_ko="진정한 감정으로 즉각적 연결을 만드세요",
    ),
    HookStyle.QUESTION: HookVariant(
        variant_id="preset_question",
        style=HookStyle.QUESTION,
        intensity=HookIntensity.MEDIUM,
        prompt_prefix="Opens with a compelling question or challenge.",
        prompt_keywords=["why", "how", "what if", "imagine", "question"],
        visual_direction="텍스트 오버레이 가능, 직접적 어필",
        coach_tip="Ask a question your audience desperately wants answered",
        coach_tip_ko="시청자가 꼭 알고 싶어하는 질문을 던지세요",
    ),
    HookStyle.PARADOX: HookVariant(
        variant_id="preset_paradox",
        style=HookStyle.PARADOX,
        intensity=HookIntensity.STRONG,
        prompt_prefix="Contradictory, unexpected juxtaposition opening.",
        prompt_keywords=["contrast", "unexpected", "but", "however", "paradox"],
        visual_direction="대비되는 요소 병치, 부조화 강조",
        coach_tip="Combine familiar with unexpected for instant intrigue",
        coach_tip_ko="익숙함과 낯섦을 조합해 즉각적 흥미를 유발하세요",
    ),
    HookStyle.TEASE: HookVariant(
        variant_id="preset_tease",
        style=HookStyle.TEASE,
        intensity=HookIntensity.STRONG,
        prompt_prefix="Shows the climax/result first, then rewinds.",
        prompt_keywords=["result", "outcome", "climax", "ending", "flash forward"],
        visual_direction="결과 장면 → 페이드/글리치 → '어떻게 여기까지?'",
        coach_tip="Show the payoff first, then make them watch to understand how",
        coach_tip_ko="결과를 먼저 보여주고, 과정이 궁금하게 만드세요",
    ),
    HookStyle.ACTION: HookVariant(
        variant_id="preset_action",
        style=HookStyle.ACTION,
        intensity=HookIntensity.EXPLOSIVE,
        prompt_prefix="Starts immediately with action, no setup.",
        prompt_keywords=["action", "moving", "dynamic", "fast", "immediate"],
        visual_direction="움직임 시작, 빠른 컷, 에너지 넘침",
        coach_tip="Drop viewers directly into the action, no warm-up",
        coach_tip_ko="워밍업 없이 바로 액션 속으로 던지세요",
    ),
    HookStyle.CALM: HookVariant(
        variant_id="preset_calm",
        style=HookStyle.CALM,
        intensity=HookIntensity.SOFT,
        prompt_prefix="Begins with calm, atmospheric establishing shot.",
        prompt_keywords=["calm", "peaceful", "establishing", "atmosphere", "slow"],
        visual_direction="와이드 샷, 여유로운 페이스, 무드 빌딩",
        coach_tip="Use for longform where you have time to build atmosphere",
        coach_tip_ko="장편에서 분위기를 쌓을 시간이 있을 때 사용하세요",
    ),
}


def get_hook_variant_preset(style: HookStyle) -> HookVariant:
    """스타일별 프리셋 훅 변형 가져오기"""
    return HOOK_VARIANT_PRESETS.get(style, HOOK_VARIANT_PRESETS[HookStyle.CURIOSITY])


def create_ab_test_variants(
    base_story: str,
    styles: List[HookStyle] = None,
) -> HookVariantSet:
    """A/B 테스트용 훅 변형 세트 생성"""
    
    if styles is None:
        styles = [HookStyle.SHOCK, HookStyle.CURIOSITY, HookStyle.PARADOX]
    
    variants = []
    for i, style in enumerate(styles):
        preset = get_hook_variant_preset(style)
        variant = HookVariant(
            variant_id=f"test_{style.value}_{i}",
            style=style,
            intensity=preset.intensity,
            prompt_prefix=preset.prompt_prefix,
            prompt_keywords=preset.prompt_keywords,
            visual_direction=preset.visual_direction,
            coach_tip_ko=preset.coach_tip_ko,
            is_control=(i == 0),  # 첫 번째가 대조군
        )
        variants.append(variant)
    
    return HookVariantSet(
        set_id=f"ab_test_{len(styles)}variants",
        name=f"훅 A/B 테스트 ({len(styles)}개 변형)",
        variants=variants,
        default_variant_id=variants[0].variant_id,
        description=f"스토리: {base_story[:50]}...",
    )
