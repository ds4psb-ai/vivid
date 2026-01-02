from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
from arq.connections import ArqRedis

router = APIRouter()

class PipelineEvent(BaseModel):
    event_type: str
    payload: Dict[str, Any]

@router.post("/events/s3_hook")
async def s3_event_hook(event: PipelineEvent, request: Request):
    """
    Receives events (simulating S3 Trigger) and enqueues jobs.
    """
    if not hasattr(request.app.state, "arq_pool"):
         raise HTTPException(status_code=500, detail="Worker pool not initialized")

    arq_pool: ArqRedis = request.app.state.arq_pool
    
    if event.event_type == "s3:ObjectCreated:Put":
         key = event.payload.get("key")
         if key:
             # Enqueue the job defined in worker.py
             job = await arq_pool.enqueue_job("process_upload", file_key=key)
             return {"status": "enqueued", "job_id": job.job_id, "key": key}
    
    return {"status": "ignored", "reason": f"No handler for event_type: {event.event_type}"}
