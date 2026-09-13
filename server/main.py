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

@app.post("/add-match")
async def match_adder(db = Depends(get_db)):
    addingmatch = Match(map_name = "Mirage", date = datetime.datetime.utcnow(), score = "13-9", duration = 45)
    db.add(addingmatch)
    await db.commit()
    await db.refresh(addingmatch)
    return addingmatch

@app.post("/player-match-add/{user_id}")
async def player_match_user(user_id: int, match_id: int, db = Depends(get_db)):
    users = select(User).where(User.id == user_id)
    matches = select(Match).where(Match.id == match_id)

    addingplayermatch = PlayerMatchStats(user_id = user_id, match_id = match_id, kd_ratio = 1.4, utility_use = 1.5, kar_ratio = 2, hs_percentage = 50)
    db.add(addingplayermatch)
    await db.commit()
    await db.refresh(addingplayermatch)
    return addingplayermatch