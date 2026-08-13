import pytest
import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Importăm baza și clasele create de tine
from models import Base, User, Match, PlayerMatchStats

# Spunem pytest-ului că acest test folosește funcții async/await
@pytest.mark.asyncio
async def test_adaugare_si_relatii_modele():
    
    # ==========================================
    # 1. ARRANGE (Pregătim terenul)
    # ==========================================
    # Creăm un engine care folosește memoria RAM în loc de Docker
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    # Generăm pe loc tabelele strict pentru acest test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    TestingSession = async_sessionmaker(engine, expire_on_commit=False)

    # ==========================================
    # 2. ACT (Acționăm: inserăm datele)
    # ==========================================
    async with TestingSession() as session:
        # Creăm obiectele (încă nu sunt în baza de date)
        new_user = User(
            username="Miru", 
            password="hashed_password_123", 
            email="miru@coach.com"
        )
        
        new_match = Match(
            date=datetime.datetime.now(), 
            score="13-10", 
            duration=2400 # 40 de minute în secunde
        )
        
        # Le punem în sesiune și dăm commit ca să le salvăm efectiv și să primească ID-uri
        session.add(new_user)
        session.add(new_match)
        await session.commit() 
        
        # Acum că au ID-uri, putem crea statistica de legătură
        new_stats = PlayerMatchStats(
            user_id=new_user.id,
            match_id=new_match.id,
            kd_ratio=1.75,
            utility_use=350.5,
            kar_ratio=1.1,
            hs_percentage=55.0
        )
        
        session.add(new_stats)
        await session.commit()

    # ==========================================
    # 3. ASSERT (Verificăm dacă totul funcționează)
    # ==========================================
    async with TestingSession() as session:
        # Interogăm statistica din baza de date. 
        # options(selectinload(...)) îi spune lui SQLAlchemy să aducă și datele din tabelele legate
        query = select(PlayerMatchStats).options(
            selectinload(PlayerMatchStats.user),
            selectinload(PlayerMatchStats.match)
        )
        result = await session.execute(query)
        statistica_salvata = result.scalar_one() # Extragem singurul rând găsit
        
        # Verificăm coloanele proprii
        assert statistica_salvata.kd_ratio == 1.75
        assert statistica_salvata.hs_percentage == 55.0
        
        # Verificăm dacă relațiile de Python (magia de care vorbeam) funcționează perfect
        assert statistica_salvata.user.username == "Miru"
        assert statistica_salvata.match.score == "13-10"