import argparse
import json
import logging
import re
from pathlib import Path
from pprint import pprint

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

from parse_tululu import download_book_by_id

logger = logging.getLogger(__file__)


def main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    argparser = argparse.ArgumentParser(description='Скачать книги одной категории с tululu.org.')
    argparser.add_argument('start_page', type=int, nargs='?',
                           default=1, help='С какой страницы начать')
    argparser.add_argument('end_page', type=int, nargs='?',
                           default=10, help='До какой страницы скачивать')
    args = argparser.parse_args()

    start_page = args.start_page
    end_page = args.end_page + 1

    pages = range(start_page, end_page)

    session = requests.Session()
    retries = Retry(total=4, backoff_factor=5, status_forcelist=[502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    book_list_path = Path('book_list.json')
    book_list_path.touch()

    for page in pages:
        downloaded_books = []

        url = f'https://tululu.org/l55/{page}'
        response = session.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')
        tables = soup.find_all('table', class_='d_book')
        for table in tables:
            book_path = table.find('a', title=lambda title: 'читать' in title)['href']
            book_id = re.search(r'\d+', book_path)[0]
            book = download_book_by_id(session, book_id)
            if book:
                downloaded_books.append(book)
                pprint(book, sort_dicts=False)

        with open(book_list_path) as f:
            existing_books = json.load(f)
        existing_books.extend(downloaded_books)
        book_list_path.write_text(
            json.dumps(existing_books, ensure_ascii=False)
        )


if __name__ == "__main__":
    main()
