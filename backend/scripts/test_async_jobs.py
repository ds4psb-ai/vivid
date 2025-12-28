#!/usr/bin/env python3
"""Test script for verifying Phase 3 async jobs pipeline.

Usage:
    1. Make sure Redis is running: docker-compose up -d redis
    2. Start the worker: arq app.worker.WorkerSettings
    3. Start the API server: uvicorn app.main:app --host 0.0.0.0 --port 8000
    4. Run this script: python scripts/test_async_jobs.py
"""
import asyncio
import httpx
import time

API_BASE = "http://localhost:8000/api/v1"

async def test_generate_job():
    """Test the generate job submission and status polling."""
    async with httpx.AsyncClient() as client:
        # Submit job
        payload = {
            "storyboard_cards": [
                {"card_id": "c1", "shot": "Wide establishing shot", "note": "Test scene"},
                {"card_id": "c2", "shot": "Close-up", "note": "Detail shot"}
            ],
            "provider": "mock",
            "sequence_id": "test-seq",
            "scene_id": "test-scene"
        }
        
        resp = await client.post(f"{API_BASE}/jobs/generate", json=payload)
        print(f"Submit Response: {resp.status_code}")
        
        if resp.status_code != 202:
            print(f"Error: {resp.text}")
            return
        
        data = resp.json()
        job_id = data["job_id"]
        print(f"Job ID: {job_id}")
        
        # Poll status
        for i in range(10):
            status_resp = await client.get(f"{API_BASE}/jobs/{job_id}/status")
            status_data = status_resp.json()
            print(f"Poll {i+1}: {status_data['status']}")
            
            if status_data["status"] in ("completed", "failed"):
                print(f"Result: {status_data.get('result') or status_data.get('error')}")
                break
            
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(test_generate_job())
