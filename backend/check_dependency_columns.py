import asyncio
from sqlalchemy import text
from app.db.session import AsyncSessionLocal


async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'commitment_dependencies'
                ORDER BY ordinal_position
            """)
        )

        print("\nCOMMITMENT_DEPENDENCIES COLUMNS:")
        print("-" * 40)

        for row in result:
            print(row.column_name)


if __name__ == "__main__":
    asyncio.run(main())