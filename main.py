from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def check_for_redirect(response: requests.models.Response):
    if response.status_code == 302:
        raise requests.exceptions.HTTPError('The requested book ID does not exist.')


def fetch_book_metadata(book_id: int):
    url = f'https://tululu.org/b{book_id}/'
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()
    check_for_redirect(response)
    soup = BeautifulSoup(response.text, 'lxml')

    title_tag = soup.find('h1')
    title = title_tag.text.split('::')[0].strip()

    image_url_relative = soup.find('div', class_='bookimage').find('img')['src']
    image_url_absolute = urljoin('https://tululu.org/', image_url_relative)

    comment_tags = soup.find_all('div', class_='texts')
    comments = [comment_tag.find('span').text for comment_tag in comment_tags]

    return {
        'title': title,
        'image_url': image_url_absolute,
        'comments': comments,
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
    filepath = book_dir.joinpath(sanitized_filename).with_suffix('.txt')
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
    for book_id in range(5, 6):
        url = f'https://tululu.org/txt.php?id={book_id}'

        try:
            book_metadata = fetch_book_metadata(book_id)
        except requests.exceptions.HTTPError:
            continue
        print(book_metadata)

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
