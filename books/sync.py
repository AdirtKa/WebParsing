"""Parse data from toy bookstore"""
import os.path
import json
import csv

from bs4 import BeautifulSoup
from requests import Response, get
from fake_useragent import UserAgent


BASE_URL = "https://books.toscrape.com/"
PAGINATION_URL = BASE_URL + "catalogue/page-{page}.html"
USER_AGENT = UserAgent()


def get_pagination_page(page: int) -> str:
    """
    Get html page from url

    :param page: page number
    :return: html page
    """
    url: str = PAGINATION_URL.format(page=page)

    response: Response = get(url, timeout=10)

    return response.text


def write_html_to_file(text: str, name: str) -> None:
    """
    Write html to file

    :param text: html text
    :param name: filename with extension
    :return: None
    """
    with open(name, "w", encoding="utf-8") as f:
        f.write(text)


def read_html_from_file(filename: str) -> str:
    """
    Read html from file

    :param filename: filename with extension
    :return: html text
    """

    with open(filename, "r", encoding="utf-8") as f:
        return f.read()


def parse_book(soup: BeautifulSoup) -> dict:
    """
    Parse book from html

    :param soup: html soup
    :return: json with book info
    """

    main_info = soup.find("div", class_="col-sm-6 product_main")

    breadcrumb: soup = soup.find("ul", class_="breadcrumb")

    return {
        "name": main_info.find("h1").text.strip(),
        "genre": breadcrumb.find("li", class_="active").find_previous_sibling().find("a").text.strip(),
        "price": main_info.find("p", class_="price_color").text.strip(),
        "availability": main_info.find("p", class_="instock availability").text.strip(),
    }


def write_to_json(data: list[dict] | dict, filename: str = "books.json") -> None:
    """
    Write json to file

    :param filename:
    :param data: data to write to file
    :return:  None
    """

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def write_to_csv(data: list[dict] | dict, filename: str = "books.csv") -> None:
    """
    Write csv to file

    :param filename:
    :param data: data to write to file
    :return: None
    """

    with open(filename, "w", encoding="utf-8", newline="") as f:
        dict_writer = csv.DictWriter(f, data[0].keys(), delimiter=";")
        dict_writer.writeheader()
        dict_writer.writerows(data)


def main():
    """Entry point."""

    books_data: list[dict[str, str]] = []

    # TODO make dynamic pagination
    for i in range(1, 51):
        filename: str = os.path.join("source", "pagination_pages", f"page{i}.html")
        if not os.path.isfile(filename):
            page: str = get_pagination_page(i)
            write_html_to_file(page, filename)

        page = read_html_from_file(filename)
        soup: BeautifulSoup = BeautifulSoup(page, "lxml")

        images: list[BeautifulSoup] = soup.find_all("div", class_="image_container")
        os.makedirs(os.path.join("source", "books", f"page{i}"), exist_ok=True)
        for image in images:
            book_name: str = image.find("a").get("href").rstrip("/index.html")
            filename: str = os.path.join("source", "books", f"page{i}", book_name + ".html")

            if not os.path.isfile(filename):
                book_link: str = BASE_URL + "catalogue/" + book_name
                print(book_link)
                response: Response = get(book_link, timeout=10)
                write_html_to_file(response.text, filename)

            page: str = read_html_from_file(filename)
            soup: BeautifulSoup = BeautifulSoup(page, "lxml")
            book_data: dict[str, str] = parse_book(soup)

            books_data.append(book_data)

    write_to_json(books_data)
    write_to_csv(books_data)


if __name__ == '__main__':
    main()
