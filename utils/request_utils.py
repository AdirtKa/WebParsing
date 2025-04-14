"""
Some useful functions.

Functions:
    fetch_with_retry(input param: param type): return data type - Aiohttp ClientResponse or None.
    fetch_with_retry_sync(url: str, retries: int, delay: int): return data type - requests.Response or None.
"""
import asyncio
import time

import requests
import aiohttp
from aiohttp import ClientSession, ClientResponse

from logger import get_logger

logger = get_logger(__name__)


async def fetch_with_retry(session: ClientSession, url: str, retries: int = 3, delay: int = 5) -> ClientResponse:
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
            response = await session.get(url, timeout=aiohttp.ClientTimeout(total=30))
            response.raise_for_status()  # Check for HTTP errors (e.g. 404, 500)
            return response  # Return the response text if successful

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            attempt += 1
            logger.error("Attempt %s/%s failed for %s: %s", attempt, retries, url, e)
            if attempt < retries:
                logger.info("Retrying in %s seconds...", delay)
                await asyncio.sleep(delay)  # Wait before retrying
            else:
                logger.error("Max retries reached for %s. Giving up.", url)
                return None  # Return None if all retries fail
            

def fetch_with_retry_sync(url: str, retries: int = 3, delay: int = 5) -> Response | None:
    """
    Perform an HTTP GET request with retries in case of failure (synchronous version).

    :param url: URL to fetch
    :param retries: number of retry attempts
    :param delay: delay between retries in seconds
    :return: Response object if successful, None if failed
    """
    attempt: int = 0
    while attempt < retries:
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()  # Check for HTTP errors (e.g., 404, 500)
            return response  # Return the response if successful

        except (requests.RequestException, requests.Timeout) as e:
            attempt += 1
            logger.error("Attempt %s/%s failed for %s: %s", attempt, retries, url, e)
            if attempt < retries:
                logger.info("Retrying in %s seconds...", delay)
                time.sleep(delay)  # Wait before retrying
            else:
                logger.error("Max retries reached for %s. Giving up.", url)
                return None  # Return None if all retries fail
