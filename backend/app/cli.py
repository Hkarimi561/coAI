"""Operator CLI.

    python -m app.cli create-admin --email admin@example.com --name "Admin" [--password ...]
    python -m app.cli ingest [--force]
    python -m app.cli eval --dataset eval/questions.json [--retrieval-only | --sweep] [--web] [--judge] [--out report.json] [--baseline old.json]
"""

import argparse
import asyncio
import getpass
import sys

from sqlalchemy import func, select

from app.db import SessionLocal, engine
from app.models import User
from app.permissions import ADMIN_ROLE
from app.security import hash_password
from app.services import ingestion, rbac


async def create_admin(email: str, name: str, password: str | None) -> int:
    password = password or getpass.getpass("Password (min 8 chars): ")
    if len(password) < 8:
        print("Password must be at least 8 characters", file=sys.stderr)
        return 2
    email = email.strip().lower()
    async with SessionLocal() as session:
        admin_role = (await rbac.ensure_system_roles(session))[ADMIN_ROLE]
        user = (await session.execute(select(User).where(func.lower(User.email) == email))).scalar_one_or_none()
        if user:
            user.is_active, user.password_hash = True, hash_password(password)
            if admin_role not in user.roles:
                user.roles.append(admin_role)
            print(f"Updated existing user {email} -> admin")
        else:
            session.add(User(email=email, name=name, password_hash=hash_password(password), roles=[admin_role]))
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


async def evaluate(args: argparse.Namespace) -> int:
    from app import evaluation  # imported lazily: the eval module pulls in the whole workflow

    return await evaluation.run(
        args.dataset, retrieval_only=args.retrieval_only, sweep=args.sweep, allow_web=args.web, use_judge=args.judge, out=args.out,
        baseline=args.baseline, only=args.only,
    )


async def main() -> int:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("create-admin")
    a.add_argument("--email", required=True)
    a.add_argument("--name", default="Administrator")
    a.add_argument("--password")
    i = sub.add_parser("ingest")
    i.add_argument("--force", action="store_true", help="re-index every file, even if unchanged")
    e = sub.add_parser("eval", help="run a question set through the answer workflow and print quality metrics")
    e.add_argument("--dataset", required=True, help="JSON file with the questions (see eval/README.md)")
    e.add_argument("--retrieval-only", action="store_true", help="no LLM: report where each question would be answered from")
    e.add_argument("--sweep", action="store_true", help="retrieval-only for a grid of DOC_SUFFICIENCY_SCORE values")
    e.add_argument("--web", action="store_true", help="allow live web search (off by default so runs are repeatable)")
    e.add_argument("--judge", action="store_true", help="ask the LLM to compare each answer with the question's reference answer")
    e.add_argument("--out", help="write a JSON report here")
    e.add_argument("--baseline", help="an earlier --out report to compare the summary with")
    e.add_argument("--only", nargs="+", help="run only these question ids")
    args = parser.parse_args()
    try:
        if args.cmd == "eval":
            return await evaluate(args)
        return await create_admin(args.email, args.name, args.password) if args.cmd == "create-admin" else await ingest(args.force)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
