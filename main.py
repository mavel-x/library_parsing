

import requests


def fetch_book_by_id(book_id: int):
    url = f'https://tululu.org/txt.php?id={book_id}'
    filename = f'id{book_id}.txt'
    response = requests.get(url)
    response.raise_for_status()

    with open(filename, 'wb') as file:
        file.write(response.content)


def main():
    pass


if __name__ == "__main__":
    main()
