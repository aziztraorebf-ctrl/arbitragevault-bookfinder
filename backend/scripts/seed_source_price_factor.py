"""
Seed script: Upsert source_price_factor into BusinessConfig global config.

Idempotent - safe to re-run. Sets data.roi.source_price_factor = 0.40
in the global BusinessConfig (id=1, scope='global').
"""

import asyncio

import logging

from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_source_price_factor() -> None:
    """Upsert source_price_factor=0.40 into global BusinessConfig roi data."""
    from app.core.db import db_manager
    from app.models.business_config import BusinessConfig, DEFAULT_BUSINESS_CONFIG

    await db_manager.initialize()

    try:
        async with db_manager.session() as session:
            result = await session.execute(
                select(BusinessConfig).where(BusinessConfig.scope == "global")
            )
            config = result.scalar_one_or_none()

            if config is None:
                # Create global config with source_price_factor included
                data = dict(DEFAULT_BUSINESS_CONFIG)
                data.setdefault("roi", {})
                data["roi"]["source_price_factor"] = 0.40
                config = BusinessConfig(
                    id=1,
                    scope="global",
                    data=data,
                    version=1,
                    description="Global business configuration",
                )
                session.add(config)
                logger.info("Created global BusinessConfig with source_price_factor=0.40")
            else:
                # Upsert into existing config
                data = dict(config.data)
                data.setdefault("roi", {})
                data["roi"]["source_price_factor"] = 0.40
                config.data = data
                config.increment_version()
                logger.info(
                    "Updated global BusinessConfig with source_price_factor=0.40 (version=%s)",
                    config.version,
                )

            await session.commit()
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(seed_source_price_factor())
