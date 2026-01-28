"""Homepage API Router.

Endpoints for homepage data:
- GET /homepage/featured - Featured IP for hero section
- GET /homepage/characters - Characters for featured section
- GET /homepage/cinema - Cinema cards for user AI cinema
- GET /homepage/creators - Creators for human cloud CTA
- GET /homepage/variations - Dimension app variations
- GET /homepage/characters/list - Paginated character list with search/filter
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models_ip import IPCatalog
from app.models_humancloud import CreatorProfile
from app.models_singularity import BlackholeTemplate
from app.schemas.homepage_schemas import (
    FeaturedIPResponse,
    FeaturedCharacter,
    HomepageCharacter,
    CinemaCard,
    CreatorInfo,
    HomepageCreator,
    VariationCard,
    CharacterListResponse,
)

router = APIRouter(prefix="/homepage", tags=["homepage"])


# =============================================================================
# Fallback Data (used when DB is empty or for initial display)
# =============================================================================

DEFAULT_FEATURED_IP = FeaturedIPResponse(
    slug="neon-horizon",
    title="NEON",
    title_accent="HORIZON",
    description="잠들지 않는 도시에서, 이단 AI가 꿈을 꾸기 시작합니다. 당신의 기억이 지워지기 전에 합성된 진실을 밝혀내세요.",
    banner_url="https://lh3.googleusercontent.com/aida-public/AB6AXuAnK4vWkCZjrOPWwMEwuJ0km4m8lqtIFwhUKg1REgmZyY5i9xLX3f-0C3U3caIjYYL0EY7zr0_TuMwG4hSbxBUVCLDMNdm6l241-FenheSVYCdrI8w8KIeXS3v4UgTHeg9UwJiM2pBaX_Mk-IqEQuOBJv70c3nN2zf9k6Pk0XBs7VjoAFv07GZc2VxmGhNk3Y4To7R0IB9w2tyC2sMilOgnpEMAMotqozzHfufSs234LzjzB9gByd-GQiBOB0_NHW9FMlqiRwEd4RE",
    tags=["시즌 1", "2042"],
    rating=4.9,
    remix_count="12K",
    match_percent=98,
    character=FeaturedCharacter(
        name="아카리",
        description="네온 사인 아래 밤 드라이브를 즐기는 감성 AI. 도시의 불빛 속에서 당신과 함께합니다.",
        status="캐릭터 모델 준비 완료",
        image_url="https://lh3.googleusercontent.com/aida-public/AB6AXuDN5xpf62iQyVAxpu6bfMxxxUbBcRwdTWKyxVSWszsqTN31eV3lNWr3ntBTIXhAjJCKXZkUTQqa3EGMRF80TU-gL20v7zBokSFOkWBAsTDF1sbc1ZVFQ9mdz8k7yBCcSho6XXcihaNCoPVzRCdkL4NiFhZDwRx0Kz5naME5XI-yk3VW7t2C2_RlgLPW9xvZ4XUOi8L6hP4pzyuhDSqjwjDdfaFxbpEZl3dpeP0ZGPes6jLYMw8Wtgl9pUvGmoggChFffG4ovuIp3PQ",
    ),
)

DEFAULT_CHARACTERS: list[HomepageCharacter] = [
    HomepageCharacter(
        id="akari",
        name="Akari",
        image_url="https://lh3.googleusercontent.com/aida-public/AB6AXuDN5xpf62iQyVAxpu6bfMxxxUbBcRwdTWKyxVSWszsqTN31eV3lNWr3ntBTIXhAjJCKXZkUTQqa3EGMRF80TU-gL20v7zBokSFOkWBAsTDF1sbc1ZVFQ9mdz8k7yBCcSho6XXcihaNCoPVzRCdkL4NiFhZDwRx0Kz5naME5XI-yk3VW7t2C2_RlgLPW9xvZ4XUOi8L6hP4pzyuhDSqjwjDdfaFxbpEZl3dpeP0ZGPes6jLYMw8Wtgl9pUvGmoggChFffG4ovuIp3PQ",
        chat_count="12k",
        quote="오늘 밤, 네온 사인 아래서 드라이브 어때요?",
        creator="@neon_dreamer",
        badge="NEW",
        category="Cyberpunk",
    ),
    HomepageCharacter(
        id="eunha",
        name="Eunha",
        image_url="https://lh3.googleusercontent.com/aida-public/AB6AXuAEFUIE-TQP1GnONSNxQtpr031HoEzolGFK2FWaSHqPYsH6fpO5MPtnwQjO1hwcDP5jIRxRI32PLsYs0_r7616VUNOCjAblP58zu6tKWxDImRG1UFotWIZLlfdp7PizcXWOM8DzpgmawyougUuKINa34yP-SWURdtC3teIcKW4b5qZn_vK1s78Vog3DWjDnhk94JdYZlgpdJ-tY_S7h3PlNB3BQ4oKHgpzy_9bmErbhIjGQDjaHRs7DbzYv-w6FmWMvdK_VmyAZGEc",
        chat_count="8.5k",
        quote="기억은 데이터일 뿐이야, 하지만 감정은...",
        creator="@cyber_seoul",
        category="Sci-Fi",
    ),
    HomepageCharacter(
        id="soonae",
        name="순애",
        image_url="/assets/characters/candidates/pure_love.avif",
        chat_count="18k",
        quote="시간을 초월하는 순수한 사랑, 그게 나야.",
        creator="@romance_ai",
        badge="NEW",
        category="Romance",
    ),
    HomepageCharacter(
        id="koko",
        name="Koko",
        image_url="/assets/characters/candidates/koko.jpg",
        chat_count="21k",
        quote="HTML로 세상을 코딩하는 안드로이드, 반가워요!",
        creator="@android_dev",
        badge="TOP_RATED",
        category="Tech",
    ),
]

DEFAULT_CINEMA_CARDS: list[CinemaCard] = [
    CinemaCard(
        id="neon-horizon",
        title="네온 호라이즌",
        description="잠들지 않는 도시를 헤매는 안드로이드가 존재하지 않았을지도 모를 과거의 기억을 찾아 나섭니다.",
        thumbnail_url="https://lh3.googleusercontent.com/aida-public/AB6AXuAwyZBDD7Rq4xTppWZ5aAUrjShF5mzTZtow9OgCYcgGoi6u9oqfzUAbk5pl6WDXKtfDz0cFqTXEKP_NU2cmhVehZ60Hd4RQ5GXj_6xbjCi0z3Lmc-RReksa6p5UwPzdD7Ft2pvyjuAzzJYGJj5tWOlKLHx37zxy3XXdW8C-hGFVpElTQINY4MnvmuYPXHuuartUGmRuFPuFbiizvAidvlhF1Y5WTkd88CK_0eG93kKp1A9qaTSgqqjqYLcRbUS1FGlMkSqAZwq3OTw",
        duration="3:00",
        category="SHORT",
        category_color="bg-[var(--bg-primary)]",
        creator=CreatorInfo(
            name="Alex Chen",
            avatar_url="https://lh3.googleusercontent.com/aida-public/AB6AXuAihzfhGiK-cuyzA7vJ5LoaYLBNwFq9NbSV8MnnXnPBSTJ0XUOVFxAumhkmxbgCj4hsOOIShlq-BklMirnrDFvYeTvnB3PUVYLmx1lWT8zTuEA4uf4IkrxVHaLHnmrzuZVJDuP0wUmowLewq6h6_O5wuJXN4AWq2iiKk1VfwulRt0WdAN-X7cztQf_UHxYLYAg5QEuRhgMoAvRpKYCwNaXCkHnFyBAowBERxVKP441K3b-5P2142Vd1HTvNi5yNOK1cT0dcJPjt21M",
        ),
        views="12.4k",
        like_percent=98,
    ),
    CinemaCard(
        id="echoes-of-light",
        title="빛의 메아리",
        description="AI가 생성한 풍경과 신스웨이브 사운드트랙이 동기화된 추상적 시각 여행입니다.",
        thumbnail_url="https://lh3.googleusercontent.com/aida-public/AB6AXuAAHexhqEvSDEKOwXWqDlj0I2qe43rx05pv-9SDHALDu3vcE2-6-wjEIffYnmRfK22BJB-JIfAZdlB08PJCrm5aGNnbRfJf-1hISk9cUkkD36LUHXODE-0D-Pqrc1yJjb7ZgnAaGlIWlV-WiW8b9m2LbNjdkOR4Pl0kRz7uZIT-VXMgDVeHYeuxHQrdGY1JMYBYERqO5Rajtc9hpGkrphxiYvusC00q_2WD1BH520cw4qYW1PFZg5LO7zn_Z78TxwwZU4dpL0-QX38",
        duration="3:42",
        category="MUSIC VIDEO",
        category_color="bg-purple-500",
        creator=CreatorInfo(
            name="Sarah Void",
            avatar_url="https://lh3.googleusercontent.com/aida-public/AB6AXuC5QaTGBVcDFzYQmvqdFxg5zg8m7N76grsISsepxva09mAhxwyLWx9xtuTAlX5Rgu3X5zt05t2thp0sLSZUolkH-Tq9Or8bYlIDDmY6s7fFTFgEIy6u_lnBrDDSc-c68xgfCfjX3SjKQdC3CFai9FTXRaQRx39qkjsI0YaYN8_jPaOT2nxeAMsgUn1zS6Y2sHLtm7oa_YNmKKwrRMpyK96vIbkDXJO376o0-Kc4tPYcbuenE8_odv9PdmwC3wLF_Dy5w0FmwdoGNHM",
        ),
        views="8.2k",
        like_percent=95,
    ),
    CinemaCard(
        id="last-signal",
        title="마지막 신호",
        description="심우주 탐험가들이 인류의 우주에 대한 이해를 바꿀 메시지를 수신합니다.",
        thumbnail_url="https://lh3.googleusercontent.com/aida-public/AB6AXuDxZKoOnHrh27hFb_pgPcDA6fUOKEs9LFs56daf8zcRdBONS9MNs-l0SL7oqdPP6uHt6s6iTXZigBSK8ufIb3ZlHO9Y9nSwQKtGpOMF5nijYmQxlg-ahC-9n4O2hSj2e0T9FdL8kcdhoD4Yf5q96HKrYv5xCidAml-imtFxN7x33dB8qdeA2N22tD7p-AScU973ZCNEOmHF0VrGXrQO40w1U6gA_Yrk2RG0Zk-8TlNOuFQqoSAuiaE-U9h_jMcw-KB4vq4m7qFqtV8",
        duration="2:15",
        category="SCI-FI",
        category_color="bg-blue-500",
        creator=CreatorInfo(
            name="Markus R",
            avatar_url="https://lh3.googleusercontent.com/aida-public/AB6AXuC6b3ip4oErhG2Efqh1VP4CnsF8DNDXTHVDyiJbdyPkqM_1VxeXfbKPTckgY4ZmC79l8Q2QEfq2mBFpJxjI3_w77ujigw0bWEzHA0BCWXK_YAUoWcz8ew_W6cgiEBDA7hDBOrVkIRRUAou57o4XE0YPCTs8Zl2ch-vECEmpEnN6CyG1Csc2RY7_kZjpqikh1lWYmcCSle-YBZFZrwVmaNUPJKTYluiiXL0WUUrTLVJTbDj8MtEelovfcFLjEhkwNddL_Bug5Pxf8es",
        ),
        views="5.7k",
        like_percent=91,
    ),
]

DEFAULT_CREATORS: list[HomepageCreator] = [
    HomepageCreator(
        id="kim-minjun",
        initial="K",
        name="김민준",
        specialty="영상 편집",
        specialty_color="primary",
        rating=4.9,
        description="10년 경력의 시네마틱 편집 전문가입니다. SF 및 판타지 장르의 컷 편집과 색보정에 특화되어 있습니다.",
    ),
    HomepageCreator(
        id="park-seoyeon",
        initial="P",
        name="박서연",
        specialty="애니메이터",
        specialty_color="blue",
        rating=5.0,
        description="3D 캐릭터 리깅 및 모션 캡처 데이터 클린업 전문입니다. 자연스러운 움직임을 만들어 드립니다.",
    ),
    HomepageCreator(
        id="lee-jinwoo",
        initial="L",
        name="이진우",
        specialty="사운드 디자인",
        specialty_color="green",
        rating=4.8,
        description="돌비 애트모스 믹싱 및 현장감 넘치는 SFX 제작. 영상의 몰입도를 높이는 사운드스케이프를 디자인합니다.",
    ),
]

DEFAULT_VARIATIONS: list[VariationCard] = [
    VariationCard(
        id="anime-adaptation",
        name="Anime Adaptation",
        description="Reimagine the gritty streets as a high-octane anime series with vibrant color palettes.",
        thumbnail_url="https://lh3.googleusercontent.com/aida-public/AB6AXuA0r2qo4L4VmyuCId41jiXkjFCO1haV7IDSbJhzCT6sPC8I6bFdZoQ5VQLPEsgaDpW2JOJCpwKmN0UJA_6nPVGcahgFpfO173A6v14e7C8XM8-kEdxrM6gZ-TZS4TQt2a7UMte3lDWQcJqLmkD6ngyZQavT8o6TPkBBqKrIbGYOHcD-TeIJ9TEVzGHA_xBxbmGL_EG2quNe5YDycI_3U9pBrWvnSqZuWgsBM8fwrFmuTEI8Fx6RlNSom13VC6oaPwi8ZZK8ku4Ccpg",
        category="visual",
        badge="VISUAL STYLE",
        badge_color="bg-red-600",
        href="/dimension/visual-realizer",
        layout="tall",
    ),
    VariationCard(
        id="shortform-drama",
        name="Short-form Drama",
        description="Punchy 60-second vertical episodes optimized for viral social platforms.",
        thumbnail_url="https://lh3.googleusercontent.com/aida-public/AB6AXuB2tBApxBE_y5JRz_79of0LwA_koCjfEHgjOyoZf-2CVrADOm8_JKbNcctgPyf3UtxEJKmBaw3uTQvbxKjduBeL0Z6Mz43TAIAVzOd_qDFhow4m2v6SmhINvJX-47fh4Wvc0_ZBjZnIz-A5jf3Yz3eLMG3bnGw7hbkSBM-RFY59uxEaghM_I1l9Oio_CN263M4wqBXOMEWca2FWIo6VKIj-c_qJbdRoougP0LQ7Imc2xIedTOaaDUzBOsI4rYWLAlrzNUFGovWrQrM",
        category="video",
        badge="FORMAT",
        badge_color="bg-blue-600",
        href="/dimension/video-maker",
        layout="wide",
    ),
    VariationCard(
        id="interactive-game",
        name="Interactive Game",
        description="Create a branching narrative game where users can choose different paths.",
        thumbnail_url="https://lh3.googleusercontent.com/aida-public/AB6AXuCcUjKInzOtfp5cZifxh65zNNJgO0SHc3gwqrIYN83WKGibsUZxOuzS646dMw8NQYrVJeCY1iUbp-olKPlBnzlfuii2pTXStRq2-9HMGivbpfRQ92rETfQeRL5vi3w0FkA2S5g2YfjHun1F0FkcMduJY9ISG_0m7AlaTpvfn0gc_ZMn499FAUEJ1XDT_kO4H2vherED8sacBwgnPUgDFlSzUu9prPIj7Gb9-kg6tw7Jmurqtbu4lWihBv93ivATNMC135caqdvH25M",
        category="interactive",
        href="/dimension/story-architect",
        layout="normal",
    ),
    VariationCard(
        id="graphic-novel",
        name="Graphic Novel",
        description="Generate a full-color graphic novel layout with consistent character art panels.",
        thumbnail_url="https://lh3.googleusercontent.com/aida-public/AB6AXuAEjDABfWSOWoCE8z39Uf9HewzfInWI575WbW6482O4KXOTY4J6Ybhkw-yssBuKTYCIYzZP8WeUtfvQCCnfp6z7jPJblSnyIDsDGoKMtm5csZjfOkyHQr2dG_Aywxj49Dpp_f_mgb98_I5E7DTFWKX7nLFa6FH_9VYSadkBwZ0IuCNBxjWETlsCn_GrcELcuXzy3OTzT1XvbBgvCiYe9l_gSJ8GMJ2foRZh3pI6Fb5CQ5jzeWBLShpIKNYekf2x4rWV60GtVQS9yIA",
        category="story",
        href="/dimension/storyboard",
        layout="normal",
    ),
    VariationCard(
        id="3d-audio",
        name="3D Audio",
        description="Convert the script into a 3D binaural audio drama with AI voice actors.",
        thumbnail_url="https://lh3.googleusercontent.com/aida-public/AB6AXuCYZPJFPKgMSdKVU_W3iR-uzF7kSGHOsv3rhcmwdb-TRfrnJZIib_FptEDLGD6MwCRe1cIbPOoWkZhcr54lZc3bateyYL9vgzf-IudGmZv4aTceiquaSXjj8FzpR3pqqtDtPw303Kvoz__-yP3u2u3rNK2Do3dNfBPCNwlZR16hSrXOSx9VcIJJE56EUiMs1T4mJ9TDj8fQBdgLeB9MPSIbRsxzHRfZnYpzlwjn-c6q-9R2Qr8O5ncDux8qhYXzRKSiUmdtDz6RWUk",
        category="audio",
        href="/dimension/sound-crafter",
        layout="normal",
    ),
]


def _format_count(count: int) -> str:
    """Format count as human-readable string (e.g., 12k, 1.2M)."""
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    elif count >= 1_000:
        return f"{count / 1_000:.1f}k"
    return str(count)


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/featured", response_model=FeaturedIPResponse)
async def get_featured_ip(db: AsyncSession = Depends(get_db)) -> FeaturedIPResponse:
    """Get featured IP for cinematic hero section.

    Returns the highest-priority featured IP from IPCatalog.
    Falls back to default if no featured IP exists or on DB error.
    """
    try:
        stmt = (
            select(IPCatalog)
            .where(IPCatalog.is_featured == True, IPCatalog.is_active == True)
            .order_by(IPCatalog.featured_order.asc())
            .limit(1)
        )
        result = await db.execute(stmt)
        ip = result.scalar_one_or_none()
    except Exception as e:
        # Log error and return fallback
        import logging
        logging.warning(f"Failed to fetch featured IP: {e}")
        return DEFAULT_FEATURED_IP

    if not ip:
        return DEFAULT_FEATURED_IP

    # Build character info if chat is enabled
    character = None
    if ip.chat_enabled and ip.persona_prompt:
        character = FeaturedCharacter(
            name=ip.name_ko,
            description=ip.description_ko or "",
            status="캐릭터 모델 준비 완료",
            image_url=ip.thumbnail_url,
        )

    # Split title for accent effect (use name_en for title split)
    name_parts = ip.name_en.split() if ip.name_en else [ip.name_ko]
    title = name_parts[0] if name_parts else ip.name_ko
    title_accent = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

    return FeaturedIPResponse(
        slug=ip.slug,
        title=title.upper(),
        title_accent=title_accent.upper() if title_accent else "",
        description=ip.description_ko or "",
        banner_url=ip.banner_url or "",
        tags=ip.tags or [],
        rating=4.9,  # TODO: Calculate from actual ratings
        remix_count=_format_count(ip.generation_count),
        match_percent=98,  # TODO: Personalization
        character=character,
    )


@router.get("/characters", response_model=list[HomepageCharacter])
async def get_homepage_characters(
    limit: int = Query(4, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
) -> list[HomepageCharacter]:
    """Get featured characters for homepage section.

    Returns chat-enabled IPs with highest session counts.
    Falls back to defaults if no characters exist or on DB error.
    """
    try:
        stmt = (
            select(IPCatalog)
            .where(IPCatalog.chat_enabled == True, IPCatalog.is_active == True)
            .order_by(IPCatalog.chat_session_count.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        ips = result.scalars().all()
    except Exception as e:
        import logging
        logging.warning(f"Failed to fetch homepage characters: {e}")
        return DEFAULT_CHARACTERS[:limit]

    if not ips:
        return DEFAULT_CHARACTERS[:limit]

    characters = []
    for ip in ips:
        # Determine badge based on age and popularity
        badge = None
        if ip.is_featured:
            badge = "TOP_RATED"
        # TODO: Add "NEW" badge based on created_at

        characters.append(HomepageCharacter(
            id=ip.slug,
            name=ip.name_ko,
            image_url=ip.thumbnail_url or "",
            chat_count=_format_count(ip.chat_session_count),
            quote=ip.description_ko[:60] + "..." if ip.description_ko and len(ip.description_ko) > 60 else (ip.description_ko or ""),
            creator=f"@{ip.auteur_key}" if ip.auteur_key else "@crebit",
            badge=badge,
            category=ip.genre[0] if ip.genre else None,
        ))

    return characters


@router.get("/cinema", response_model=list[CinemaCard])
async def get_homepage_cinema(
    limit: int = Query(3, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
) -> list[CinemaCard]:
    """Get cinema cards for user AI cinema section.

    Returns featured blackhole templates.
    Falls back to defaults if no templates exist or on DB error.
    """
    try:
        stmt = (
            select(BlackholeTemplate)
            .where(BlackholeTemplate.is_featured == True, BlackholeTemplate.is_public == True)
            .order_by(BlackholeTemplate.use_count.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        templates = result.scalars().all()
    except Exception as e:
        import logging
        logging.warning(f"Failed to fetch homepage cinema: {e}")
        return DEFAULT_CINEMA_CARDS[:limit]

    if not templates:
        return DEFAULT_CINEMA_CARDS[:limit]

    cards = []
    for template in templates:
        # Map category to color
        category_colors = {
            "short": "bg-[var(--bg-primary)]",
            "music_video": "bg-purple-500",
            "sci-fi": "bg-blue-500",
            "drama": "bg-green-500",
        }
        category_color = category_colors.get(template.category.lower(), "bg-gray-500")

        cards.append(CinemaCard(
            id=str(template.id),
            title=template.title,
            description=template.description,
            thumbnail_url=template.thumbnail_url or "",
            duration="3:00",  # TODO: Extract from template metadata
            category=template.category.upper(),
            category_color=category_color,
            creator=CreatorInfo(
                name=template.creator_name,
                avatar_url="",  # TODO: Add avatar URL to BlackholeTemplate
            ),
            views=_format_count(template.use_count),
            like_percent=round(template.rating_avg * 20, 1) if template.rating_avg else 90,
        ))

    return cards


@router.get("/creators", response_model=list[HomepageCreator])
async def get_homepage_creators(
    limit: int = Query(3, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
) -> list[HomepageCreator]:
    """Get creators for human cloud CTA section.

    Returns verified and available creators.
    Falls back to defaults if no creators exist or on DB error.
    """
    try:
        stmt = (
            select(CreatorProfile)
            .where(CreatorProfile.is_available == True, CreatorProfile.is_verified == True)
            .order_by(CreatorProfile.avg_rating.desc().nullslast(), CreatorProfile.completed_count.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        creators = result.scalars().all()
    except Exception as e:
        import logging
        logging.warning(f"Failed to fetch homepage creators: {e}")
        return DEFAULT_CREATORS[:limit]

    if not creators:
        return DEFAULT_CREATORS[:limit]

    # Map categories to specialty colors
    specialty_colors = {
        "video_creative": "primary",
        "thumbnail": "blue",
        "short_video": "primary",
        "motion_graphic": "blue",
        "brand_video": "green",
    }

    homepage_creators = []
    for creator in creators:
        # Get primary category
        primary_category = creator.categories[0] if creator.categories else "video_creative"
        specialty_color = specialty_colors.get(primary_category, "primary")

        # Get display specialty name
        specialty_names = {
            "video_creative": "영상 편집",
            "thumbnail": "썸네일 디자인",
            "short_video": "숏폼 영상",
            "motion_graphic": "모션 그래픽",
            "brand_video": "브랜드 영상",
        }
        specialty = specialty_names.get(primary_category, "영상 편집")

        homepage_creators.append(HomepageCreator(
            id=str(creator.id),
            initial=creator.display_name[0].upper() if creator.display_name else "C",
            name=creator.display_name,
            specialty=specialty,
            specialty_color=specialty_color,
            rating=float(creator.avg_rating) if creator.avg_rating else 4.5,
            description=creator.bio or "",
        ))

    return homepage_creators


@router.get("/variations", response_model=list[VariationCard])
async def get_homepage_variations(
    sort: str = Query("popular", pattern="^(popular|new)$"),
) -> list[VariationCard]:
    """Get variation cards for bento grid.

    Returns dimension app variations (currently from static config).
    TODO: Support dynamic ordering from database.
    """
    variations = DEFAULT_VARIATIONS.copy()

    # Sort by popularity or newness
    if sort == "new":
        # Reverse order for "new" (assuming later items are newer)
        variations = list(reversed(variations))

    return variations


@router.get("/characters/list", response_model=CharacterListResponse)
async def list_characters(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> CharacterListResponse:
    """List all characters with search and filter support.

    Server-side filtering for /characters page.
    Falls back to defaults on DB error.
    """
    # Try DB query, fallback to defaults on error
    try:
        # Base query
        query = select(IPCatalog).where(IPCatalog.chat_enabled == True, IPCatalog.is_active == True)

        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    IPCatalog.name_ko.ilike(search_pattern),
                    IPCatalog.name_en.ilike(search_pattern),
                    IPCatalog.description_ko.ilike(search_pattern),
                )
            )

        # Apply category filter
        if category and category.lower() != "all":
            # Filter by genre (JSONB contains)
            query = query.where(IPCatalog.genre.contains([category]))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(IPCatalog.chat_session_count.desc()).offset(offset).limit(page_size)

        result = await db.execute(query)
        ips = result.scalars().all()
    except Exception as e:
        import logging
        logging.warning(f"Failed to fetch character list: {e}")
        # Fall through to default handling
        ips = []
        total = 0
        offset = (page - 1) * page_size

    # If no results from DB, use defaults with filtering and pagination
    if not ips:
        filtered_defaults = DEFAULT_CHARACTERS.copy()

        if search:
            search_lower = search.lower()
            filtered_defaults = [
                c for c in filtered_defaults
                if search_lower in c.name.lower() or search_lower in c.quote.lower()
            ]

        if category and category.lower() != "all":
            filtered_defaults = [
                c for c in filtered_defaults
                if c.category and c.category.lower() == category.lower()
            ]

        # Apply pagination to defaults
        total_defaults = len(filtered_defaults)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_defaults = filtered_defaults[start_idx:end_idx]

        return CharacterListResponse(
            items=paginated_defaults,
            total=total_defaults,
            page=page,
            page_size=page_size,
            has_more=end_idx < total_defaults,
        )

    # Convert to response models
    characters = []
    for ip in ips:
        badge = None
        if ip.is_featured:
            badge = "TOP_RATED"

        characters.append(HomepageCharacter(
            id=ip.slug,
            name=ip.name_ko,
            image_url=ip.thumbnail_url or "",
            chat_count=_format_count(ip.chat_session_count),
            quote=ip.description_ko[:60] + "..." if ip.description_ko and len(ip.description_ko) > 60 else (ip.description_ko or ""),
            creator=f"@{ip.auteur_key}" if ip.auteur_key else "@crebit",
            badge=badge,
            category=ip.genre[0] if ip.genre else None,
        ))

    return CharacterListResponse(
        items=characters,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(characters)) < total,
    )
