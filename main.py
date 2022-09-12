import asyncio
from parsing import Parser


def main():
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(Parser.main())


if __name__ == '__main__':
    main()