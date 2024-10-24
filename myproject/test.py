from asgiref.sync import sync_to_async

@sync_to_async
def test_func():
    return "Success!"

import asyncio

async def main():
    result = await test_func()
    print(result)

asyncio.run(main())
