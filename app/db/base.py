from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event

DATABASE_URL = "sqlite+aiosqlite:///ecom.db"

# create engine
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# enable SQLite foreign keys on every connection
@event.listens_for(engine.sync_engine, "connect")
def _fk_pragma_on_connect(dbapi_connection, connection_record):
    # called for each DB-API connection
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

class Base(DeclarativeBase):
    pass

# session factory
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    # create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)