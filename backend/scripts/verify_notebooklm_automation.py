import asyncio
import logging
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.rag.notebooklm_playwright import PlaywrightNotebookLMClient

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    logger.info("🚀 Starting NotebookLM Automation Verification")
    
    client = PlaywrightNotebookLMClient(cdp_port=9223)
    
    try:
        # 1. Connect
        logger.info("Step 1: Connecting to Chrome...")
        await client.connect()
        logger.info("✅ Connected")

        # 2. Create Notebook
        logger.info("Step 2: Creating Notebook 'Automation Test'...")
        nb_id = await client.create_notebook("Automation Test")
        logger.info(f"✅ Notebook Created: {nb_id}")

        # 3. Add Source
        logger.info("Step 3: Adding Text Source...")
        source_id = await client.add_text_source(
            nb_id, 
            "Test Document", 
            "This is a test document for verification. The secret code is SUPER_SECRET_123."
        )
        logger.info(f"✅ Source Added: {source_id}")

        # 4. Query
        logger.info("Step 4: Querying...")
        await asyncio.sleep(15) # Wait for indexing (NotebookLM needs time)
        # Pass source_id directly to avoid flaky UUID extraction
        source_ids = [source_id] if source_id else None
        result = await client.query(nb_id, "What is the secret code?", source_ids=source_ids)
        
        # Check result
        if result.get("success"):
            logger.info(f"✅ Query Success. Response Length: {len(result['raw_response'])}")
            print(f"Response Preview: {result['raw_response'][:200]}...")
        else:
            logger.error(f"❌ Query Failed. Full Result: {result}")
            if 'logs' in result:
                logger.error("Browser Console Logs:")
                for log in result['logs']:
                    logger.error(f"  - {log}")

        # 5. Delete (Clean up)
        # Uncomment to enable cleanup, or keep for manual inspection
        logger.info("Step 5: Cleaning up (Deleting Notebook)...")
        await client.delete_notebook(nb_id)
        logger.info("✅ Notebook Deleted")

    except Exception as e:
        logger.error(f"❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
