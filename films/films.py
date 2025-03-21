"""Parse data from Oscar films"""
import asyncio
from typing import Any, Coroutine
from urllib.parse import urljoin

from aiohttp import ClientSession
from bs4 import BeautifulSoup

from utils.file_utils import save_to_json, save_to_csv
from utils.request_utils import fetch_with_retry
from logger import get_logger


logger = get_logger(__name__)
BASE_URL: str = "https://www.scrapethissite.com/pages/ajax-javascript/"


async def get_films(session: ClientSession, year: str) -> dict[str, Any]:
    """
    Use AJAX request for specified year.

    :param session: aiohttp session
    :param year: year
    :return: dict of data
    """
    ajax_url: str = "?ajax=true&year={}"
    url: str = urljoin(BASE_URL, ajax_url.format(year))

    logger.info("Fetching films for year: %s", year)

    response = await fetch_with_retry(session, url)
    data = await response.json()
    response.close()

    logger.info("Successfully fetched %d films for year: %s", len(data), year)

    return data


async def get_years(session: ClientSession) -> list[str]:
    """
    Parse all year categories from the main page.

    :param session: aiohttp session
    :return: list of years
    """
    logger.info("Fetching available years from main page...")

    response = await fetch_with_retry(session, BASE_URL)
    data = await response.text()
    response.close()

    soup: BeautifulSoup = BeautifulSoup(data, "lxml")
    years_soup: list[BeautifulSoup] = soup.findAll("a", class_="year-link")
    years: list[str] = [year.text.strip() for year in years_soup]

    logger.info("Found %d years to process.", len(years))

    return years


async def main():
    """Entry point."""
    logger.info("Starting film data extraction...")

    async with ClientSession() as session:
        years: list[str] = await get_years(session)

        if not years:
            logger.warning("No years found, exiting.")
            return

        tasks: list[Coroutine] = [get_films(session, year) for year in years]
        results = await asyncio.gather(*tasks)

    all_data: list[dict] = [item for sublist in results for item in sublist]

    if all_data:
        save_to_csv(all_data, "films.csv")
        save_to_json(all_data, "films.json")
        logger.info("Data successfully saved.")
    else:
        logger.warning("No data to save.")

    logger.info("Film data extraction completed.")


if __name__ == '__main__':
    asyncio.run(main())
