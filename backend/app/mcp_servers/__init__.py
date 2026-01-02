"""
MCP Server Base - Vivid Computational Truth Architecture

Streamable HTTP 기반 MCP 서버 베이스 클래스.
2025 Best Practice: SSE 대신 Streamable HTTP 사용.

License: arkain.info@gmail.com (Gemini Enterprise)
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, TypeVar
from functools import wraps
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T")


class MCPToolMetadata(BaseModel):
    """MCP Tool 메타데이터"""
    name: str
    description: str
    parameters: Dict[str, Any] = {}
    returns: Optional[str] = None


class MCPResourceMetadata(BaseModel):
    """MCP Resource 메타데이터"""
    uri: str
    name: str
    description: str
    mime_type: str = "application/json"


class MCPServerBase(ABC):
    """
    MCP 서버 베이스 클래스
    
    Features:
    - Streamable HTTP (2025 Standard)
    - Tool/Resource 자동 등록
    - 에러 핸들링 및 로깅
    """
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self._tools: Dict[str, Callable] = {}
        self._resources: Dict[str, Callable] = {}
        self._tool_metadata: Dict[str, MCPToolMetadata] = {}
        self._resource_metadata: Dict[str, MCPResourceMetadata] = {}
        
        # 자동으로 데코레이터로 등록된 메서드 수집
        self._collect_decorated_methods()
        
        logger.info(f"MCP Server initialized: {name} v{version}")
    
    def _collect_decorated_methods(self):
        """데코레이터로 마킹된 메서드 수집"""
        for attr_name in dir(self):
            attr = getattr(self, attr_name, None)
            if callable(attr):
                if hasattr(attr, "_mcp_tool"):
                    tool_name = attr._mcp_tool
                    self._tools[tool_name] = attr
                    if hasattr(attr, "_mcp_tool_meta"):
                        self._tool_metadata[tool_name] = attr._mcp_tool_meta
                elif hasattr(attr, "_mcp_resource"):
                    resource_uri = attr._mcp_resource
                    self._resources[resource_uri] = attr
                    if hasattr(attr, "_mcp_resource_meta"):
                        self._resource_metadata[resource_uri] = attr._mcp_resource_meta
    
    @abstractmethod
    def get_server_info(self) -> Dict[str, Any]:
        """서버 정보 반환"""
        pass
    
    def list_tools(self) -> List[MCPToolMetadata]:
        """사용 가능한 도구 목록"""
        return list(self._tool_metadata.values())
    
    def list_resources(self) -> List[MCPResourceMetadata]:
        """사용 가능한 리소스 목록"""
        return list(self._resource_metadata.values())
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """도구 호출"""
        if tool_name not in self._tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        tool_fn = self._tools[tool_name]
        
        try:
            logger.info(f"MCP Tool call: {tool_name}")
            result = await tool_fn(**arguments)
            logger.info(f"MCP Tool success: {tool_name}")
            return result
        except Exception as e:
            logger.error(f"MCP Tool error: {tool_name} - {e}")
            raise
    
    async def read_resource(self, uri: str) -> Any:
        """리소스 읽기"""
        if uri not in self._resources:
            raise ValueError(f"Unknown resource: {uri}")
        
        resource_fn = self._resources[uri]
        
        try:
            logger.info(f"MCP Resource read: {uri}")
            result = await resource_fn()
            return result
        except Exception as e:
            logger.error(f"MCP Resource error: {uri} - {e}")
            raise


def mcp_tool(name: str, description: str = "", parameters: Dict[str, Any] = None):
    """MCP Tool 데코레이터"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        wrapper._mcp_tool = name
        wrapper._mcp_tool_meta = MCPToolMetadata(
            name=name,
            description=description or func.__doc__ or "",
            parameters=parameters or {},
        )
        return wrapper
    return decorator


def mcp_resource(uri: str, name: str, description: str = "", mime_type: str = "application/json"):
    """MCP Resource 데코레이터"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        wrapper._mcp_resource = uri
        wrapper._mcp_resource_meta = MCPResourceMetadata(
            uri=uri,
            name=name,
            description=description or func.__doc__ or "",
            mime_type=mime_type,
        )
        return wrapper
    return decorator
