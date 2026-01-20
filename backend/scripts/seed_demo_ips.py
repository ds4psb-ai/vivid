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
            "setting": "Modern Seoul, rainy day",
            "characters": [
                {"name": "주인공", "role": "protagonist", "traits": ["introspective", "kind"]},
                {"name": "상대역", "role": "love_interest", "traits": ["mysterious", "warm"]}
            ],
            "themes": ["chance encounter", "fate", "connection"],
            "content_type": "vertical-shortform",
            "aspect_ratio": "9:16"
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
            "setting": "Competitive cooking arena",
            "characters": [
                {"name": "주인공 셰프", "role": "protagonist", "traits": ["passionate", "skilled"]},
                {"name": "라이벌", "role": "rival", "traits": ["cool", "precise"]}
            ],
            "themes": ["competition", "passion", "mastery"],
            "content_type": "horizontal-anime-mv",
            "aspect_ratio": "16:9"
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
