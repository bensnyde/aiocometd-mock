import asyncio

from aiocometd_ng import Client

async def chat():

    # connect to the server
    async with Client("http://localhost:8080/cometd") as client:

            # subscribe to channels
            await client.subscribe("/chat/demo")
            await client.subscribe("/members/demo")

            # listen for incoming messages
            async for message in client:
                topic = message["channel"]
                data = message["data"]
                print(f"{topic}: {data}")

if __name__ == "__main__":
    asyncio.run(chat())