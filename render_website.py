import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import chunked

BASE_DIR = Path(__file__).parent
WEB_DIR = BASE_DIR / Path('web')
IMAGE_DIR = Path('static/images')
BOOK_DIR = Path('static/books')

BOOK_INFO_FILE = BASE_DIR / 'saved_books.json'


def render():
    env = Environment(
        loader=FileSystemLoader(BASE_DIR),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template(f'web/template.html')

    with open(BOOK_INFO_FILE, 'r') as file:
        books = json.load(file)

    # convert paths from absolute into relative for web serving
    for book in books:
        full_image_path = Path(book['img_src'])
        book['img_src'] = Path('..') / IMAGE_DIR / full_image_path.name
        full_txt_path = Path(book['book_path'])
        book['book_path'] = Path('..') / BOOK_DIR / full_txt_path.name

    page_dir = WEB_DIR / 'pages'
    page_dir.mkdir(exist_ok=True)

    pages = list(chunked(books, 20))

    total_pages = len(pages)

    for page_number, page_books in enumerate(pages, 1):
        rendered_page = template.render(
            books=page_books,
            total_pages=total_pages,
            current_page=page_number,
        )
        with open(page_dir / f'index{page_number}.html', 'w', encoding="utf8") as file:
            file.write(rendered_page)


def main():
    render()

    server = Server()
    server.watch('web/template.html', render)
    server.serve(root=WEB_DIR)


if __name__ == "__main__":
    main()
