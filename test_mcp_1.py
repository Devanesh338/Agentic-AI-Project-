import asyncio
import mcp_client

async def main():
    print("Without nest_asyncio:")
    try:
        print(await mcp_client.get_airlines())
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
