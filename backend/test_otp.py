import asyncio
import httpx

async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post('http://localhost:8000/auth/send-otp', json={'phone': '07025580054'})
        print(resp.status_code)
        print(resp.text)

if __name__ == "__main__":
    asyncio.run(main())
