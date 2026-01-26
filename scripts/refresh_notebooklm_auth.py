#!/usr/bin/env python3
"""NotebookLM 인증 갱신 스크립트.

쿠키 유효성을 확인하고 필요 시 갱신합니다.
cron job으로 실행하거나 수동으로 실행할 수 있습니다.

Usage:
    # 직접 실행
    python scripts/refresh_notebooklm_auth.py
    
    # cron job (매 6시간마다)
    0 */6 * * * cd /Users/ted/vivid/backend && /Users/ted/vivid/backend/venv314/bin/python scripts/refresh_notebooklm_auth.py >> /tmp/notebooklm-refresh.log 2>&1
"""
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
SCRIPT_DIR = Path(__file__).parent.parent  # /Users/ted/vivid
BACKEND_DIR = SCRIPT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


AUTH_FILE = Path.home() / ".notebooklm-mcp" / "auth.json"
LOG_FILE = Path("/tmp/notebooklm-auth-refresh.log")


async def check_and_refresh():
    """쿠키 상태 확인 및 필요 시 갱신."""
    from app.rag.notebooklm_auth import get_auth_service, AuthStatus
    
    auth_service = get_auth_service()
    status = await auth_service.check_status()
    
    logger.info(f"[Auth Check] Status: {status.status.value}")
    logger.info(f"[Auth Check] Expires at: {status.expires_at}")
    logger.info(f"[Auth Check] Last success: {status.last_success}")
    
    if status.status == AuthStatus.VALID:
        logger.info("✅ Auth is valid, no refresh needed")
        return True
    
    if status.status in (AuthStatus.EXPIRED, AuthStatus.MISSING):
        logger.warning(f"⚠️ Auth issue: {status.error_message}")
        
        # Try automatic refresh via Playwright
        logger.info("[Refresh] Attempting Playwright session refresh...")
        success = await auth_service.refresh()
        
        if success:
            logger.info("✅ Session refreshed successfully")
            return True
        else:
            logger.error("❌ Automatic refresh failed")
            logger.info("💡 Manual refresh required. Run: notebooklm-mcp-auth")
            
            # Send notification (optional - integrate with your notification system)
            await send_alert("NotebookLM auth expired and auto-refresh failed")
            return False
    
    return status.status == AuthStatus.VALID


async def send_alert(message: str):
    """알림 전송 (Slack, Discord 등으로 확장 가능)."""
    logger.warning(f"[ALERT] {message}")
    
    # TODO: Slack webhook integration
    # webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    # if webhook_url:
    #     import httpx
    #     async with httpx.AsyncClient() as client:
    #         await client.post(webhook_url, json={"text": f"🔑 {message}"})


async def verify_api_call():
    """실제 API 호출로 인증 검증."""
    try:
        from app.rag.tier0_notebooklm import get_notebooklm_service
        
        service = get_notebooklm_service()
        result = await service.query_notebook(
            notebook_id="DNA_강주노",
            query="테스트 쿼리"
        )
        
        if result.confidence > 0.5:
            logger.info(f"✅ API verification passed: confidence={result.confidence}")
            return True
        else:
            logger.warning(f"⚠️ Low confidence response: {result.confidence}")
            return False
            
    except Exception as e:
        logger.error(f"❌ API verification failed: {e}")
        return False


async def main():
    """메인 실행."""
    logger.info("=" * 50)
    logger.info(f"NotebookLM Auth Refresh - {datetime.now().isoformat()}")
    logger.info("=" * 50)
    
    # 1. Check and refresh if needed
    auth_ok = await check_and_refresh()
    
    if not auth_ok:
        sys.exit(1)
    
    # 2. Verify with actual API call (optional)
    if "--verify" in sys.argv:
        api_ok = await verify_api_call()
        if not api_ok:
            sys.exit(2)
    
    logger.info("✅ All checks passed")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
