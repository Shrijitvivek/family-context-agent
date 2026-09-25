import asyncio

from sqlalchemy import text

from app.db.session import engine


async def main():
    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            print("DATABASE CONNECTION SUCCESS:", result.scalar_one())
    except Exception as exc:
        print("DATABASE CONNECTION FAILED:")
        print(exc)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())