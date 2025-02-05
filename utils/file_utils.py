"""
Utils for file manipulation.

This module provides utility functions for saving parsed data to JSON and CSV files.

Functions:
- save_to_json(data: list[dict], filename: str) -> None: Saves a list of dictionaries to a JSON file.
- save_to_csv(data: list[dict], filename: str) -> None: Saves a list of dictionaries to a CSV file.
- save_image(image_bytes: bytes, filename: str) -> None: synchronously saves binary image data to a JPG file.
"""

import json
import csv

import aiofiles

from logger import get_logger


logger = get_logger(__name__)


def save_to_json(data: list[dict], filename: str) -> None:
    """
    Save parsed data to a JSON file.

    :param data: List of dictionaries containing parsed data.
    :param filename: Name of the output JSON file.
    """
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        logger.info("Data successfully saved to %s", filename)
    except Exception as e:
        logger.error("Error writing to JSON file %s: %s", filename, e)


def save_to_csv(data: list[dict], filename: str) -> None:
    """
    Save parsed data to a CSV file.

    :param data: List of dictionaries containing parsed data.
    :param filename: Name of the output CSV file.
    """
    if not data:
        logger.warning("No data to save to CSV")
        return

    try:
        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        logger.info("Data successfully saved to %s", filename)
    except Exception as e:
        logger.error("Error writing to CSV file %s: %s", filename, e)


async def save_image(image_bytes: bytes, filename: str) -> None:
    """
    Asynchronously save image bytes to a JPG file.

    :param image_bytes: Binary image data.
    :param filename: Output file name (should include .jpg extension).
    """
    try:
        async with aiofiles.open(filename, "wb") as file:
            await file.write(image_bytes)
        print(f"Image successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving image {filename}: {e}")
