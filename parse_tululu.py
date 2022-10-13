import argparse
import logging
from pathlib import Path
from pprint import pprint
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from requests.adapters import HTTPAdapter, Retry

logger = logging.getLogger(__file__)

BOOK_DIR = 'books/'
IMG_DIR = 'images/'


def check_for_redirect(response: requests.models.Response):
    if response.is_redirect:
        raise requests.exceptions.HTTPError('No {requested_page} exists for book ID {book_id}.')


def parse_book_page(page_html: str, book_page_url: str):
    soup = BeautifulSoup(page_html, 'lxml')

    title_tag = soup.select_one('h1')
    title, author = (string.replace(u' \xa0 :: \xa0 ', '') for string in title_tag.strings)

    image_url_relative = soup.select_one('.bookimage img')['src']
    image_url = urljoin(book_page_url, image_url_relative)

    comment_tags = soup.select('.texts span')
    comments = [comment_tag.text for comment_tag in comment_tags] or None

    genre_tags = soup.select('span.d_book a')
    genres = [genre_tag.text for genre_tag in genre_tags] or None

    return {
        'title': title,
        'author': author,
        'image_url': image_url,
        'comments': comments,
        'genres': genres,
    }


def save_txt_to_disk(book_txt: bytes, filename: str, directory=BOOK_DIR):
    sanitized_filename = sanitize_filename(filename)
    book_dir = Path(directory)
    book_dir.mkdir(exist_ok=True)
    filepath = book_dir.joinpath(f'{sanitized_filename}.txt')
    if filepath.exists():
        raise FileExistsError
    filepath.write_bytes(book_txt)
    return filepath


def save_image_to_disk(image: bytes, filename, directory=IMG_DIR):
    image_dir = Path(directory)
    image_dir.mkdir(exist_ok=True)
    filepath = image_dir.joinpath(filename)
    filepath.write_bytes(image)
    return filepath


def download_txt(book_id, filename, session, directory=BOOK_DIR):
    txt_url = f'https://tululu.org/txt.php'
    response = session.get(txt_url, params={'id': book_id}, allow_redirects=False)
    response.raise_for_status()
    check_for_redirect(response)
    book_txt = response.content
    return save_txt_to_disk(book_txt, filename, directory)


def download_image(url, filename, session, directory=IMG_DIR):
    response = session.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    image = response.content
    return save_image_to_disk(image, filename, directory)


def format_book_metadata(book: dict):
    return {
        'title': book['title'],
        'author': book['author'],
        'genres': book['genres'],
        'comments': book['comments'],
    }


def download_book_by_id(session: requests.Session, book_id):
    book_page_url = f'https://tululu.org/b{book_id}/'
    try:
        response = session.get(book_page_url, allow_redirects=False)
        response.raise_for_status()
        check_for_redirect(response)
    except requests.exceptions.HTTPError as error:
        logger.info(str(error).format(requested_page='book page', book_id=book_id))
        return

    book_page = response.text
    book = parse_book_page(book_page, book_page_url)

    title = book['title']
    image_url = book['image_url']
    txt_filename = f'{book_id}. {title}'
    image_filename = image_url.split('/')[-1]

    try:
        book_path = download_txt(book_id, txt_filename, session)
    except requests.exceptions.HTTPError as error:
        logger.info(str(error).format(requested_page='text file', book_id=book_id))
        return
    except FileExistsError:
        logger.info(f'Book #{book_id} is already on disk.')
        return

    try:
        image_path = download_image(image_url, image_filename, session)
    except requests.exceptions.HTTPError as error:
        image_path = None
        logger.info(str(error).format(requested_page='image', book_id=book_id))

    book_metadata = format_book_metadata(book)
    book_metadata.update({
        'img_src': str(image_path),
        'book_path': str(book_path),
    })

    return book_metadata


def main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    session = requests.Session()
    retries = Retry(total=4, backoff_factor=5, status_forcelist=[502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    argparser = argparse.ArgumentParser(description='Скачать книги с tululu.org по их ID.')
    argparser.add_argument('start_id', type=int, nargs='?',
                           default=1, help='С какой книги начать')
    argparser.add_argument('end_id', type=int, nargs='?',
                           default=10, help='До какой книги скачивать')
    args = argparser.parse_args()

    start_id = args.start_id
    end_id = args.end_id + 1

    book_ids = range(start_id, end_id)

    for book_id in book_ids:
        book = download_book_by_id(session, book_id)
        if book:
            pprint(book, sort_dicts=False)


if __name__ == "__main__":
    main()
