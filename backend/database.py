import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

_DB_PATH = os.getenv("DB_PATH", "/data/maildefender.db")
_DATABASE_URL = f"sqlite+aiosqlite:///{_DB_PATH}"

engine = create_async_engine(_DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def init_db():
    dir_ = os.path.dirname(_DB_PATH)
    if dir_:
        os.makedirs(dir_, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        try:
            await conn.execute(text("ALTER TABLE scans ADD COLUMN source VARCHAR(16) DEFAULT 'unknown'"))
        except Exception:
            pass  # Column already exists
