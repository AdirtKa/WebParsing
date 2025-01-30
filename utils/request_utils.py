"""
Some useful functions.

Functions:
    fetch_with_retry(input param: param type): return data type - description.
"""
from typing import Optional
import asyncio

import aiohttp
from aiohttp import ClientSession

from logger import get_logger

logger = get_logger(__name__)


async def fetch_with_retry(session: ClientSession, url: str, retries: int = 3, delay: int = 5) -> Optional[str]:
    """
    Perform an HTTP GET request with retries in case of failure.

    :param session: aiohttp session
    :param url: URL to fetch
    :param retries: number of retry attempts
    :param delay: delay between retries in seconds
    :return: response text if successful, None if failed
    """
    attempt: int = 0
    while attempt < retries:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                response.raise_for_status()  # Check for HTTP errors (e.g. 404, 500)
                return await response.text()  # Return the response text if successful
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            attempt += 1
            logger.error("Attempt %s/%s failed for %s: %s", attempt, retries, url, e)
            if attempt < retries:
                logger.info("Retrying in %s seconds...", delay)
                await asyncio.sleep(delay)  # Wait before retrying
            else:
                logger.error("Max retries reached for %s. Giving up.", url)
                return None  # Return None if all retries fail
