import argparse
import logging
from pathlib import Path
from pprint import pprint
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from requests.adapters import HTTPAdapter, Retry

logging.basicConfig(level=logging.INFO, format='%(message)s')

session = requests.Session()
retries = Retry(total=4, backoff_factor=5, status_forcelist=[502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))


def check_for_redirect(response: requests.models.Response):
    if response.is_redirect:
        raise requests.exceptions.HTTPError('No {requested_page} exists for book ID {book_id}.')


def parse_book_page(page_html: str, book_page_url: str):
    soup = BeautifulSoup(page_html, 'lxml')

    title_tag = soup.find('h1')
    title = title_tag.text.split('::')[0].strip()
    author = title_tag.find('a').text

    image_url_relative = soup.find('div', class_='bookimage').find('img')['src']
    image_url = urljoin(book_page_url, image_url_relative)

    comment_tags = soup.find_all('div', class_='texts')
    comments = [comment_tag.find('span').text for comment_tag in comment_tags] if comment_tags else None

    genre_tags = soup.find('span', class_='d_book').find_all('a')
    genres = [genre_tag.text for genre_tag in genre_tags]

    return {
        'title': title,
        'author': author,
        'image_url': image_url,
        'comments': comments,
        'genres': genres,
    }


def save_book_to_disk(book: bytes, filename: str, folder='books/'):
    sanitized_filename = sanitize_filename(filename)
    book_dir = Path(folder)
    book_dir.mkdir(exist_ok=True)
    filepath = book_dir.joinpath(f'{sanitized_filename}.txt')
    filepath.write_bytes(book)
    return filepath


def save_image_to_disk(image: bytes, filename, folder='images/'):
    image_dir = Path(folder)
    image_dir.mkdir(exist_ok=True)
    filepath = image_dir.joinpath(filename)
    filepath.write_bytes(image)
    return filepath


def download_txt(url, filename, folder='books/'):
    response = session.get(url, allow_redirects=False)
    response.raise_for_status()
    check_for_redirect(response)
    book = response.content
    return save_book_to_disk(book, filename, folder)


def download_image(url, filename, folder='images/'):
    response = session.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    image = response.content
    return save_image_to_disk(image, filename, folder)


def save_comments_to_file(comments: list, book_id: int):
    comment_dir = Path('comments')
    comment_dir.mkdir(exist_ok=True)
    filepath = comment_dir.joinpath(f'{book_id}_comments').with_suffix('.txt')
    with open(filepath, 'w') as file:
        for comment in comments:
            file.write(comment)
            file.write('\n')
    return filepath


def format_metadata(metadata: dict):
    return {
        'title': metadata['title'],
        'author': metadata['author'],
        'genres': metadata['genres'],
        'comments': metadata['comments'],
    }


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('start_id', type=int, nargs='?',
                           default=2, help='С какой книги начать')
    argparser.add_argument('end_id', type=int, nargs='?',
                           default=10, help='До какой книги скачивать')
    args = argparser.parse_args()

    start_id = args.start_id
    end_id = args.end_id + 1
    for book_id in range(start_id, end_id):
        book_page_url = f'https://tululu.org/b{book_id}/'
        try:
            response = session.get(book_page_url, allow_redirects=False)
            response.raise_for_status()
            check_for_redirect(response)
        except requests.exceptions.HTTPError as error:
            logging.info(str(error).format(requested_page='metadata', book_id=book_id))
            continue

        book_page = response.text
        book_metadata = parse_book_page(book_page, book_page_url)

        title = book_metadata['title']
        image_url = book_metadata['image_url']
        txt_filename = f'{book_id}. {title}'
        image_filename = image_url.split('/')[-1]

        txt_url = f'https://tululu.org/txt.php?id={book_id}'
        try:
            download_txt(txt_url, txt_filename)
        except requests.exceptions.HTTPError as error:
            logging.info(str(error).format(requested_page='text file', book_id=book_id))
            continue

        try:
            download_image(image_url, image_filename)
        except requests.exceptions.HTTPError as error:
            logging.info(str(error).format(requested_page='image', book_id=book_id))

        if book_metadata['comments']:
            save_comments_to_file(book_metadata['comments'], book_id)

        print(f'Saved book #{book_id}:')
        pprint(format_metadata(book_metadata), sort_dicts=False)


if __name__ == "__main__":
    main()
