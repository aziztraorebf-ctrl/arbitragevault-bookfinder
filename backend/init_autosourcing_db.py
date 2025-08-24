#!/usr/bin/env python3
"""
Script d'initialisation directe des tables AutoSourcing.
Évite les problèmes de migration Alembic avec les types JSONB existants.
"""
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.settings import get_settings
from app.models.autosourcing import Base, SavedProfile

async def init_autosourcing_tables():
    """Initialise les tables AutoSourcing et crée les profils par défaut."""
    
    settings = get_settings()
    
    # Créer engine async
    engine = create_async_engine(settings.database_url)
    
    print("🔧 Création des tables AutoSourcing...")
    
    async with engine.begin() as conn:
        # Créer seulement les nouvelles tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Tables créées avec succès")
    
    # Créer les profils par défaut
    print("🎯 Création des profils par défaut...")
    
    async with engine.begin() as conn:
        from sqlalchemy.ext.asyncio import AsyncSession
        async with AsyncSession(engine) as session:
            # Vérifier si des profils existent déjà
            from sqlalchemy import text, select
            result = await session.execute(select(SavedProfile))
            count = len(result.all())
            
            if count == 0:
                default_profiles = SavedProfile.create_default_profiles()
                session.add_all(default_profiles)
                await session.commit()
                print(f"✅ {len(default_profiles)} profils par défaut créés")
            else:
                print(f"ℹ️  {count} profils déjà présents")
    
    await engine.dispose()
    
    print("🎉 Initialisation AutoSourcing terminée!")

if __name__ == "__main__":
    asyncio.run(init_autosourcing_tables())