"""Operator CLI.

    python -m app.cli create-admin --email admin@example.com --name "Admin" [--password ...]
    python -m app.cli ingest [--force]
"""

import argparse
import asyncio
import getpass
import sys

from sqlalchemy import func, select

from app.db import SessionLocal, engine
from app.models import User
from app.security import hash_password
from app.services import ingestion


async def create_admin(email: str, name: str, password: str | None) -> int:
    password = password or getpass.getpass("Password (min 8 chars): ")
    if len(password) < 8:
        print("Password must be at least 8 characters", file=sys.stderr)
        return 2
    email = email.strip().lower()
    async with SessionLocal() as session:
        user = (await session.execute(select(User).where(func.lower(User.email) == email))).scalar_one_or_none()
        if user:
            user.role, user.is_active, user.password_hash = "admin", True, hash_password(password)
            print(f"Updated existing user {email} -> admin")
        else:
            session.add(User(email=email, name=name, password_hash=hash_password(password), role="admin"))
            print(f"Created admin {email}")
        await session.commit()
    return 0


async def ingest(force: bool) -> int:
    report = await ingestion.sync_directory(force=force)
    print(f"indexed={len(report.indexed)} unchanged={report.skipped} removed={len(report.removed)} errors={len(report.errors)}")
    for p in report.indexed:
        print(f"  + {p}")
    for p in report.removed:
        print(f"  - {p}")
    for e in report.errors:
        print(f"  ! {e['path']}: {e['error']}", file=sys.stderr)
    return 1 if report.errors else 0


async def main() -> int:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("create-admin")
    a.add_argument("--email", required=True)
    a.add_argument("--name", default="Administrator")
    a.add_argument("--password")
    i = sub.add_parser("ingest")
    i.add_argument("--force", action="store_true", help="re-index every file, even if unchanged")
    args = parser.parse_args()
    try:
        return await create_admin(args.email, args.name, args.password) if args.cmd == "create-admin" else await ingest(args.force)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
