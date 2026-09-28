import asyncio
from httpx import AsyncClient
from main import app

async def test():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/export-maestro")
        print("Status code:", response.status_code)
        
asyncio.run(test())
