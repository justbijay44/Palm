from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# uses sqlite
# +aiosqlite is async sqlite driver
DATABASE_URL = 'sqlite+aiosqlite:///app.db'    

# core connection handler to db
engine = create_async_engine(DATABASE_URL, echo = False)

# to create factory that produce async db session
AsyncSessionLocal = async_sessionmaker(
    bind= engine,
    expire_on_commit=False  # to make orm object usable even after commits
)

# defining base orm class
Base = declarative_base()

# the imp part
# creation of db session, automatic session close after use
async def get_session():
    async with AsyncSessionLocal() as session:
        yield session