"""Parsing hockey site synchronously."""
import csv
import json
import requests
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from logger import get_logger

logger = get_logger(__name__)
BASE_URL = "https://www.scrapethissite.com/pages/forms/"


def get_pages_count(per_page=25):
    """
    Get number of pages with specified number of rows per page.

    :param per_page: number of rows per page
    :return: number of pages
    """
    url = urljoin(BASE_URL, f"?per_page={per_page}")
    logger.info("Fetching number of pages from %s", url)

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        text = response.text

        soup = BeautifulSoup(text, "lxml")
        pagination = soup.find("ul", class_="pagination")

        if not pagination or len(pagination.find_all("li")) < 2:
            logger.info("Pagination not found, assuming 1 page")
            return 1

        pages_count = int(pagination.find_all("li")[-2].text.strip())
        logger.info("Successfully fetched %s pages", pages_count)
        return pages_count

    except requests.RequestException as e:
        logger.error("Request error for %s: %s", url, e)
        return -1


def parse_page(per_page, page_num):
    """
    Parse all table data from a page.

    :param per_page: how many rows per page
    :param page_num: page index
    :return: list of parsed data
    """
    url = urljoin(BASE_URL, f"?page_num={page_num}&per_page={per_page}")
    logger.info("Parsing page %d: %s", page_num, url)

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        text = response.text

        soup = BeautifulSoup(text, "lxml")
        table = soup.find("table", class_="table")

        if not table:
            logger.warning("No table found on page %d", page_num)
            return []

        rows = table.find_all("tr")
        logger.info("Found %s rows on page %d", len(rows) - 1, page_num)

        table_headers = [column.text.strip() for column in rows[0].find_all("th")]
        rows_data = [parse_row(row, table_headers) for row in rows[1:]]

        logger.info("Successfully parsed page %d", page_num)
        return rows_data

    except requests.RequestException as e:
        logger.error("Error parsing page %d: %s", page_num, e)
        return []


def parse_row(row, table_headers):
    """
    Transform soup row into dictionary format.

    :param row: BeautifulSoup row
    :param table_headers: list of table headers
    :return: dictionary representation of row
    """
    columns = [column.text.strip() for column in row.find_all("td")]
    return dict(zip(table_headers, columns))


def main():
    """Entry point."""
    logger.info("Starting scraping process")

    per_page = 25
    pages_count = get_pages_count(per_page)

    if pages_count == -1:
        logger.error("Failed to retrieve number of pages, exiting")
        return

    all_data = []
    for i in range(1, pages_count + 1):
        all_data.extend(parse_page(per_page, i))

    logger.info("Successfully scraped %d records in total", len(all_data))

    save_to_json(all_data, "sync_hockey_data.json")
    save_to_csv(all_data, "sync_hockey_data.csv")

    logger.info("Scraping process finished")


def save_to_json(data, filename):
    """
    Save parsed data to a JSON file.
    """
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        logger.info("Data successfully saved to %s", filename)
    except Exception as e:
        logger.error("Error writing to JSON file %s: %s", filename, e)


def save_to_csv(data, filename):
    """
    Save parsed data to a CSV file.
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


if __name__ == '__main__':
    main()
