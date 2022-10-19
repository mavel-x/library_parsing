import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = Path(__file__).parent
IMAGE_DIR = Path('images')

BOOK_INFO_FILE = BASE_DIR / 'saved_books.json'


def main():
    env = Environment(
        loader=FileSystemLoader(BASE_DIR),
        autoescape=select_autoescape(['html', 'xml'])
    )

    template = env.get_template('template.html')

    with open(BOOK_INFO_FILE, 'r') as f:
        books = json.load(f)

    for book in books:
        full_path = Path(book['img_src'])
        book['img_src'] = IMAGE_DIR / full_path.name

    rendered_page = template.render(
        books=books,
    )

    with open('index.html', 'w', encoding="utf8") as file:
        file.write(rendered_page)

    server = HTTPServer(('0.0.0.0', 8000), SimpleHTTPRequestHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
