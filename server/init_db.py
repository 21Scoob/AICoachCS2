import asyncio
from main import engine
from models import Base

async def creeaza_tabele():
    print("Trimit structura către Supabase...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tabelele au fost construite cu succes în cloud!")

if __name__ == "__main__":
    asyncio.run(creeaza_tabele())