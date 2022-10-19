import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server

BASE_DIR = Path(__file__).parent
WEB_DIR = Path('web')
IMAGE_DIR = Path('images')

BOOK_INFO_FILE = BASE_DIR / 'saved_books.json'


def render():
    env = Environment(
        loader=FileSystemLoader(BASE_DIR),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template(f'web/template.html')

    with open(BOOK_INFO_FILE, 'r') as f:
        books = json.load(f)

    for book in books:
        full_path = Path(book['img_src'])
        book['img_src'] = IMAGE_DIR / full_path.name

    rendered_page = template.render(
        books=books,
    )
    with open('web/index.html', 'w', encoding="utf8") as file:
        file.write(rendered_page)


def main():
    server = Server()
    server.watch('web/template.html', render)
    server.serve(root=WEB_DIR)


if __name__ == "__main__":
    main()
