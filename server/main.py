from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from models import Base, User, Match, PlayerMatchStats
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv


load_dotenv()

DB = os.getenv('SQL_DATABASE_URL')

engine = create_async_engine(DB,
                             connect_args={"statement_cache_size": 0})
SessionLocal = async_sessionmaker(bind=engine,autoflush= False)
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

async def get_db():
    async with SessionLocal() as db:
        yield db

app = FastAPI(lifespan=lifespan)

@app.get("/user/{user_id}")
async def user_extract(user_id: int, db = Depends(get_db)):
    users = select(User).where(User.id == user_id)

    result = await db.execute(users)

    found_users = result.scalar_one_or_none()

    if found_users is None:
        return{"error": "Jucatorul nu a fost gasit"}
    else:
        return{"username": found_users.username}
