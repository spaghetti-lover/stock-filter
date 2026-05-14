#!/bin/sh
set -e

python3 -B -c "
import asyncio, asyncpg, os, pathlib

async def migrate():
    conn = await asyncpg.connect(os.environ['DATABASE_URL'])
    migrations = sorted(pathlib.Path('./db/migrations').glob('*.sql'))
    for f in migrations:
        await conn.execute(f.read_text())
    await conn.close()

asyncio.run(migrate())
"

exec python3 -B -m uvicorn main:app --host 0.0.0.0 --port 8000
