"""Parsing hockey site."""
from logging import Logger
from pprint import pprint
from typing import Coroutine
from urllib.parse import urljoin
import asyncio


import aiohttp
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
            logger.info("Successfully fetched 1 page")
            return 1

        # Извлекаем количество страниц
        pages_count = int(pagination.find_all("li")[-2].text.strip())
        logger.info("Successfully fetched %s pages", pages_count)
        return pages_count

    except asyncio.TimeoutError as e:
        logger.error("Timeout error for %s: %s", url, e)
        return -1

    except aiohttp.ClientError as e:
        logger.error("AIOHTTP client error for %s: %s", url, e)
        return -1

    except Exception as e:
        logger.error("Unexpected error for %s: %s", url, e)
        return -1


async def parse_page(session: ClientSession, per_page: int, page_num: int) -> list[dict]:
    """
    Parse all table data from a page.

    :param session: aiohttp session
    :param per_page: how many rows per page
    :param page_num: page index
    :return:
    """
    url: str = urljoin(BASE_URL, f"?{page_num=}&{per_page=}")
    logger.info("Parsing page: %s", url)
    async with session.get(url) as response:
        text = await response.text()

    soup: BeautifulSoup = BeautifulSoup(text, "lxml")
    soup = soup.find("table", class_="table")
    rows: list[BeautifulSoup] = soup.find_all("tr")
    logger.info("Found %s rows", len(rows) - 1)

    table_headers_soup: list[BeautifulSoup] = rows[0].find_all("th")
    table_headers: list[str] = [column.text.strip() for column in table_headers_soup]

    rows_without_headers: list[BeautifulSoup] = rows[1:]
    rows_data: list[dict] = []
    for row in rows_without_headers:
        row_data: dict = parse_row(row, table_headers)
        rows_data.append(row_data)

    return rows_data


def parse_row(row: BeautifulSoup, table_headers: list[str]) -> dict[str, str]:
    """
    Transform soup row into json format

    :param row: BeautifulSoup row
    :param table_headers: list of table headers
    :return: json format row
    """

    columns_soup: list[BeautifulSoup] = row.find_all("td")
    columns: list[str] = [column.text.strip() for column in columns_soup]
    return dict(zip(table_headers, columns))


async def main():
    """Entry point."""
    async with ClientSession() as session:
        per_page: int = 25
        pages_count: int = await get_pages_count(session, per_page=per_page)
        tasks: list[Coroutine] = [parse_page(session, per_page, i) for i in range(1, pages_count + 1)]

        results: list[list[dict]] = await asyncio.gather(*tasks)
        pprint(results)



if __name__ == '__main__':
    asyncio.run(main())
