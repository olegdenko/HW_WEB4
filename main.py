from http.server import HTTPServer, BaseHTTPRequestHandler
import pathlib
import urllib.parse
import mimetypes
import json
from datetime import datetime
import socket
import logging

BASE_DIR = pathlib.Path()

# html = """
# <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>OlegDenko</title>
# </head>
# <body>
#     <h1> Hello World </h1>
# </body>
# </html>"""


class HTTPHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        body = urllib.parse.unquote(body.decode())
        body.replace('=', '')

        # Отримуємо існуючі дані з файлу
        try:
            with open(BASE_DIR.joinpath('storage/data.json'), 'r', encoding='utf-8') as fd:
                data = json.load(fd)
        except FileNotFoundError:
            data = {}

        # Розпаковуємо дані з POST-запиту
        payload_data = {key: value for key, value in [
            el.split('=') for el in body.split('&')]}

        # Додаємо запис до словника
        payload = {
            str(datetime.now()): payload_data
        }

        # Додаємо до існуючих даних
        data.update(payload)

        # Записуємо оновлені дані у файл
        with open(BASE_DIR.joinpath('storage/data.json'), 'w', encoding='utf-8') as fd:
            json.dump(data, fd, ensure_ascii=False, indent=4)

        self.send_response(302)
        self.send_header('Location', '/contact')
        self.end_headers()

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case "/":
                self.send_html('index.html')
            case "/message":
                self.send_html('message.html')
            case "/contact":
                self.send_html('contact.html')
            case _:
                file = BASE_DIR / route.path[1:]
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html('error.html', 404)

    def send_html(self, filename, status_code=200):           
        self.send_response(status_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())

    def send_static(self, filename):
        self.send_response(200)
        mime_type, *rest = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content-type', mime_type)
        else:
            self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())


def run(server=HTTPServer, hamdler=HTTPHandler):
    addres = ('', 3000)
    http_server = server(addres, hamdler)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()


if __name__ == "__main__":

    run()
