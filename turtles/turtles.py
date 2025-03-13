"""Parsing turtles data from iframes"""
from typing import Coroutine
from urllib.parse import urljoin
from os.path import join

import asyncio
import aiohttp
from bs4 import BeautifulSoup

from utils.request_utils import fetch_with_retry
from utils.file_utils import save_to_json, save_to_csv, save_image
from logger import get_logger


logger = get_logger(__name__)
BASE_URL: str = "https://www.scrapethissite.com/pages/frames/?frame=i"


async def get_turtle_links(session: aiohttp.ClientSession) -> list[str]:
    """
    get turtles iframes links from a main page.

    :param session: aiohttp.ClientSession
    :return: list[str]
    """
    turtle_links: list[str] = []

    logger.info("Getting turtle links from %s", BASE_URL)

    response: aiohttp.ClientResponse = await fetch_with_retry(session, BASE_URL)
    text: str = await response.text()
    response.close()

    soup: BeautifulSoup = BeautifulSoup(text, "lxml")
    turtle_buttons: list[BeautifulSoup] = soup.find_all("a", class_="btn btn-default btn-xs")
    logger.info("Found %s turtle links", len(turtle_buttons))
    for turtle_button in turtle_buttons:
        turtle_links.append(urljoin(BASE_URL, turtle_button["href"]))

    return turtle_links


async def parse_turtles(session: aiohttp.ClientSession, turtle_link: str) -> dict[str, str]:
    """
    Parse name, description and image from a turtle link.

    :param session: aiohttp.ClientSession
    :param turtle_link: str
    :return: dict[str, str]
    """
    logger.info("Parsing %s", turtle_link)
    response: aiohttp.ClientResponse = await fetch_with_retry(session, turtle_link)
    soup: BeautifulSoup = BeautifulSoup(await response.text(), "lxml")
    response.close()
    turtle_name: str = soup.find("h3", class_="family-name").text.strip()
    description: str = soup.find("p", class_="lead").text.strip()

    image_url: str = soup.find("img", attrs={"src": True, "class": "turtle-image center-block"})["src"]
    await fetch_and_save_image(session, image_url, turtle_name + ".jpg")

    return {"name": turtle_name, "description": description, "image_name": turtle_name + ".jpg"}


async def fetch_and_save_image(session: aiohttp.ClientSession, url: str, filename: str):
    """
    Save image from url to filename.

    :param session: aiohttp.ClientSession
    :param url: str
    :param filename: str
    :return: None
    """
    images_directory: str = "images"
    logger.info("Fetching %s", url)
    async with session.get(url) as response:
        if response.status == 200:
            image_bytes = await response.read()
            logger.info("Saved %s", filename)
            await save_image(image_bytes, join(images_directory, filename))
        else:
            logger.error("Failed to download image: %s", response.status)


async def main() -> None:
    """Entry point."""
    async with aiohttp.ClientSession() as session:
        links: list[str] = await get_turtle_links(session)

        tasks: list[Coroutine] = [parse_turtles(session, link) for link in links]
        results = await asyncio.gather(*tasks)

    save_to_json(results, "turtles.json")
    save_to_csv(results, "turtles.csv")


if __name__ == '__main__':
    asyncio.run(main())
