"""E2E Test: Fork → Attribution → Settlement Flow

Tests the complete 4-Layer ecosystem:
1. Create a fork of an existing tool
2. Simulate usage of the forked tool
3. Calculate attribution score
4. Create and process settlement
5. Verify revenue distribution

Run with: python -m scripts.test_e2e_fork_settlement
"""
import asyncio
import logging
from uuid import uuid4
from datetime import datetime

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models_telemetry import ToolManifest, ToolRunEvent, ForkEvent, ToolTier
from app.services import telemetry_service
from app.services.fork_revenue_service import (
    create_settlement,
    process_settlement,
    get_settlement_details,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


async def run_e2e_test():
    """Run full E2E test of Fork → Attribution → Settlement flow."""
    
    logger.info("\n" + "=" * 60)
    logger.info("E2E Test: Fork → Attribution → Settlement")
    logger.info("=" * 60)
    
    async with AsyncSessionLocal() as db:
        # ---------------------------------------------------------------------
        # Step 1: Get parent tool (use existing generate_veo_prompt)
        # ---------------------------------------------------------------------
        logger.info("\n📦 Step 1: Get parent tool")
        
        result = await db.execute(
            select(ToolManifest).where(ToolManifest.tool_key == "generate_veo_prompt")
        )
        parent_tool = result.scalars().first()
        
        if not parent_tool:
            logger.error("❌ Parent tool 'generate_veo_prompt' not found!")
            return
        
        logger.info(f"  ✅ Found parent: {parent_tool.tool_key} (id={parent_tool.id})")
        logger.info(f"     Tier: {parent_tool.tier}, Usage: {parent_tool.usage_count}")
        
        # ---------------------------------------------------------------------
        # Step 2: Create a forked tool
        # ---------------------------------------------------------------------
        logger.info("\n🍴 Step 2: Create forked tool")
        
        forked_tool = ToolManifest(
            id=uuid4(),
            tool_key=f"generate_veo_prompt_cinematic_v1_{uuid4().hex[:6]}",
            display_name="1D Origin - 시네마틱 특화 프롬프트",
            description="시네마틱 스타일에 최적화된 Veo 프롬프트 생성기",
            version="1.0.0",
            category="dimension",
            tier=ToolTier.EXPERIMENTAL.value,
            input_schema=parent_tool.input_schema,
            output_schema=parent_tool.output_schema,
            credit_cost=2,  # Different cost
            fork_count=0,
            usage_count=0,
            total_revenue=0,
            parent_tool_id=parent_tool.id,
            fork_depth=1,
            created_by="test-user-forker",
            safety_rating="safe",
            sandbox_required=False,
            is_active=True,
        )
        db.add(forked_tool)
        await db.commit()
        await db.refresh(forked_tool)
        
        logger.info(f"  ✅ Created fork: {forked_tool.tool_key}")
        logger.info(f"     Parent ID: {forked_tool.parent_tool_id}")
        logger.info(f"     Fork depth: {forked_tool.fork_depth}")
        
        # Update parent's fork count
        parent_tool.fork_count += 1
        await db.commit()
        
        # ---------------------------------------------------------------------
        # Step 3: Create ForkEvent
        # ---------------------------------------------------------------------
        logger.info("\n📝 Step 3: Create ForkEvent")
        
        fork_event = ForkEvent(
            id=uuid4(),
            parent_tool_id=parent_tool.id,
            child_tool_id=forked_tool.id,
            fork_depth=1,
            forker_id="test-user-forker",
            fork_reason="시네마틱 스타일에 특화된 프롬프트 생성을 위해",
            diff_lines_added=50,
            diff_lines_removed=10,
            diff_lines_modified=20,
            diff_score=35.0,  # 35% different from parent
            test_passed=True,
            test_run_at=datetime.utcnow(),
            test_details={"tests_run": 5, "tests_passed": 5},
            is_suspicious=False,
        )
        db.add(fork_event)
        await db.commit()
        await db.refresh(fork_event)
        
        logger.info(f"  ✅ Created ForkEvent: {fork_event.id}")
        logger.info(f"     Diff score: {fork_event.diff_score}")
        logger.info(f"     Test passed: {fork_event.test_passed}")
        
        # ---------------------------------------------------------------------
        # Step 4: Simulate usage of forked tool
        # ---------------------------------------------------------------------
        logger.info("\n🔄 Step 4: Simulate tool usage (10 runs)")
        
        for i in range(10):
            run_event = ToolRunEvent(
                id=uuid4(),
                tool_id=forked_tool.id,
                tool_key=forked_tool.tool_key,
                tool_version=forked_tool.version,
                user_id=f"user-{i % 3}",  # 3 different users
                status="success",
                inputs_summary={"topic": f"테스트 주제 {i}"},
                outputs_summary={"has_prompt": True},
                latency_ms=1000 + (i * 100),
                credits_charged=forked_tool.credit_cost,
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )
            db.add(run_event)
            forked_tool.usage_count += 1
            forked_tool.total_revenue += forked_tool.credit_cost
        
        await db.commit()
        await db.refresh(forked_tool)
        
        logger.info(f"  ✅ Simulated 10 runs")
        logger.info(f"     Usage count: {forked_tool.usage_count}")
        logger.info(f"     Total revenue: {forked_tool.total_revenue} credits")
        
        # ---------------------------------------------------------------------
        # Step 5: Calculate Attribution Score
        # ---------------------------------------------------------------------
        logger.info("\n📊 Step 5: Calculate Attribution Score")
        
        # Set quality rating for calculation
        forked_tool.quality_rating = 4.2
        await db.commit()
        
        attribution = await telemetry_service.calculate_attribution_score(db, fork_event.id)
        
        logger.info(f"  ✅ Attribution Score: {attribution.total_score:.2f}")
        logger.info(f"     - Diff score (20%):    {attribution.diff_score:.1f}")
        logger.info(f"     - Test score (15%):    {attribution.test_score:.1f}")
        logger.info(f"     - Usage score (25%):   {attribution.usage_score:.1f}")
        logger.info(f"     - Revenue score (25%): {attribution.revenue_score:.1f}")
        logger.info(f"     - Quality score (15%): {attribution.quality_score:.1f}")
        
        # ---------------------------------------------------------------------
        # Step 6: Create Settlement
        # ---------------------------------------------------------------------
        logger.info("\n💰 Step 6: Create Settlement")
        
        # Get one of the run events for settlement
        result = await db.execute(
            select(ToolRunEvent)
            .where(ToolRunEvent.tool_id == forked_tool.id)
            .limit(1)
        )
        run_event = result.scalars().first()
        
        settlement = await create_settlement(
            db=db,
            tool_run_id=run_event.id,
            tool_id=forked_tool.id,
            tool_key=forked_tool.tool_key,
            total_credits=run_event.credits_charged,
            payer_user_id="payer-user-001",
        )
        
        logger.info(f"  ✅ Created Settlement: {settlement.id}")
        logger.info(f"     Status: {settlement.status}")
        logger.info(f"     Total: {settlement.total_credits} credits")
        logger.info(f"     Platform fee: {settlement.platform_fee} credits")
        logger.info(f"     Creator pool: {settlement.creator_pool} credits")
        
        # ---------------------------------------------------------------------
        # Step 7: Process Settlement (use fresh session to avoid conflicts)
        # ---------------------------------------------------------------------
        logger.info("\n⚙️ Step 7: Process Settlement")
        
        settlement_id = settlement.id
        attribution_total_score = attribution.total_score
        forked_tool_key = forked_tool.tool_key
        forked_usage = forked_tool.usage_count
        forked_revenue = forked_tool.total_revenue
        
    # Use new session for settlement processing
    async with AsyncSessionLocal() as db2:
        success, error = await process_settlement(
            db=db2,
            settlement_id=settlement_id,
            processed_by="system-e2e-test",
        )
        
        if success:
            logger.info(f"  ✅ Settlement processed successfully!")
        else:
            logger.info(f"  ⚠️ Settlement processing issue: {error}")
        
        # Get final settlement details
        details = await get_settlement_details(db2, settlement_id)
        
        if details:
            logger.info(f"     Final status: {details.status}")
            logger.info(f"     Payouts: {len(details.payouts)}")
            for payout in details.payouts:
                logger.info(f"       - {payout.recipient_id}: {payout.amount} credits ({payout.share_type})")
    
    # Summary with fresh read
    async with AsyncSessionLocal() as db3:
        result = await db3.execute(
            select(ToolManifest).where(ToolManifest.tool_key == "generate_veo_prompt")
        )
        parent_tool = result.scalars().first()
        
        result = await db3.execute(
            select(ToolManifest).where(ToolManifest.parent_tool_id == parent_tool.id)
        )
        forked_tool = result.scalars().first()
        
        # ---------------------------------------------------------------------
        # Summary
        # ---------------------------------------------------------------------
        logger.info("\n" + "=" * 60)
        logger.info("✅ E2E TEST COMPLETE")
        logger.info("=" * 60)
        logger.info(f"""
Summary:
- Parent Tool: {parent_tool.tool_key if parent_tool else 'N/A'}
- Forked Tool: {forked_tool_key}
- Fork Attribution Score: {attribution_total_score:.2f}
- Usage Count: {forked_usage}
- Total Revenue: {forked_revenue} credits
- Settlement Status: {'SUCCESS' if success else 'NEEDS REVIEW'}
""")
        
        # ---------------------------------------------------------------------
        # Cleanup (optional - comment out to keep test data)
        # ---------------------------------------------------------------------
        # logger.info("\n🧹 Cleaning up test data...")
        # await db.delete(settlement)
        # await db.delete(fork_event)
        # await db.delete(forked_tool)
        # await db.commit()
        # logger.info("  ✅ Test data cleaned up")


if __name__ == "__main__":
    asyncio.run(run_e2e_test())
