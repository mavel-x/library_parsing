from pathlib import Path

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def fetch_book_by_id(book_id: int):
    url = f'https://tululu.org/txt.php?id={book_id}'
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()
    check_for_redirect(response)
    return response.content


def check_for_redirect(response: requests.models.Response):
    if response.status_code == 302:
        raise requests.exceptions.HTTPError('The requested book ID does not exist.')


def fetch_book_metadata(book_id: int):
    url = f'https://tululu.org/b{book_id}/'
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    title_tag = soup.find('h1')
    title = title_tag.text.split('::')[0].strip()
    author = title_tag.find('a').text
    return {
        'title': title,
        'author': author,
    }


def fetch_book_title(book_id: int):
    url = f'https://tululu.org/b{book_id}/'
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    title_tag = soup.find('h1')
    title = title_tag.text.split('::')[0].strip()
    return title


def save_book_to_disk(book: bytes, filename):
    book_dir = Path('books')
    book_dir.mkdir(exist_ok=True)
    filepath = book_dir.joinpath(filename)
    with open(filepath, 'wb') as file:
        file.write(book)
    return filepath


def download_txt(book_id):
    book = fetch_book_by_id(book_id)
    title = fetch_book_title(book_id)
    sanitized_title = sanitize_filename(title)
    sanitized_title_with_id = f'{book_id}. {sanitized_title}'
    save_book_to_disk(book, sanitized_title_with_id)


def main():
    for book_id in range(1, 11):
        try:
            download_txt(book_id)
        except requests.exceptions.HTTPError:
            continue


if __name__ == "__main__":
    main()
