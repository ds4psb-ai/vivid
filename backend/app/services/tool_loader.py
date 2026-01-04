"""Service for dynamically loading and caching tool definitions."""
import json
from typing import List, Optional, Dict, Any
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Tool, ToolSchema, ToolDependency
from app.redis_client import get_redis_client

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 300  # 5 minutes
CACHE_KEY_ALL_TOOLS = "tools:all:v1"

class DynamicToolLoader:
    """Loads tool definitions from DB with Redis caching."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        try:
            self.redis = get_redis_client()
        except RuntimeError:
            logger.warning("Redis client not initialized, caching disabled")
            self.redis = None

    async def get_all_tools(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """
        Get all tools with their current schemas.
        Returns serialized dicts suitable for LLM context or API response.
        """
        if not include_inactive and self.redis:
            # Try cache first
            cached = await self.redis.get(CACHE_KEY_ALL_TOOLS)
            if cached:
                try:
                    return json.loads(cached)
                except json.JSONDecodeError:
                    await self.redis.delete(CACHE_KEY_ALL_TOOLS)
        
        # Fetch from DB
        stmt = select(Tool).options(
            selectinload(Tool.current_schema)  # We'll need to define this relationship or join manually
        )
        
        if not include_inactive:
            stmt = stmt.where(Tool.is_active == True)
            
        result = await self.db.execute(stmt)
        tools = result.scalars().all()
        
        # Serialize
        serialized_tools = []
        for tool in tools:
            # Fetch current schema manually if relationship not defined
            stmt_schema = select(ToolSchema).where(
                ToolSchema.tool_id == tool.id,
                ToolSchema.is_current == True
            )
            schema_res = await self.db.execute(stmt_schema)
            schema = schema_res.scalar_one_or_none()
            
            tool_dict = {
                "id": str(tool.id),
                "tool_key": tool.tool_key,
                "dimension": tool.dimension,
                "name": {"ko": tool.name_ko, "en": tool.name_en},
                "description": {"ko": tool.description_ko, "en": tool.description_en},
                "endpoint": tool.endpoint,
                "input_schema": schema.input_schema if schema else {},
                "output_schema": schema.output_schema if schema else {},
                "credit_cost": tool.credit_cost,
                "color": tool.color,
                "icon": tool.icon,
            }
            serialized_tools.append(tool_dict)
            
        # Update cache if active-only
        if not include_inactive and self.redis:
            await self.redis.setex(
                CACHE_KEY_ALL_TOOLS,
                CACHE_TTL_SECONDS,
                json.dumps(serialized_tools)
            )
            
        return serialized_tools

    async def invalidate_cache(self):
        """Invalidate all tool caches."""
        if self.redis:
            await self.redis.delete(CACHE_KEY_ALL_TOOLS)
            logger.info("Tool cache invalidated")
