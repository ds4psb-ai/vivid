#!/usr/bin/env python3
"""Seed a master admin account (email only) for initial access."""
import argparse
import asyncio
from datetime import datetime

from sqlalchemy import select

from app.config import settings
from app.credit_service import get_or_create_user_credits
from app.database import AsyncSessionLocal, init_db
from app.models import UserAccount


async def seed(email: str, role: str) -> None:
    await init_db(drop_all=False)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserAccount).where(
                UserAccount.provider == "google",
                UserAccount.email == email,
            )
        )
        account = result.scalar_one_or_none()
        if not account:
            account = UserAccount(
                user_id=f"google:{email}",
                provider="google",
                provider_user_id=email,
                email=email,
                role=role,
                is_active=True,
                last_login_at=datetime.utcnow(),
            )
            session.add(account)
        else:
            account.role = role
            account.is_active = True
            account.last_login_at = datetime.utcnow()
        await session.commit()
        await session.refresh(account)
        await get_or_create_user_credits(session, account.user_id)
        print(f"Seeded {account.email} as {account.role} (user_id={account.user_id})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed a master admin account")
    parser.add_argument(
        "--email",
        default=(settings.MASTER_ADMIN_EMAILS.split(",")[0].strip() if settings.MASTER_ADMIN_EMAILS else ""),
        help="Email address to seed (default: first MASTER_ADMIN_EMAILS)",
    )
    parser.add_argument("--role", default="master", help="Role to assign (default: master)")
    args = parser.parse_args()
    if not args.email:
        raise SystemExit("Email is required. Use --email or set MASTER_ADMIN_EMAILS.")
    asyncio.run(seed(args.email, args.role))


if __name__ == "__main__":
    main()
