import argparse
from pathlib import Path
from pprint import pprint
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def check_for_redirect(response: requests.models.Response):
    if response.status_code == 302:
        raise requests.exceptions.HTTPError('The requested book ID does not exist.')


def fetch_book_page(book_id: int):
    url = f'https://tululu.org/b{book_id}/'
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()
    check_for_redirect(response)
    return response.text


def parse_book_page(page_html: str):
    def find_title(soup: BeautifulSoup):
        title_tag = soup.find('h1')
        return title_tag.text.split('::')[0].strip()

    def find_image_url(soup: BeautifulSoup):
        image_url_relative = soup.find('div', class_='bookimage').find('img')['src']
        return urljoin('https://tululu.org/', image_url_relative)

    def find_comments(soup: BeautifulSoup):
        comment_tags = soup.find_all('div', class_='texts')
        return [comment_tag.find('span').text for comment_tag in comment_tags]

    def find_genres(soup: BeautifulSoup):
        genre_tags = soup.find('span', class_='d_book').find_all('a')
        return [genre_tag.text for genre_tag in genre_tags]

    book_soup = BeautifulSoup(page_html, 'lxml')

    return {
        'title': find_title(book_soup),
        'image_url': find_image_url(book_soup),
        'comments': find_comments(book_soup),
        'genres': find_genres(book_soup)
    }


def fetch_book_by_url(url: str):
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()
    check_for_redirect(response)
    return response.content


def save_book_to_disk(book: bytes, filename: str, folder='books/'):
    sanitized_filename = sanitize_filename(filename)
    book_dir = Path(folder)
    book_dir.mkdir(exist_ok=True)
    filepath = book_dir.joinpath(f'{sanitized_filename}.txt')
    filepath.write_bytes(book)
    return filepath


def fetch_image_by_url(url: str):
    response = requests.get(url)
    response.raise_for_status()
    return response.content


def save_image_to_disk(image: bytes, filename, folder='images/'):
    image_dir = Path(folder)
    image_dir.mkdir(exist_ok=True)
    filepath = image_dir.joinpath(filename)
    filepath.write_bytes(image)
    return filepath


def download_txt(url, filename, folder='books/'):
    book = fetch_book_by_url(url)
    return save_book_to_disk(book, filename, folder)


def download_image(url, filename, folder='images/'):
    image = fetch_image_by_url(url)
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


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('start_id', type=int, nargs='?',
                           default=1, help='С какой книги начать')
    argparser.add_argument('end_id', type=int, nargs='?',
                           default=10, help='До какой книги скачивать')
    args = argparser.parse_args()

    start_id = args.start_id
    end_id = args.end_id + 1
    for book_id in range(start_id, end_id):
        url = f'https://tululu.org/txt.php?id={book_id}'

        try:
            book_page = fetch_book_page(book_id)
        except requests.exceptions.HTTPError:
            continue
        book_metadata = parse_book_page(book_page)
        pprint(book_metadata, sort_dicts=False)

        title = book_metadata['title']
        image_url = book_metadata['image_url']
        txt_filename = f'{book_id}. {title}'
        image_filename = image_url.split('/')[-1]

        try:
            download_txt(url, txt_filename)
        except requests.exceptions.HTTPError:
            continue

        download_image(image_url, image_filename)

        if book_metadata['comments']:
            save_comments_to_file(book_metadata['comments'], book_id)


if __name__ == "__main__":
    main()
