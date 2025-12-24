import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import AsyncSessionLocal, init_db
from app.seed import seed_auteur_data


async def main() -> None:
    await init_db()
    async with AsyncSessionLocal() as session:
        result = await seed_auteur_data(session)
        print("Seed result:", result)


if __name__ == "__main__":
    asyncio.run(main())
