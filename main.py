from pathlib import Path

import requests
from bs4 import BeautifulSoup


def fetch_book_by_id(book_id: int):
    url = f'https://tululu.org/txt.php?id={book_id}'
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()
    check_for_redirect(response)
    return response.content


def check_for_redirect(response: requests.models.Response):
    if response.status_code == 302:
        raise requests.exceptions.HTTPError('The requested book ID does not exist.')


def save_book_to_disk(book_id: int, book_content: bytes):
    filename = f'id{book_id}.txt'
    book_dir = Path('books')
    book_dir.mkdir(exist_ok=True)
    with open(book_dir.joinpath(filename), 'wb') as file:
        file.write(book_content)


def parse_blog():
    url = 'https://www.franksonnenbergonline.com/blog/are-you-grateful/'
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    title_tag = soup.find('main').find('header').find('h1')
    img_url = soup.find('img', class_='attachment-post-image')['src']
    text_div = soup.find('div', class_='entry-content')
    post_paragraphs = [paragraph.text for paragraph in text_div]
    post_text = ''.join(post_paragraphs)

    post = {
        'title': title_tag.text,
        'img': img_url,
        'text': post_text,
    }

    print(post)

def main():
    for book_id in range(1, 11):
        try:
            book = fetch_book_by_id(book_id)
        except requests.exceptions.HTTPError:
            continue
        save_book_to_disk(book_id, book)


if __name__ == "__main__":
    parse_blog()
