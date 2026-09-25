from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from models import Base, User, Match, PlayerMatchStats
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import datetime
import httpx
from pydantic import BaseModel, ConfigDict, ValidationError
from pydantic_core import from_json

load_dotenv()

DB = os.getenv('SQL_DATABASE_URL')
leetify_api_key = os.getenv('LEETIFY_API')

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

#Leetify data retrievers
async def validate_leetify_key(leetify_api_key: str) -> bool:
    async with httpx.AsyncClient() as client:
        r = await client.get("https://api-public.cs-prod.leetify.com/api-key/validate", headers = {'Authorization': f"Bearer {leetify_api_key}"})
        return r.status_code == 200

async def get_recent_matches(leetify_id: str, leetify_api_key: str):
    async with httpx.AsyncClient() as client:
        r = await client.get("https://api-public.cs-prod.leetify.com/v3/profile/matches", headers = {'Authorization': f"Bearer {leetify_api_key}"}, params={"id": leetify_id})
        if r.status_code == 200:
            return r.json()
        else:
            return r.status_code

#JSON parser for database
class UserCreate(BaseModel):
    username : str
    email : str
    password : str
    steamid_64: str | None = None

#Backend route logic
@app.get("/user/{user_id}")
async def user_extract(user_id: int, db = Depends(get_db)):
    users = select(User).where(User.id == user_id)

    result = await db.execute(users)

    found_users = result.scalar_one_or_none()

    if found_users is None:
        return{"error": "Jucatorul nu a fost gasit"}
    else:
        return{"username": found_users.username}

@app.get("/matches")
async def match_extract(match_id: int, db = Depends(get_db)):
    matches = select(Match).where(Match.id == match_id)
    result = await db.execute(matches)
    found_matches = result.scalar_one_or_none()

    if found_matches is None:
        return{"error": "No matches registered."}
    else:
        return{"map": found_matches.map}

@app.post("/add-user")
async def create_user(user_data: UserCreate, db = Depends(get_db)):
    addinguser = User(username = user_data.username,
                      email = user_data.email,
                      password = user_data.password,
                      steamid_64 = user_data.steamid_64)
    db.add(addinguser)
    await db.commit()
    await db.refresh(addinguser)
    return addinguser

@app.post("/sync-matches/{user_id}")
async def sync_matches(user_id: int, db = Depends(get_db)):
    user = select(User).where(User.id == user_id)
    result = await db.execute(user)
    found_user = result.scalar_one_or_none()
    if found_user is None:
        return {"error": "User negasit"}
    if not found_user.steamid_64:
        return {"error": "Userul nu are steamid_64 setat"}
    matches_data = await get_recent_matches(found_user.steamid_64, leetify_api_key)
    return matches_data
