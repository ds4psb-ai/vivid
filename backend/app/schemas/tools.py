from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from datetime import datetime
from uuid import UUID

class ToolSchemaCreate(BaseModel):
    version: str = Field(..., pattern=r'^v\d+\.\d+\.\d+$', description="Semantic version, e.g. v1.0.0")
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    is_current: bool = True

class ToolRegistration(BaseModel):
    tool_key: str = Field(..., min_length=1, max_length=50, pattern=r'^[a-z0-9_]+$')
    dimension: str = Field(..., pattern=r'^[1-4]D$')
    category: str
    
    name_ko: str
    name_en: str
    description_ko: Optional[str] = None
    description_en: Optional[str] = None
    
    endpoint: str
    executor_type: str = "http"
    timeout_seconds: int = 60
    
    credit_cost: int = 5
    billing_type: str = "per_run"
    
    color: Optional[str] = None
    icon: Optional[str] = None
    
    # Inline schema definition for version v1.0.0 (default)
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]

class ToolResponse(BaseModel):
    id: UUID
    tool_key: str
    dimension: str
    name_ko: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
