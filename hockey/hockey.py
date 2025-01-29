"""Parsing hockey site."""
from logging import Logger
from urllib.parse import urljoin

import aiohttp
import asyncio

from aiohttp import ClientSession
from bs4 import BeautifulSoup

from logger import get_logger
from utils.request_utils import fetch_with_retry

logger: Logger = get_logger(__name__)
BASE_URL: str = "https://www.scrapethissite.com/pages/forms/"


async def get_pages_count(session: ClientSession, per_page: int = 25) -> int:
    """
    Get number of pages with specified number of rows per page.

    :param per_page: number of rows per page
    :param session: aiohttp session
    :return: number of pages
    """
    url: str = urljoin(BASE_URL, f"?per_page={per_page}")
    try:

        text: str = await fetch_with_retry(session, url)

        if not text:
            return -1

        soup: BeautifulSoup = BeautifulSoup(text, "lxml")
        pagination = soup.find("ul", class_="pagination")

        if pagination.text == "\n" or len(pagination.find_all("li")) < 2:
            # Пагинация не найдена или есть только одна страница
            return 1

        # Извлекаем количество страниц
        pages_count = pagination.find_all("li")[-2].text.strip()
        return int(pages_count)

    except asyncio.TimeoutError as e:
        logger.error(f"Timeout error for {url}: {e}")
        return -1

    except aiohttp.ClientError as e:
        logger.error(f"AIOHTTP client error for {url}: {e}")
        return -1

    except Exception as e:
        logger.error(f"Unexpected error for {url}: {e}")
        return -1


async def main():
    """Entry point."""
    async with ClientSession() as session:
        pages_count: int = await get_pages_count(session, per_page=600)
        logger.info(f"Successfully fetched {pages_count} pages")
        print(pages_count)


if __name__ == '__main__':
    asyncio.run(main())
