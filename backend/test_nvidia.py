import asyncio

from app.clients.ai_model import AIModelClient


async def main():
    client = AIModelClient()

    response = await client.chat(
        messages=[
            {
                "role": "user",
                "content": "Reply with exactly: NVIDIA connection successful",
            }
        ]
    )

    print("AI RESPONSE:")
    print(response.content)


if __name__ == "__main__":
    asyncio.run(main())