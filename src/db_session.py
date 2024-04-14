import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec


SqlAlchemyBase = dec.declarative_base()
__factory = None


def base_init(db_file: Path):
    global __factory
    if __factory:
        return
    if not db_file.parent.exists():
        raise Exception("Parent folder doesn't exist")
    conn_str = f'sqlite+aiosqlite:///{db_file}?check_same_thread=False'
    print(f"Connection to base {db_file}\n")
    engine = create_async_engine(conn_str, echo=False)
    __factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    import src.__all_models__

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(SqlAlchemyBase.metadata.create_all)

    asyncio.run(init_models())


def create_session() -> Session:
    global __factory
    return __factory()
