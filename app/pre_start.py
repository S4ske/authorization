from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy import select
from tenacity import retry, stop_after_attempt, wait_fixed
import asyncio
from app.core.db import async_engine

max_tries = 60 * 5
wait_seconds = 1


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
)
async def init(db_engine: AsyncEngine) -> None:
    async with AsyncSession(db_engine) as async_session:
        await async_session.execute(select(1))


async def main() -> None:
    await init(async_engine)


if __name__ == "__main__":
    asyncio.run(main())
