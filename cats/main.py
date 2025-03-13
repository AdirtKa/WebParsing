"""Parsing cats gifs, jpgs and pngs from an open api"""
import os
from typing import Coroutine
import asyncio

import aiohttp

from utils.file_utils import save_image
from logger import get_logger

logger = get_logger(__name__)

# Создаем папку для сохранения изображений
IMAGES_PATH = "cat_images"
os.makedirs(IMAGES_PATH, exist_ok=True)

# Параметры API
API_URL = "https://api.thecatapi.com/v1/images/search"
API_KEY = "live_mNSFKBE7H5dOar7ou73pCXrriZ7EyfuFRlnhGwVI829aShUM7aJA11l6lc46xUE9"

headers = {
    "x-api-key": API_KEY
}

TOTAL_IMAGES = 1000
BATCH_SIZE = 100


async def fetch_batch(session: aiohttp.ClientSession, page: int):
    """
    get batch of images from an api.

    :param page: current page
    :param session: aiohttp.ClientSession
    """
    params = {
        "limit": BATCH_SIZE,
        "order": "ASC",
        "page": page
    }

    async with session.get(API_URL, headers=headers, params=params) as response:
        logger.info("fetching images from api.")
        if response.status == 200:
            tasks = []
            for image in await response.json():
                image_name = image["url"].rsplit("/")[-1]
                tasks.append(asyncio.create_task(fetch_and_save_image(session, image["url"], image_name)))

            await asyncio.gather(*tasks)

        else:
            logger.error("Failed to get images image: %s", response.status)


async def fetch_and_save_image(session: aiohttp.ClientSession, url: str, filename: str):
    """
    Save image from url to filename.

    :param session: aiohttp.ClientSession
    :param url: str
    :param filename: str
    :return: None
    """
    images_directory: str = IMAGES_PATH
    logger.info("Fetching %s", url)
    async with session.get(url) as response:
        if response.status == 200:
            image_bytes = await response.read()
            logger.info("Saved %s", filename)
            await save_image(image_bytes, os.path.join(images_directory, filename))
        else:
            logger.error("Failed to download image: %s", response.status)


async def main():
    """Entry Point."""
    async with aiohttp.ClientSession() as session:
        tasks: list[Coroutine] = [fetch_batch(session, page) for page in range(0, TOTAL_IMAGES // BATCH_SIZE + 1)]

        await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())
