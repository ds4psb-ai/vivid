"""
TikTok Trends Crawler Job

Virlo 대체 - TikTok Creative Center에서 트렌딩 콘텐츠 발굴
→ OutlierItem 생성 → Scout Bot Telegram 알림

Usage (Arq worker):
    # worker.py에 추가
    from app.jobs.crawl_tiktok_trends import crawl_tiktok_trends
    
    # WorkerSettings.functions에 추가
    # WorkerSettings.cron_jobs에 추가 (6시간마다)
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

# K-Beauty 관련 시드 해시태그
KBEAUTY_SEED_HASHTAGS = [
    "kbeauty",
    "koreanskincare", 
    "glassskin",
    "koreanmakeup",
    "skincareroutine",
    "skincaretips",
    "skincarekorea",
    "kbeautyproducts",
    "koreanbeauty",
]

# 최소 조회수 기준 (7일)
MIN_VIEWS_7D = 1_000_000  # 100만 뷰
MIN_VIEWS_7D_OUTLIER = 10_000_000  # 1000만 뷰 → 아웃라이어


async def crawl_tiktok_trends(
    ctx: Dict[str, Any],
    seed_hashtags: List[str] = None,
    min_views: int = MIN_VIEWS_7D,
    notify_telegram: bool = True,
) -> Dict[str, Any]:
    """
    TikTok Creative Center에서 K-Beauty 트렌드 크롤링
    
    Args:
        ctx: Arq context
        seed_hashtags: 시드 해시태그 (기본값: K-Beauty 관련)
        min_views: 최소 7일 조회수
        notify_telegram: Telegram 알림 여부
        
    Returns:
        크롤링 결과 요약
    """
    from app.services.creative_center_scraper import CreativeCenterScraper
    
    if seed_hashtags is None:
        seed_hashtags = KBEAUTY_SEED_HASHTAGS
    
    logger.info(f"[Cron] crawl_tiktok_trends: seeds={seed_hashtags[:3]}...")
    
    results = {
        "status": "completed",
        "discovered_hashtags": 0,
        "outliers_found": 0,
        "outlier_items_created": 0,
        "errors": [],
    }
    
    scraper = CreativeCenterScraper()
    
    try:
        # 1. K-Beauty 해시태그 발굴
        discovered = await scraper.discover_beauty_hashtags(
            seed_hashtags=seed_hashtags,
            min_views_7d=min_views,
            max_depth=2,
        )
        results["discovered_hashtags"] = len(discovered)
        
        # 2. 아웃라이어 필터링 (10M+ views)
        outliers = [
            h for h in discovered 
            if h.video_views_7d >= MIN_VIEWS_7D_OUTLIER
        ]
        results["outliers_found"] = len(outliers)
        
        # 3. OutlierItem 생성 (DB 저장)
        if outliers:
            outlier_items = await _create_outlier_items(outliers)
            results["outlier_items_created"] = len(outlier_items)
            
            # 4. Telegram 알림
            if notify_telegram and outlier_items:
                await _send_telegram_notification(outlier_items)
        
        logger.info(
            f"[Cron] TikTok trends crawl complete: "
            f"hashtags={results['discovered_hashtags']}, "
            f"outliers={results['outliers_found']}"
        )
        
    except Exception as e:
        logger.exception(f"crawl_tiktok_trends failed: {e}")
        results["status"] = "failed"
        results["errors"].append(str(e))
        
    finally:
        await scraper.close()
    
    return results


async def _create_outlier_items(hashtags) -> List[Dict[str, Any]]:
    """
    HashtagDetails를 OutlierItem으로 변환하여 DB 저장
    """
    from app.database import AsyncSessionLocal
    from app.models_outlier import OutlierItem
    from sqlalchemy import select
    
    created = []
    
    async with AsyncSessionLocal() as db:
        for h in hashtags:
            # 중복 체크
            existing = await db.execute(
                select(OutlierItem).where(
                    OutlierItem.source_id == f"hashtag:{h.hashtag_id}"
                )
            )
            if existing.scalar_one_or_none():
                continue
            
            # OutlierItem 생성
            item = OutlierItem(
                id=uuid4(),
                source_url=f"https://www.tiktok.com/tag/{h.hashtag_name}",
                source_id=f"hashtag:{h.hashtag_id}",
                platform="tiktok",
                title=f"#{h.hashtag_name}",
                category=h.industry or "Beauty",
                analysis_status="pending",
                view_count=h.video_views_7d,
                tags=[h.hashtag_name] + [
                    r["hashtag_name"] for r in (h.related_hashtags or [])[:5]
                ],
                vdg_data={
                    "source": "creative_center",
                    "hashtag_details": {
                        "views_7d": h.video_views_7d,
                        "views_all": h.video_views_all,
                        "posts_7d": h.publish_count_7d,
                        "posts_all": h.publish_count_all,
                        "audience_ages": h.audience_ages,
                        "audience_interests": h.audience_interests,
                        "audience_countries": h.audience_countries,
                    },
                },
            )
            
            db.add(item)
            created.append({
                "id": str(item.id),
                "hashtag": h.hashtag_name,
                "views_7d": h.video_views_7d,
                "industry": h.industry,
            })
        
        await db.commit()
    
    logger.info(f"Created {len(created)} OutlierItems from hashtags")
    return created


async def _send_telegram_notification(outlier_items: List[Dict[str, Any]]):
    """
    Scout Bot Telegram 알림 전송
    """
    try:
        # TODO: 실제 Telegram Bot 연동
        # 현재는 로그만 출력
        message = "🎯 **K-Beauty Outliers Discovered!**\n\n"
        
        for item in outlier_items[:5]:
            views = item["views_7d"]
            views_str = f"{views/1_000_000:.1f}M" if views >= 1_000_000 else f"{views:,}"
            message += f"#{item['hashtag']} - {views_str} views (7d)\n"
        
        if len(outlier_items) > 5:
            message += f"\n... and {len(outlier_items) - 5} more"
        
        logger.info(f"[Telegram] Would send:\n{message}")
        
        # 실제 전송 (OpenClaw 메시지 도구 사용)
        # await send_telegram_message(message)
        
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")


# ============================================================
# Worker 등록용 (worker.py에 추가)
# ============================================================

"""
# worker.py에 추가할 내용:

from app.jobs.crawl_tiktok_trends import crawl_tiktok_trends

# WorkerSettings.functions에 추가:
functions = [
    ...existing functions...,
    crawl_tiktok_trends,
]

# WorkerSettings.cron_jobs에 추가:
cron_jobs = [
    ...existing cron jobs...,
    # K-Beauty 트렌드 크롤링 (6시간마다)
    {
        "func": crawl_tiktok_trends,
        "cron": "0 */6 * * *",  # 매 6시간 (0:00, 6:00, 12:00, 18:00)
        "unique": True,
    },
]
"""
