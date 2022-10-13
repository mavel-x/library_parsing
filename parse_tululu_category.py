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

    session = requests.Session()
    retries = Retry(total=4, backoff_factor=5, status_forcelist=[502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    book_list_path = Path('book_list.json')
    # overwrite file each time the script is run
    book_list_path.write_text('[]')

    for page in range(1, 5):
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
