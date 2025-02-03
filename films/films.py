"""Parse data from a Oscar films"""
import asyncio
from typing import Any, Coroutine
from urllib.parse import urljoin

from aiohttp import ClientSession
from bs4 import BeautifulSoup

from utils.file_utils import save_to_json, save_to_csv
from utils.request_utils import fetch_with_retry

BASE_URL: str = "https://www.scrapethissite.com/pages/ajax-javascript/"


async def get_films(session: ClientSession, year: str) -> dict[str, Any]:
    """
    Use ajax request for specified year.

    :param session: aiohttp session
    :param year: year
    :return: dict of data
    """
    ajax_url: str = "?ajax=true&year={}"
    url: str = urljoin(BASE_URL, ajax_url.format(year))
    response = await fetch_with_retry(session, url)
    data = await response.json()
    response.close()

    return data


async def get_years(session: ClientSession) -> list[str]:
    """
    Parse all years categories from a main page.

    :param session: aiohttp session
    :return: list of years
    """
    response = await fetch_with_retry(session, BASE_URL)
    data = await response.text()
    response.close()

    soup: BeautifulSoup = BeautifulSoup(data, "lxml")
    years_soup: list[BeautifulSoup] = soup.findAll("a", class_="year-link")
    years: list[str] = [year.text.strip() for year in years_soup]

    return years


async def main():
    """Entry point."""

    async with ClientSession() as session:
        years: list[str] = await get_years(session)

        tasks: list[Coroutine] = [get_films(session, year) for year in years]
        results = await asyncio.gather(*tasks)

    all_data: list[dict] = [item for sublist in results for item in sublist]

    save_to_csv(all_data, "films.csv")
    save_to_json(all_data, "films.json")


if __name__ == '__main__':
    asyncio.run(main())
