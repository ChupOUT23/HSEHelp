import asyncio
from db.models import create_db

async def main():
    await create_db()
    print("Database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(main())
