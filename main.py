from pathlib import Path

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def check_for_redirect(response: requests.models.Response):
    if response.status_code == 302:
        raise requests.exceptions.HTTPError('The requested book ID does not exist.')


def fetch_book_title(book_id: int):
    url = f'https://tululu.org/b{book_id}/'
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    title_tag = soup.find('h1')
    title = title_tag.text.split('::')[0].strip()
    return title


def download_txt(url, filename, folder='books/'):
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()
    check_for_redirect(response)
    book = response.content
    sanitized_filename = sanitize_filename(filename)
    book_dir = Path(folder)
    book_dir.mkdir(exist_ok=True)
    filepath = book_dir.joinpath(sanitized_filename)
    with open(filepath, 'wb') as file:
        file.write(book)
    return filepath


def main():
    for book_id in range(1, 11):
        url = f'https://tululu.org/txt.php?id={book_id}'
        book_title = fetch_book_title(book_id)
        filename = f'{book_id}. {book_title}'
        try:
            download_txt(url, filename)
        except requests.exceptions.HTTPError:
            continue


if __name__ == "__main__":
    main()
