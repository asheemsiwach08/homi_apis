import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as client:
        response = await client.post(
        "https://api.gupshup.io/wa/api/v1/msg",
        headers={
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/x-www-form-urlencoded',
            'apikey': '',
            'cache-control': 'no-cache'
        },
        data={
            'channel': 'whatsapp',
            'source': '',
            'destination': '91',
            'message': 'Hello, how are you?'
        },
        timeout=30.0
    )
        print(response.text)

if __name__ == "__main__":
    asyncio.run(main())
