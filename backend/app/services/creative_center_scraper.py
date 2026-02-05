"""
TikTok Creative Center Scraper

Virlo 대체 솔루션 - TikTok Creative Center에서 트렌딩 콘텐츠 Discovery

Usage:
    from app.services.creative_center_scraper import CreativeCenterScraper
    
    scraper = CreativeCenterScraper()
    hashtags = await scraper.fetch_trending_hashtags(country="KR")
    videos = await scraper.fetch_trending_videos(country="KR")
"""

import httpx
import json
import re
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class TrendingHashtag:
    """트렌딩 해시태그 데이터"""
    hashtag_id: str
    hashtag_name: str
    rank: int
    video_views: int
    publish_count: int
    industry: Optional[str] = None
    country: Optional[str] = None
    rank_diff: Optional[int] = None
    is_promoted: bool = False
    trend_data: Optional[List[Dict]] = None


@dataclass
class TrendingVideo:
    """트렌딩 비디오 데이터"""
    video_id: str
    video_url: str
    title: Optional[str] = None
    author: Optional[str] = None
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    duration_ms: int = 0


@dataclass
class HashtagDetails:
    """해시태그 상세 정보"""
    hashtag_id: str
    hashtag_name: str
    description: Optional[str] = None
    # 7일 통계
    video_views_7d: int = 0
    publish_count_7d: int = 0
    # 전체 통계
    video_views_all: int = 0
    publish_count_all: int = 0
    # 카테고리
    industry: Optional[str] = None
    industry_id: Optional[int] = None
    # 오디언스
    audience_ages: Optional[List[Dict]] = None
    audience_interests: Optional[List[Dict]] = None
    audience_countries: Optional[List[Dict]] = None
    # 관련 해시태그
    related_hashtags: Optional[List[Dict]] = None
    # 트렌드 데이터
    trend_data: Optional[List[Dict]] = None


class CreativeCenterScraper:
    """TikTok Creative Center 스크래퍼"""
    
    BASE_URL = "https://ads.tiktok.com/business/creativecenter"
    HASHTAG_URL = f"{BASE_URL}/inspiration/popular/hashtag/pc/en"
    VIDEO_URL = f"{BASE_URL}/inspiration/popular/pc/en"
    CREATOR_URL = f"{BASE_URL}/inspiration/popular/creator/pc/en"
    MUSIC_URL = f"{BASE_URL}/inspiration/popular/music/pc/en"
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
    }
    
    # 뷰티 관련 산업 ID (Creative Center 기준)
    BEAUTY_INDUSTRY_ID = 13000000000  # Beauty & Personal Care
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """HTTP 클라이언트 가져오기 (싱글톤)"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers=self.HEADERS,
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._client
    
    async def close(self):
        """클라이언트 종료"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    def _extract_next_data(self, html: str) -> Optional[Dict[str, Any]]:
        """HTML에서 __NEXT_DATA__ JSON 추출"""
        pattern = r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse __NEXT_DATA__: {e}")
        return None
    
    def _extract_list_from_queries(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """쿼리에서 리스트 데이터 추출"""
        queries = (
            data.get("props", {})
            .get("pageProps", {})
            .get("dehydratedState", {})
            .get("queries", [])
        )
        
        for query in queries:
            state_data = query.get("state", {}).get("data", {})
            pages = state_data.get("pages", [])
            if pages and "list" in pages[0]:
                return pages[0]["list"]
        
        return []
    
    async def fetch_trending_hashtags(
        self,
        country: str = "ALL",
        industry_id: Optional[int] = None,
        limit: int = 100,
    ) -> List[TrendingHashtag]:
        """
        트렌딩 해시태그 가져오기
        
        Args:
            country: 국가 코드 (ALL, US, KR, JP 등)
            industry_id: 산업 ID (None=전체, 13000000000=뷰티)
            limit: 최대 결과 수
            
        Returns:
            TrendingHashtag 리스트
        """
        client = await self._get_client()
        
        # URL 파라미터 구성 (국가/산업 필터는 클라이언트 사이드)
        url = self.HASHTAG_URL
        
        try:
            response = await client.get(url)
            response.raise_for_status()
            
            data = self._extract_next_data(response.text)
            if not data:
                logger.warning("No __NEXT_DATA__ found in response")
                return []
            
            raw_list = self._extract_list_from_queries(data)
            hashtags = []
            
            for item in raw_list[:limit]:
                # 국가 필터
                item_country = item.get("countryInfo", {}).get("id", "ALL")
                if country != "ALL" and item_country != country:
                    continue
                
                # 산업 필터
                if industry_id:
                    item_industry_id = item.get("industryInfo", {}).get("id")
                    if item_industry_id != industry_id:
                        continue
                
                hashtag = TrendingHashtag(
                    hashtag_id=str(item.get("hashtagId", "")),
                    hashtag_name=item.get("hashtagName", ""),
                    rank=item.get("rank", 0),
                    video_views=item.get("videoViews", 0),
                    publish_count=item.get("publishCnt", 0),
                    industry=item.get("industryInfo", {}).get("value"),
                    country=item_country,
                    rank_diff=item.get("rankDiff"),
                    is_promoted=item.get("isPromoted", False),
                    trend_data=item.get("trend"),
                )
                hashtags.append(hashtag)
            
            logger.info(f"Fetched {len(hashtags)} trending hashtags")
            return hashtags
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching hashtags: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching hashtags: {e}")
            return []
    
    async def fetch_trending_videos(
        self,
        country: str = "ALL",
        min_views: int = 500_000,
        limit: int = 50,
    ) -> List[TrendingVideo]:
        """
        트렌딩 비디오 가져오기
        
        Args:
            country: 국가 코드
            min_views: 최소 조회수 필터
            limit: 최대 결과 수
            
        Returns:
            TrendingVideo 리스트
        """
        client = await self._get_client()
        
        try:
            response = await client.get(self.VIDEO_URL)
            response.raise_for_status()
            
            data = self._extract_next_data(response.text)
            if not data:
                logger.warning("No __NEXT_DATA__ found in response")
                return []
            
            raw_list = self._extract_list_from_queries(data)
            videos = []
            
            for item in raw_list[:limit]:
                view_count = item.get("playCount", 0) or item.get("videoViews", 0)
                
                # 조회수 필터
                if view_count < min_views:
                    continue
                
                video = TrendingVideo(
                    video_id=str(item.get("videoId", item.get("itemId", ""))),
                    video_url=item.get("videoUrl", item.get("url", "")),
                    title=item.get("title", item.get("videoTitle", "")),
                    author=item.get("authorName", item.get("nickName", "")),
                    view_count=view_count,
                    like_count=item.get("likeCount", item.get("diggCount", 0)),
                    comment_count=item.get("commentCount", 0),
                    share_count=item.get("shareCount", 0),
                    duration_ms=item.get("duration", 0) * 1000,
                )
                videos.append(video)
            
            logger.info(f"Fetched {len(videos)} trending videos (min {min_views} views)")
            return videos
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching videos: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching videos: {e}")
            return []
    
    async def fetch_beauty_hashtags(self, limit: int = 50) -> List[TrendingHashtag]:
        """뷰티 카테고리 해시태그만 가져오기"""
        return await self.fetch_trending_hashtags(
            industry_id=self.BEAUTY_INDUSTRY_ID,
            limit=limit,
        )
    
    async def fetch_hashtag_details(self, hashtag_name: str) -> Optional[HashtagDetails]:
        """
        특정 해시태그의 상세 정보 가져오기
        
        Args:
            hashtag_name: 해시태그 이름 (# 제외)
            
        Returns:
            HashtagDetails 또는 None
        """
        client = await self._get_client()
        url = f"{self.BASE_URL}/hashtag/{hashtag_name}/pc/en"
        
        try:
            response = await client.get(url)
            response.raise_for_status()
            
            data = self._extract_next_data(response.text)
            if not data:
                return None
            
            page_data = data.get("props", {}).get("pageProps", {}).get("data", {})
            if not page_data:
                return None
            
            # 관련 해시태그 추출
            related = page_data.get("relatedHashtags", [])
            related_list = [
                {
                    "hashtag_id": r.get("hashtagId"),
                    "hashtag_name": r.get("hashtagName"),
                    "video_url": r.get("videoUrl"),
                }
                for r in related
            ]
            
            return HashtagDetails(
                hashtag_id=str(page_data.get("hashtagId", "")),
                hashtag_name=page_data.get("hashtagName", hashtag_name),
                description=page_data.get("description"),
                video_views_7d=page_data.get("videoViews", 0),
                publish_count_7d=page_data.get("publishCnt", 0),
                video_views_all=page_data.get("videoViewsAll", 0),
                publish_count_all=page_data.get("publishCntAll", 0),
                industry=page_data.get("industryInfo", {}).get("value"),
                industry_id=page_data.get("industryInfo", {}).get("id"),
                audience_ages=page_data.get("audienceAges"),
                audience_interests=page_data.get("audienceInterests"),
                audience_countries=page_data.get("audienceCountries"),
                related_hashtags=related_list,
                trend_data=page_data.get("trend"),
            )
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching hashtag details for {hashtag_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching hashtag details for {hashtag_name}: {e}")
            return None
    
    async def discover_beauty_hashtags(
        self,
        seed_hashtags: List[str] = None,
        min_views_7d: int = 1_000_000,
        max_depth: int = 2,
    ) -> List[HashtagDetails]:
        """
        K-Beauty 관련 해시태그 발굴 (BFS 확장)
        
        Args:
            seed_hashtags: 시작 해시태그들
            min_views_7d: 7일 최소 조회수
            max_depth: 관련 해시태그 탐색 깊이
            
        Returns:
            발굴된 HashtagDetails 리스트
        """
        if seed_hashtags is None:
            seed_hashtags = [
                "kbeauty", "koreanskincare", "glassskin", 
                "koreanmakeup", "skincareroutine", "skincaretips"
            ]
        
        discovered = {}  # hashtag_name -> HashtagDetails
        to_explore = list(seed_hashtags)
        explored = set()
        current_depth = 0
        
        while to_explore and current_depth < max_depth:
            next_level = []
            
            for hashtag in to_explore:
                if hashtag in explored:
                    continue
                explored.add(hashtag)
                
                details = await self.fetch_hashtag_details(hashtag)
                if details and details.video_views_7d >= min_views_7d:
                    discovered[hashtag] = details
                    
                    # 관련 해시태그 추가
                    if details.related_hashtags:
                        for related in details.related_hashtags:
                            rel_name = related.get("hashtag_name")
                            if rel_name and rel_name not in explored:
                                next_level.append(rel_name)
            
            to_explore = next_level
            current_depth += 1
        
        logger.info(f"Discovered {len(discovered)} beauty hashtags")
        return list(discovered.values())


# ============================================================
# Celery Task Integration (Worker에 추가 필요)
# ============================================================

async def crawl_creative_center_hashtags(
    country: str = "ALL",
    min_views: int = 500_000,
) -> List[Dict[str, Any]]:
    """
    Creative Center에서 트렌딩 해시태그 크롤링
    
    OutlierItem 파이프라인에 연결 가능
    """
    scraper = CreativeCenterScraper()
    try:
        hashtags = await scraper.fetch_trending_hashtags(country=country)
        
        # OutlierItem 형식으로 변환
        results = []
        for h in hashtags:
            if h.video_views >= min_views:
                results.append({
                    "source": "creative_center",
                    "hashtag_id": h.hashtag_id,
                    "hashtag_name": h.hashtag_name,
                    "video_views": h.video_views,
                    "publish_count": h.publish_count,
                    "rank": h.rank,
                    "industry": h.industry,
                    "discovered_at": datetime.utcnow().isoformat(),
                })
        
        logger.info(f"Discovered {len(results)} high-view hashtags from Creative Center")
        return results
        
    finally:
        await scraper.close()


# CLI 테스트용
if __name__ == "__main__":
    import asyncio
    
    async def main():
        scraper = CreativeCenterScraper()
        try:
            print("=== Fetching trending hashtags ===")
            hashtags = await scraper.fetch_trending_hashtags(limit=10)
            for h in hashtags:
                print(f"#{h.hashtag_name} - {h.video_views:,} views (rank #{h.rank})")
            
            print("\n=== Fetching trending videos ===")
            videos = await scraper.fetch_trending_videos(min_views=1_000_000, limit=5)
            for v in videos:
                print(f"{v.title[:50]}... - {v.view_count:,} views")
        finally:
            await scraper.close()
    
    asyncio.run(main())
