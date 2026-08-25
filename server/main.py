from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, select 
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from models import Base, User, Match, PlayerMatchStats
import os
from dotenv import load_dotenv


load_dotenv()

DB = os.getenv('SQL_DATABASE_URL')

engine = create_async_engine(DB)
SessionLocal = async_sessionmaker(bind=engine,autoflush= False)

async def get_db():
    async with SessionLocal() as db:
        yield db

app = FastAPI()

@app.get("/user/{user_id}")
async def user_extract(user_id: int, db = Depends(get_db)):
    users = select(User).where(User.id == user_id)
    
    result = await db.execute(users)
    
    found_users = result.scalar_one_or_none()
    
    if found_users is None:
        return{"error": "Jucatorul nu a fost gasit"}
    else:
        return{"username": found_users.username}
   