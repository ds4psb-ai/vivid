#!/usr/bin/env python3
"""Seed demo IPs for investor demo.

This script inserts umbrella-encounter and cooking-anime-mv into ip_catalog
with corresponding ip_rights entries.

Usage:
    cd backend && source venv/bin/activate
    python scripts/seed_demo_ips.py
"""
import asyncio
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal
from app.models_ip import IPCatalog, IPRights, IPWorkflowPreset


DEMO_IPS = [
    {
        "slug": "umbrella-encounter",
        "name_ko": "우산 속 만남",
        "name_en": "Umbrella Encounter",
        "description_ko": "빗속에서 우연히 만난 두 사람의 로맨스. 9:16 세로형 숏폼 웹드라마.",
        "description_en": "A romantic encounter between two strangers sharing an umbrella in the rain. 9:16 vertical shortform web drama.",
        "thumbnail_url": "/demo-video/umbrella-encounter-thumb.jpg",
        "banner_url": "/demo-video/umbrella-encounter-thumb.jpg",
        "genre": ["romance", "drama", "shortform"],
        "tags": ["vertical", "9:16", "demo", "rain", "romance"],
        "license_status": "allowed",
        "is_featured": True,
        "featured_order": 1,
        "worldbuilding": {
            "setting": "2024년 서울, 장마철 저녁. 을지로 골목에서 갑자기 쏟아지는 소나기.",
            "logline": "우연히 같은 우산 속에 들어간 두 사람. 비가 그치기 전, 서로의 인생이 바뀐다.",
            "characters": [
                {
                    "name": "이서연",
                    "role": "여자 주인공",
                    "age": "28세",
                    "job": "스타트업 UX 디자이너",
                    "traits": ["완벽주의", "내성적", "관찰력"],
                    "backstory": "3년간의 연애 끝에 최근 이별. 일에만 몰두하며 감정을 피해왔다."
                },
                {
                    "name": "강민재",
                    "role": "남자 주인공",
                    "age": "31세",
                    "job": "퇴사 후 첫 소설 집필 중",
                    "traits": ["자유로움", "따뜻함", "직관적"],
                    "backstory": "대기업을 그만두고 꿈을 찾아 방황 중. 우산 하나로 세상과 연결된다."
                }
            ],
            "themes": ["우연과 운명", "일상 속 로맨스", "치유와 성장"],
            "mood": "감성적, 따뜻한, 몽환적",
            "content_type": "vertical-shortform",
            "aspect_ratio": "9:16",
            "episode_count": 8,
            "episode_length": "60초"
        },
        "workflows": [
            {
                "name_ko": "캐릭터 변주",
                "name_en": "Character Variation", 
                "preset_type": "character_variation",
                "description_ko": "MBTI 등으로 캐릭터 성격을 변주합니다",
                "description_en": "Vary character personality using MBTI etc",
                "estimated_credits": 50,
                "workflow_steps": [
                    {"step": "reference_decoder", "app": "4D"},
                    {"step": "abyss_mirror", "app": "AI"},
                    {"step": "story_architect", "app": "2D"},
                    {"step": "video_maker", "app": "VEO"}
                ]
            },
            {
                "name_ko": "스타일 리믹스",
                "name_en": "Style Remix",
                "preset_type": "style_remix",
                "description_ko": "영상 스타일을 변주합니다",
                "description_en": "Remix the video style",
                "estimated_credits": 80,
                "workflow_steps": [
                    {"step": "reference_decoder", "app": "4D"},
                    {"step": "aesthetic_director", "app": "AD"},
                    {"step": "visual_realizer", "app": "3D"}
                ]
            }
        ]
    },
    {
        "slug": "cooking-anime-mv",
        "name_ko": "흑백요리사2 애니 오프닝",
        "name_en": "Cooking Anime MV",
        "description_ko": "요리 배틀 애니메이션 뮤직비디오. 16:9 가로형 MV.",
        "description_en": "Cooking battle animation music video. 16:9 horizontal MV.",
        "thumbnail_url": "/demo-video/cooking-anime-mv-thumb.jpg",
        "banner_url": "/demo-video/cooking-anime-mv-thumb.jpg",
        "genre": ["animation", "music-video", "action"],
        "tags": ["horizontal", "16:9", "demo", "anime", "cooking"],
        "license_status": "allowed",
        "is_featured": True,
        "featured_order": 2,
        "worldbuilding": {
            "setting": "2025년, 전 세계가 주목하는 요리 서바이벌 '흑백요리사' 시즌2 결승전 무대.",
            "logline": "100명의 셰프, 단 하나의 왕관. 요리로 증명하는 자존심의 전쟁.",
            "characters": [
                {
                    "name": "백승훈",
                    "role": "주인공",
                    "age": "34세",
                    "specialty": "한식 퓨전",
                    "traits": ["독창적", "끈기", "감성적"],
                    "backstory": "무명 셰프에서 SNS 바이럴로 주목받은 신예. 어머니의 레시피를 현대적으로 재해석한다."
                },
                {
                    "name": "에드워드 리",
                    "role": "최종 라이벌",
                    "age": "41세",
                    "specialty": "모던 프렌치",
                    "traits": ["완벽주의", "카리스마", "냉철함"],
                    "backstory": "미쉐린 3스타 출신. 시즌1 준우승의 설욕을 노린다."
                },
                {
                    "name": "최유나",
                    "role": "심사위원장",
                    "age": "52세",
                    "specialty": "글로벌 퓨전",
                    "traits": ["날카로움", "공정함", "따뜻한 멘토"]
                }
            ],
            "themes": ["도전과 성장", "요리의 본질", "세대를 잇는 맛"],
            "mood": "역동적, 열정적, 드라마틱",
            "content_type": "horizontal-anime-mv",
            "aspect_ratio": "16:9",
            "duration": "90초",
            "music_style": "오케스트라 + 일렉트로닉 하이브리드"
        },
        "workflows": [
            {
                "name_ko": "씬별 재생성",
                "name_en": "Scene-by-Scene Regeneration",
                "preset_type": "scene_regeneration",
                "description_ko": "각 씬을 분석하고 재생성합니다",
                "description_en": "Analyze and regenerate each scene",
                "estimated_credits": 200,
                "workflow_steps": [
                    {"step": "reference_decoder", "app": "4D"},
                    {"step": "abyss_mirror", "app": "AI"},
                    {"step": "aesthetic_director", "app": "AD"},
                    {"step": "character_consistency", "app": "VEO"},
                    {"step": "suno_bgm", "app": "SUNO"},
                    {"step": "scene_synthesis", "app": "VEO"}
                ]
            },
            {
                "name_ko": "BGM 변주",
                "name_en": "BGM Variation",
                "preset_type": "bgm_variation",
                "description_ko": "배경 음악을 새로 생성합니다",
                "description_en": "Generate new background music",
                "estimated_credits": 30,
                "workflow_steps": [
                    {"step": "reference_decoder", "app": "4D"},
                    {"step": "suno_bgm", "app": "SUNO"}
                ]
            }
        ]
    }
]


async def seed_demo_ips(session: AsyncSession) -> dict:
    """Seed demo IPs into the database."""
    created_ips = 0
    created_rights = 0
    created_presets = 0
    updated_ips = 0
    
    for ip_data in DEMO_IPS:
        # Check if IP already exists
        result = await session.execute(
            select(IPCatalog).where(IPCatalog.slug == ip_data["slug"])
        )
        existing = result.scalar_one_or_none()
        
        workflows = ip_data.pop("workflows", [])
        
        if existing:
            # Update existing IP
            for key, value in ip_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            ip_id = existing.id
            updated_ips += 1
            print(f"  Updated IP: {ip_data['slug']}")
        else:
            # Create new IP
            ip = IPCatalog(**ip_data)
            session.add(ip)
            await session.flush()
            ip_id = ip.id
            created_ips += 1
            print(f"  Created IP: {ip_data['slug']}")
        
        # Ensure IPRights exists
        rights_result = await session.execute(
            select(IPRights).where(IPRights.ip_id == ip_id)
        )
        existing_rights = rights_result.scalar_one_or_none()
        
        if not existing_rights:
            rights = IPRights(
                ip_id=ip_id,
                license_status="allowed",
                territory=[],  # worldwide
                scope="fan_creation",
                commercial_ok=False,
                license_notes="Demo IP for investor presentation"
            )
            session.add(rights)
            created_rights += 1
            print(f"    Created rights for: {ip_data['slug']}")
        
        # Create workflow presets
        for wf in workflows:
            preset_result = await session.execute(
                select(IPWorkflowPreset).where(
                    IPWorkflowPreset.ip_id == ip_id,
                    IPWorkflowPreset.preset_type == wf["preset_type"]
                )
            )
            existing_preset = preset_result.scalar_one_or_none()
            
            if not existing_preset:
                preset = IPWorkflowPreset(
                    ip_id=ip_id,
                    name_ko=wf["name_ko"],
                    name_en=wf["name_en"],
                    preset_type=wf["preset_type"],
                    description_ko=wf.get("description_ko"),
                    description_en=wf.get("description_en"),
                    estimated_credits=wf.get("estimated_credits", 50),
                    workflow_steps=wf.get("workflow_steps", []),
                    is_active=True,
                    is_featured=True
                )
                session.add(preset)
                created_presets += 1
                print(f"    Created preset: {wf['name_en']}")
    
    await session.commit()
    
    return {
        "created_ips": created_ips,
        "updated_ips": updated_ips,
        "created_rights": created_rights,
        "created_presets": created_presets
    }


async def main():
    print("🌱 Seeding demo IPs...")
    async with AsyncSessionLocal() as session:
        result = await seed_demo_ips(session)
    
    print("\n✅ Demo IP seeding complete!")
    print(f"   IPs created: {result['created_ips']}")
    print(f"   IPs updated: {result['updated_ips']}")
    print(f"   Rights created: {result['created_rights']}")
    print(f"   Presets created: {result['created_presets']}")


if __name__ == "__main__":
    asyncio.run(main())
