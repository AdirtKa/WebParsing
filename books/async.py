"""Parse data from toy bookstore but async"""
import os.path
from typing import Coroutine, Optional

import aiofiles
import asyncio
from bs4 import BeautifulSoup
from aiohttp import ClientSession, ClientResponse
from fake_useragent import UserAgent

from sync import parse_book, write_to_json, write_to_csv

BASE_URL = "https://books.toscrape.com/"
PAGINATION_URL = BASE_URL + "catalogue/page-{page}.html"
headers = {"User-Agent": UserAgent().random}


async def get_pagination_page(page: int, session: ClientSession) -> Optional[str]:
    """
    Get 1 page from toscrape.com

    :param session:
    :param page: page number
    :return: page html
    """

    url: str = PAGINATION_URL.format(page=page)

    try:
        async with session.get(url, timeout=10) as response:
            text: str = await response.text()
        return text

    except TimeoutError as e:
        print(f"Error fetching url {url}: {e}")
        return None


async def write_html_to_file(text: str, name: str) -> None:
    """
    Write html to file

    :param text: html
    :param name: file name
    :return: None
    """

    async with aiofiles.open(name, "w", encoding="utf-8") as file:
        await file.write(text)


async def read_html_from_file(filename: str) -> str:
    """
    Read html from file

    :param filename: file name
    :return: html
    """
    try:
        async with aiofiles.open(filename, "r", encoding="utf-8") as file:
            text: str = await file.read()
        return text
    except FileNotFoundError as e:
        print(f"Error fetching file {filename}: {e}")

async def process_page(page: int, session: ClientSession) -> list[str]:
    """Main task to parse a site."""
    filename: str = os.path.join("source", "pagination_pages", f"page{page}.html")
    if not os.path.isfile(filename):
        page_content: Optional[str] = await get_pagination_page(page, session)
        if page_content:
            await write_html_to_file(page_content, filename)

    page_content = await read_html_from_file(filename)
    soup: BeautifulSoup = BeautifulSoup(page_content, "lxml")

    images: list[BeautifulSoup] = soup.find_all("div", class_="image_container")
    os.makedirs(os.path.join("source", "books", f"page{page}"), exist_ok=True)

    tasks: list[Coroutine] = []
    book_filenames: list[str] = []

    for image in images:
        book_name: str = image.find("a").get("href").rstrip("/index.html")
        book_filename: str = os.path.join("source", "books", f"page{page}", book_name + ".html")
        book_filenames.append(book_filename)

        if not os.path.isfile(book_filename):
            book_link: str = BASE_URL + "catalogue/" + book_name
            tasks.append(fetch_and_save_book(book_link, book_filename, session))

    if tasks:
        await asyncio.gather(*tasks)

    return book_filenames


async def fetch_and_save_book(book_link: str, book_filename: str, session: ClientSession) -> None:
    """
    Fetch book from toscrape.com

    :param book_link: book link
    :param book_filename: book filename
    :param session: ClientSession
    :return:
    """
    try:
        print(book_link)
        response = await session.get(book_link, timeout=10)
        text = await response.text()
        await write_html_to_file(text, book_filename)
    except TimeoutError as e:
        print(f"Error fetching url {book_link}: {e}")


async def main():
    """Entry point."""
    books_data: list[dict[str, str]] = []

    #TODO make dynamic pagination
    async with ClientSession(headers=headers) as session:
        # Скачивание страниц и книг
        book_filenames_per_page = await asyncio.gather(
            *(process_page(i, session) for i in range(1, 51))
        )

    # Обработка загруженных книг
    for book_filenames in book_filenames_per_page:
        for book_filename in book_filenames:
            try:
                book_page: str = await read_html_from_file(book_filename)
                soup: BeautifulSoup = BeautifulSoup(book_page, "lxml")
                book_data: dict[str, str] = parse_book(soup)
                books_data.append(book_data)
            except Exception as e:
                print(f"Error processing book file {book_filename}: {e}")

    # Сохранение данных
    write_to_csv(books_data, "async_books.csv")
    write_to_json(books_data, "async_books.json")



if __name__ == '__main__':
    asyncio.run(main())