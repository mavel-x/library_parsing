import argparse
import json
import logging
import re
from pathlib import Path
from pprint import pprint

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

from parse_tululu import check_for_redirect, download_book_by_id

logger = logging.getLogger(__file__)

DEFAULT_BASE_DIR = Path(__file__).parent


def main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    argparser = argparse.ArgumentParser(description='Скачать книги одной категории с tululu.org.')
    argparser.add_argument('start_page', type=int, nargs='?',
                           default=1, help=('с какой страницы раздела начать, '
                                            'по умолчанию - 1'))
    argparser.add_argument('end_page', type=int, nargs='?',
                           default=10, help=('до какой страницы скачивать, '
                                             'по умолчанию - 10'))
    argparser.add_argument('-d', '--dest_dir', default=DEFAULT_BASE_DIR,
                           help=('путь к каталогу с результатами парсинга, '
                                 'по умолчанию - ./'))
    argparser.add_argument('-j', '--json_path', default='saved_books.json',
                           help=('путь к .json файлу для информации о скачанных книгах, '
                                 'по умолчанию - ./saved_books.json'))
    argparser.add_argument('-ni', '--skip_imgs', action='store_true', default=False,
                           help='не скачивать картинки')
    argparser.add_argument('-nb', '--skip_txt', action='store_true', default=False,
                           help='не скачивать книги')

    args = argparser.parse_args()

    start_page = args.start_page
    end_page = args.end_page + 1
    dest_dir = DEFAULT_BASE_DIR.joinpath(args.dest_dir)

    pages = range(start_page, end_page)

    session = requests.Session()
    retries = Retry(total=4, backoff_factor=5, status_forcelist=[502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    book_info_file = Path(args.json_path)
    book_info_file.parent.mkdir(exist_ok=True)
    if not book_info_file.exists():
        book_info_file.write_text('[]')

    for page in pages:
        downloaded_books = []

        url = f'https://tululu.org/l55/{page}'
        try:
            response = session.get(url, allow_redirects=False)
            response.raise_for_status()
            check_for_redirect(response)
        except requests.exceptions.HTTPError as error:
            logger.error(error)
            return

        soup = BeautifulSoup(response.text, 'lxml')
        tables = soup.find_all('table', class_='d_book')
        for table in tables:
            book_path = table.find('a', title=lambda title: 'читать' in title)['href']
            book_id = re.search(r'\d+', book_path)[0]

            try:
                book = download_book_by_id(session, book_id,
                                           dest_dir=dest_dir,
                                           skip_imgs=args.skip_imgs, skip_txt=args.skip_txt)
            except requests.exceptions.HTTPError as error:
                logger.error(error)
                continue
            except FileExistsError:
                logger.info(f'Book #{book_id} is already on disk.')
                continue
            except requests.exceptions.InvalidURL as error:
                logger.error(error)
                book = f'{book_id} was downloaded but its metadata was lost.'

            if book:
                downloaded_books.append(book)
                pprint(book, sort_dicts=False)

        # Запись файла находится в цикле, чтобы постепенно добавлять информацию о книгах после каждого цикла.
        # Это полезно на случай ошибки сети или прочего при большом объеме книг - данные до ошибки не потеряются.
        with open(book_info_file, 'rb') as f:
            existing_books = json.load(f)
        existing_books.extend(downloaded_books)

        book_info_file.write_text(
            json.dumps(existing_books, ensure_ascii=False)
        )


if __name__ == "__main__":
    main()
