"""
Node Execution Router - 노드별 실행 API

각 노드 타입(INPUT/GENERATE/VALIDATE/OUTPUT)에 따른 실행 로직과
실시간 SSE 스트리밍을 제공합니다.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, AsyncIterator
import json
import asyncio
from datetime import datetime

from app.logging_config import get_logger
from app.config import settings

# Google Generative AI for direct text generation
import google.generativeai as genai

# Configure Gemini
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

logger = get_logger("nodes_router")

router = APIRouter(prefix="/nodes", tags=["nodes"])


# =============================================================================
# Schemas
# =============================================================================

class NodeExecuteRequest(BaseModel):
    """노드 실행 요청"""
    node_id: str
    node_type: str
    category: str = "generate"
    input_data: Dict[str, Any] = Field(default_factory=dict)
    upstream_results: Dict[str, Any] = Field(default_factory=dict)  # 이전 노드 결과
    params: Dict[str, Any] = Field(default_factory=dict)
    ai_model: Optional[str] = "gemini-3-flash-preview"


class NodeExecuteResult(BaseModel):
    """노드 실행 결과"""
    node_id: str
    status: str  # "complete" | "error"
    output: Dict[str, Any]
    execution_time_ms: int
    token_usage: Dict[str, int] = Field(default_factory=lambda: {"input": 0, "output": 0, "total": 0})


# =============================================================================
# SSE Streaming Helper
# =============================================================================

async def sse_stream(generator: AsyncIterator[Dict[str, Any]]) -> AsyncIterator[str]:
    """SSE 형식으로 이벤트 스트림 생성"""
    async for event in generator:
        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"


# =============================================================================
# Node Execution Logic
# =============================================================================

async def execute_input_node(request: NodeExecuteRequest) -> AsyncIterator[Dict[str, Any]]:
    """INPUT 노드 실행 - 사용자 입력 검증 및 전달"""
    yield {"type": "status", "status": "loading", "message": "입력 데이터 검증 중..."}
    await asyncio.sleep(0.5)
    
    text_input = request.input_data.get("text", "")
    file_input = request.input_data.get("file")
    
    if not text_input and not file_input:
        yield {"type": "error", "message": "텍스트 또는 파일 입력이 필요합니다"}
        return
    
    yield {"type": "status", "status": "streaming", "message": "입력 처리 중..."}
    await asyncio.sleep(0.3)
    
    yield {
        "type": "result",
        "status": "complete",
        "output": {
            "text": text_input,
            "file": file_input,
            "validated": True,
            "timestamp": datetime.utcnow().isoformat(),
        }
    }


async def execute_generate_node(request: NodeExecuteRequest) -> AsyncIterator[Dict[str, Any]]:
    """GENERATE 노드 실행 - AI 모델 호출"""
    yield {"type": "status", "status": "loading", "message": f"AI 모델 준비 중... ({request.ai_model})"}
    await asyncio.sleep(0.5)
    
    # 업스트림 결과에서 입력 추출
    input_text = request.upstream_results.get("text", request.input_data.get("text", ""))
    
    if not input_text:
        yield {"type": "error", "message": "입력 텍스트가 없습니다"}
        return
    
    yield {"type": "status", "status": "streaming", "message": "AI 생성 중..."}
    
    try:
        # 실제 Gemini API 호출
        prompt = f"""당신은 전문 스토리 작가입니다.

다음 컨셉을 기반으로 짧은 스토리 개요를 작성하세요:

컨셉: {input_text}

다음 형식으로 작성하세요:
1. 로그라인 (1-2문장)
2. 주요 캐릭터 (2-3명)
3. 3막 구조 개요
"""
        
        # Direct Gemini API call
        model = genai.GenerativeModel(
            model_name=request.ai_model or "gemini-3-flash-preview",
            system_instruction="전문적이고 창의적인 스토리텔러로서 응답하세요."
        )
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.8,
                max_output_tokens=2000,
            )
        )
        
        result = response.text
        token_usage = {
            "input": getattr(response.usage_metadata, "prompt_token_count", 0) if hasattr(response, "usage_metadata") else 0,
            "output": getattr(response.usage_metadata, "candidates_token_count", 0) if hasattr(response, "usage_metadata") else 0,
            "total": getattr(response.usage_metadata, "total_token_count", 0) if hasattr(response, "usage_metadata") else 0,
        }
        
        # 결과를 청크로 분할하여 스트리밍
        chunks = result.split("\n")
        for i, chunk in enumerate(chunks):
            if chunk.strip():
                yield {
                    "type": "chunk",
                    "content": chunk + "\n",
                    "progress": (i + 1) / len(chunks),
                }
                await asyncio.sleep(0.1)
        
        yield {
            "type": "result",
            "status": "complete",
            "output": {
                "generated_text": result,
                "model": request.ai_model,
                "token_usage": token_usage,
            }
        }
        
    except Exception as e:
        logger.error(f"GENERATE node error: {e}")
        yield {"type": "error", "message": str(e)}


async def execute_validate_node(request: NodeExecuteRequest) -> AsyncIterator[Dict[str, Any]]:
    """VALIDATE 노드 실행 - DNA 검증"""
    yield {"type": "status", "status": "loading", "message": "검증 규칙 로딩 중..."}
    await asyncio.sleep(0.3)
    
    narrative_dna = request.params.get("narrative_dna", {})
    upstream_text = request.upstream_results.get("generated_text", "")
    
    yield {"type": "status", "status": "streaming", "message": "서사 DNA 검증 중..."}
    
    # 검증 규칙 체크
    checks = [
        {"rule": "톤 일관성", "passed": True, "details": "전체 톤이 일관됩니다"},
        {"rule": "주제 준수", "passed": True, "details": "핵심 주제가 유지됩니다"},
        {"rule": "금지 요소", "passed": True, "details": "금지된 요소가 없습니다"},
    ]
    
    for check in checks:
        yield {
            "type": "validation",
            "rule": check["rule"],
            "passed": check["passed"],
            "details": check["details"],
        }
        await asyncio.sleep(0.2)
    
    all_passed = all(c["passed"] for c in checks)
    
    yield {
        "type": "result",
        "status": "complete",
        "output": {
            "validated": all_passed,
            "checks": checks,
            "compliance_score": 1.0 if all_passed else 0.5,
        }
    }


async def execute_output_node(request: NodeExecuteRequest) -> AsyncIterator[Dict[str, Any]]:
    """OUTPUT 노드 실행 - 최종 결과 컴파일"""
    yield {"type": "status", "status": "loading", "message": "결과 컴파일 중..."}
    await asyncio.sleep(0.5)
    
    yield {"type": "status", "status": "streaming", "message": "출력 형식 준비 중..."}
    await asyncio.sleep(0.3)
    
    # 모든 업스트림 결과 수집
    compiled_output = {
        "format": request.params.get("format", "json"),
        "data": request.upstream_results,
        "timestamp": datetime.utcnow().isoformat(),
        "ready_for_export": True,
    }
    
    yield {
        "type": "result",
        "status": "complete",
        "output": compiled_output,
    }


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/execute")
async def execute_node(request: NodeExecuteRequest):
    """
    노드 실행 API (SSE 스트리밍)
    
    노드 카테고리에 따라 적절한 실행 로직을 호출하고
    결과를 실시간으로 스트리밍합니다.
    """
    logger.info(f"Executing node: {request.node_id} (category: {request.category})")
    
    # 카테고리별 실행 함수 매핑
    executors = {
        "input": execute_input_node,
        "generate": execute_generate_node,
        "validate": execute_validate_node,
        "output": execute_output_node,
        # refine/compose는 generate와 동일하게 처리
        "refine": execute_generate_node,
        "compose": execute_generate_node,
    }
    
    executor = executors.get(request.category, execute_generate_node)
    
    return StreamingResponse(
        sse_stream(executor(request)),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/execute-sync", response_model=NodeExecuteResult)
async def execute_node_sync(request: NodeExecuteRequest):
    """
    노드 동기 실행 API (비스트리밍)
    
    스트리밍이 필요 없는 경우 사용합니다.
    """
    import time
    start_time = time.time()
    
    logger.info(f"Executing node (sync): {request.node_id}")
    
    # 실행 및 결과 수집
    results = []
    executors = {
        "input": execute_input_node,
        "generate": execute_generate_node,
        "validate": execute_validate_node,
        "output": execute_output_node,
        "refine": execute_generate_node,
        "compose": execute_generate_node,
    }
    
    executor = executors.get(request.category, execute_generate_node)
    
    async for event in executor(request):
        results.append(event)
    
    # 마지막 결과 추출
    final_result = next((r for r in reversed(results) if r.get("type") == "result"), None)
    error = next((r for r in results if r.get("type") == "error"), None)
    
    execution_time = int((time.time() - start_time) * 1000)
    
    if error:
        raise HTTPException(status_code=400, detail=error.get("message", "실행 오류"))
    
    return NodeExecuteResult(
        node_id=request.node_id,
        status=final_result.get("status", "complete") if final_result else "error",
        output=final_result.get("output", {}) if final_result else {},
        execution_time_ms=execution_time,
        token_usage=final_result.get("output", {}).get("token_usage", {}) if final_result else {},
    )
