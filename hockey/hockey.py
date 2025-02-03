"""Parsing hockey site."""
from logging import Logger
from typing import Coroutine, Any
from urllib.parse import urljoin
import asyncio

import aiohttp
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from logger import get_logger
from utils.request_utils import fetch_with_retry
from utils.file_utils import save_to_json, save_to_csv

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
    logger.info("Fetching number of pages from %s", url)

    try:
        response = await fetch_with_retry(session, url)
        text: str = await response.text()
        response.close()

        if not text:
            logger.warning("Received empty response for %s", url)
            return -1

        soup: BeautifulSoup = BeautifulSoup(text, "lxml")
        pagination = soup.find("ul", class_="pagination")

        if not pagination or len(pagination.find_all("li")) < 2:
            logger.info("Pagination not found, assuming 1 page")
            return 1

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
    logger.info("Parsing page %d: %s", page_num, url)

    try:
        async with session.get(url) as response:
            text = await response.text()

        soup: BeautifulSoup = BeautifulSoup(text, "lxml")
        table = soup.find("table", class_="table")

        if not table:
            logger.warning("No table found on page %d", page_num)
            return []

        rows: list[BeautifulSoup] = table.find_all("tr")
        logger.info("Found %s rows on page %d", len(rows) - 1, page_num)

        table_headers_soup: list[BeautifulSoup] = rows[0].find_all("th")
        table_headers: list[str] = [column.text.strip() for column in table_headers_soup]

        rows_without_headers: list[BeautifulSoup] = rows[1:]
        rows_data: list[dict] = [parse_row(row, table_headers) for row in rows_without_headers]

        logger.info("Successfully parsed page %d", page_num)
        return rows_data

    except Exception as e:
        logger.error("Error parsing page %d: %s", page_num, e)
        return []


def parse_row(row: BeautifulSoup, table_headers: list[str]) -> dict[str, str]:
    """
    Transform soup row into json format.

    :param row: BeautifulSoup row
    :param table_headers: list of table headers
    :return: json format row
    """
    columns_soup: list[BeautifulSoup] = row.find_all("td")
    columns: list[str] = [column.text.strip() for column in columns_soup]
    return dict(zip(table_headers, columns))


async def main():
    """Entry point."""
    logger.info("Starting scraping process")

    async with ClientSession() as session:
        per_page: int = 25
        pages_count: int = await get_pages_count(session, per_page=per_page)

        if pages_count == -1:
            logger.error("Failed to retrieve number of pages, exiting")
            return

        tasks: list[Coroutine] = [parse_page(session, per_page, i) for i in range(1, pages_count + 1)]
        results: tuple[Any] = await asyncio.gather(*tasks)

        all_data: list[dict] = [item for sublist in results for item in sublist]  # Flatten the list
        logger.info("Successfully scraped %d records in total", len(all_data))

        save_to_json(all_data, "hockey_data.json")
        save_to_csv(all_data, "hockey_data.csv")

    logger.info("Scraping process finished")


if __name__ == '__main__':
    asyncio.run(main())
